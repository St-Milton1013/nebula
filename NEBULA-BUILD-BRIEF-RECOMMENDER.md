# BUILD BRIEF — nebula recommendation engine

Paste this into a fresh chat. It is self-contained; read it fully before writing code.

---

## 1. Mission

Build the recommendation engine for **nebula**, a single-user, evidence-first cEDH deck
auditor. It proposes **cuts and adds** for one deck at a time, and every proposal must carry
the evidence behind it. It is not an EDHREC clone and it is not a chat assistant.

The owner's working principle: *objective over curated*. Anything hand-maintained rots, so
prefer a computed answer with a stated population and method over a list somebody wrote.

---

## 2. Read these first

| File | Why |
|---|---|
| `NEBULA-CONTRACT-P0.md` | decisions D1–D17. These are settled; do not relitigate them. |
| `NEBULA-RESEARCH-QUEUE.md` | R1–R5, especially **R5** (recommendation engine) and **R2a** (packages) |
| `README.md` | what P0 already does |

Workspace: `C:\Users\Main\Desktop\project frontgate\Projects\nebula` (a git clone — work
there, not in a copy).
Repo: `St-Milton1013/nebula`. `main` holds docs + contract; **code lives on branch
`p0-evidence-layer`** (78 tests green). Branch off it.

Run the suite before changing anything:

```
python -m unittest discover -s tests -t .
```

---

## 3. What already exists (do not rebuild)

| Module | Does |
|---|---|
| `nebula/importer.py` | text decklist → zones; quantities preserved; printing metadata stripped |
| `nebula/decklink.py` | Moxfield + Archidekt deck import via their JSON APIs |
| `nebula/freeze.py` | canonical + `deck_sha256` + `text_sha256`, immutable snapshot |
| `nebula/cardtruth.py` | frozen Scryfall index (38,838 cards, full Oracle text, faces, legality) |
| `nebula/legality.py` | 903.5a size, commander count, partner pairing, singleton, colour identity, bans |
| `nebula/metrics.py` | lands/basics/nonlands, average+median MV, curve, type breakdown |
| `nebula/tagger.py` | Scryfall Tagger store: 4,607 tags, ancestry, per-card tags by oracle id |
| `nebula/roles.py` | role coverage from Tagger parents; lands carry ramp only; multi-role allowed |
| `nebula/config.py` | policy numbers (event floor, support floor, stability, pooling) |
| `nebula/cli.py` | `--deck` / `--link`, `--roles`, `--json` |

Data stores are **rebuilt, never committed**: `data/card_truth.json.gz` (4.3 MB),
`data/oracle_tags.json.gz` (2.0 MB). Build them with `scripts/build_card_truth.py` and
`scripts/build_tags.py`. `data/` is gitignored.

---

## 4. Hard rules (these are decisions, not preferences)

1. **Stdlib only.** No new dependencies. No `codie.*` imports — nebula inherits Codie's
   conclusions, never its code (D1).
2. **Every capability returns a status.** `AVAILABLE / PARTIAL / UNSUPPORTED / FAIL`, with a
   mandatory caveat on anything not `AVAILABLE`. A module that fails silently is a defect.
3. **No win rate, ever.** No "this deck performs better", no game-outcome claim (D3).
4. **Never quote the theory corpus** and never paste rules text. Cite a rule number + the
   Wizards CR date, paraphrased (§11 of the contract).
5. **One deck at a time.** Multi-deck compare is out of scope (D5).
6. **Network is injectable** (`fetch=` parameter). Tests never touch the internet.
7. **Policy numbers live in `nebula/config.py`**, with defaults and a test.
8. **Recommendations are opt-in** (`--recommend`). The default report stays diagnostic until
   the package model exists (D14).
9. **Reports are archived, never rewritten** (D16): no editing of prior outputs.

---

## 5. External contracts — verified 2026-11-22, use these exactly

### Commander Spellbook (combo completion — no tournament data needed)

```
POST https://backend.commanderspellbook.com/find-my-combos
{"main": [{"card": "Sol Ring"}, {"card": "Underworld Breach"}, ...]}
```

`main` is a list of objects, each `{"card": "<exact card name>"}` — **not** bare strings, and
`name` alone is rejected. 80 req/min is the documented safe rate; identify the client in the
User-Agent.

Response `results` holds six buckets:

| Bucket | Meaning |
|---|---|
| `included` | the deck has everything the variant needs |
| `almostIncluded` | missing pieces (may be more than one) |
| `almostIncludedByAddingColors` | needs colours the deck lacks |
| `includedByChangingCommanders` | would work with a different commander |
| `almostIncludedByChangingCommanders` | needs both |
| `almostIncludedByAddingColorsAndChangingCommanders` | needs both |

Each variant: `id`, `uses[]` (`card{name, oracleId}`, `quantity`, `zoneLocations`),
`requires[]` (**either** `card` **or** `template{name, scryfallQuery}`), `produces[]`
(`feature{name}`), `description`, `popularity`, `manaNeeded`, `notablePrerequisites`.

**Known gap, must be handled:** the API returns **no `present_cards` / `missing_cards`
fields and no rules citations.** Derive missing pieces by diffing `uses` against the deck,
and report `requires[].template` entries as `UNRESOLVED_TEMPLATE` with the template name
(their Scryfall query can be used to match against the deck later). Rules citations are ours
to write, separately.

Measured baseline on the frozen fixture (`tests/fixtures/ishai_rograkh.deck`, 100 cards,
Ishai + Rograkh): `included` 9, `almostIncluded` 76, `almostIncludedByAddingColors` 29,
identity `URW`. Use those as the expected shape, not exact numbers, in tests.

### Recommander (benchmark only — do not call at runtime)

`recommander.cards` is a collaborative-filtering model over 600k casual decks. Their scores
are response-relative and their population is not cEDH. **Do not build a dependency on it.**
It may appear only as an opt-in benchmark in a manual test, comparing rank correlation.

---

## 6. What to build, in order

### Stage A — works today, no tournament data

**A1. Combo completion.**
Call Spellbook with the frozen deck. For each `almostIncluded` variant, derive the missing
cards by diffing `uses` against the deck. Rank an *add* candidate by:
1. how few pieces it closes (1-card gap beats 2-card),
2. variant popularity,
3. whether the missing piece is a template (flag, don't guess).

Output per candidate: `{name, closes_variants: [...], gap_size, popularity, status}`. A card
that closes a one-piece gap in a popular variant is the strongest add signal we have without
any tournament data.

**A2. Redundancy — the primary cut signal.**

This is the single most important rule in this brief, and it is counterintuitive:

> You do **not** cut cards that fit the deck badly. You cut cards that fit it **too well**,
> because the deck already has enough of that effect. Pet cards, pet interaction and silver
> bullets are the cards you keep.

So do not rank deck cards by "would I include this". Score **marginal coverage**: for each
card, how much of its role set is already covered by the rest of the deck (use
`nebula.roles` + `nebula.metrics`). A card whose roles are all covered N times is redundant,
regardless of how strong it is in isolation. Report the covering cards by name so the claim
is inspectable.

**A3. Role gaps.** For each role, the deck's count against the population's count — but with
no tournament data, report only the deck's own internal distribution and mark the comparison
`UNSUPPORTED — no population`. Do not invent a target number.

### Stage B — needs §6 tournament ingestion (do not start without it)

- **Lift**, defined exactly as: `share of this commander's lists running the card ÷ share of
  all identity-legal lists running it`. High = commander-associated, ~0 = staple, negative =
  avoided.
- **Deck stats** derived from lift: synergy (mean lift, −100%..+100%), synergy range, staple
  and anti-staple share.
- **Outcome lift**: top-cut vs field inside a population, with a stated floor and interval.
- **Candidate ranking**, per the skeleton in R5:

```
score =  deck_conditioned_lift + package_fit + combo_completion + outcome_lift
       - staple_penalty - small_sample_penalty - redundancy
```

Weights are policy numbers, hand-set and published, not fitted.

### Stage C — proposal format

Every proposal carries: the cut, the add, the role/package affected, one evidence line per
claim with its source and version, a confidence ceiling, and **what evidence would change the
verdict**. Competing proposals stay side by side when evidence is inconclusive; never force a
single winner.

---

## 7. Acceptance criteria

1. `python -m nebula.cli --link <moxfield url> --recommend` prints proposals with evidence
   lines, statuses and caveats.
2. Tests prove, on fixtures:
   - a deck one card short of a popular combo surfaces that card;
   - a card whose roles are fully covered is flagged redundant, and the covering cards are
     named;
   - a card with unique coverage is **not** flagged redundant;
   - a template requirement yields `UNRESOLVED_TEMPLATE`, not a fabricated card.
3. No network in tests; all external calls injectable.
4. No new dependency; `python -m unittest discover -s tests -t .` stays green.
5. A deck with unresolved cards degrades to `PARTIAL` and still produces a report.

---

## 8. Out of scope

- Rebuilding Recommander, or calling it at runtime.
- The simulator (parked: 0/10 win-condition packages have action support).
- Jin's two-pass critic (ships in 1.1).
- Multi-deck compare, Discord delivery, theory prose.
- Cuts wired into the default report before packages exist (D14).

---

## 9. How to report back

State what is **run**, what is **theoretical**, and what is **blocked**. Every claim needs a
command output or a test behind it. If a dependency is missing, stop at the boundary and say
so — do not stub it, and do not mark anything done that has not been executed.
