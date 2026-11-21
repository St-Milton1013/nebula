---
id: nebula-contract-p0
project: nebula
type: contract
status: PROPOSED
created: '2026-11-21'
updated: '2026-11-21'
authority: user-locked-decisions
confidence: high
---

# NEBULA — P0 Contract (frozen before any code)

Step 235 of the audit-tool design: *"Freeze the audit contract. Define the inputs,
required outputs, evidence labels, report structure, and human-authority boundaries."*

This file is that freeze. Code that contradicts it is wrong, not the contract.

---

## 0. Locked decisions (user, 2026-11-21)

| # | Decision | Consequence |
|---|---|---|
| D1 | **Nebula is an independent iteration**, not a continuation of Codie. It inherits Codie's *conclusions*, never its code. | Nebula imports nothing from `codie.*`. No shared package, no vendored modules. |
| D2 | **Codie is the staging ground.** Parts are proven there first, then promoted into Nebula. | A component earns its place in Nebula by passing §1.2, not by existing. |
| D3 | **The simulator answers one question:** probability that this deck can *cast* a named card by turn N. Not "can we win", not "do we see it". One target per run. | No win-rate field anywhere in Nebula. See §5. |
| D4 | Nebula builds the **pipeline** (P0 → P3 in that order). | Later stages may not be built before their prerequisites. |
| D5 | Single-deck review; Jin's two-pass critic is the review layer. | Multi-deck is out of scope; `/compare` is not in the pipeline. |
| D6 | **The role taxonomy is the Scryfall Tagger hierarchy.** Community-built, community-checked; good enough. Roles are Tagger parents, and a card counts for a role when any of its tags inherits that anchor. | No hand-written keyword lists, no per-deck tuning. Lands carry no role and are counted separately. |
| D7 | **A card may hold several roles.** Roles are coverage, not buckets: a card that counters and removes counts for both. | Counts are per role, never forced to sum to the deck size, and cards in more than one role are listed so the overlap is visible. |

---

## 1. Ownership boundary

### 1.1 What Nebula may inherit from Codie

Only **artifacts that already exist as data**, copied in as frozen, fingerprinted inputs:

| Artifact | Location (verified 2026-11-21) | Status |
|---|---|---|
| Theory corpus | `mtg_laya_project/corpus/corpus_pack.json` | 32 profiles, 1,002 paragraphs, 432 body entries |
| Card truth | `mtg_laya_project/nodes/00_CardTruth/cards.json` | 33,777 cards, 0 unresolved, Scryfall bulk 2026-10-20 |
| Rules index | `nodes/00_CardTruth/rules/rules_index_academyruins.json` | 3,166 rules |
| Tournament data | `mtg_laya_project/tournaments/` + `config/topdeck_all_tournaments.json` | 10,124 / 10,124 files |
| Laya framework | `codie/project frontgate/Projects/Codie/review-laya-question-framework.md` | 70 questions, 18 part headings (PART 2 absent) |
| LearnCEDH cache | `nebula_repos/learncedh/cached_decks.json` | unverified coverage |

### 1.2 Promotion rule (Codie → Nebula)

A part moves when all four hold:

1. It runs standalone with no import from `codie.*`.
2. It has a fixture that exercises it, not just an import test.
3. Its input and output are declared (a shape, not a dict of whatever).
4. Its failure is observable — it returns a status, it does not silently pass.

Anything failing 1–4 stays in Codie. "It works in the audit" is not evidence.

### 1.3 Explicitly excluded (Codie technical debt)

`goal_engine`, `decision_intelligence`, `validation` gate machinery, `providers/` (35 modules),
`presentation_export`, `recommendation_output`, and the Phase44–51 packet/governance chain.
Nebula does not carry a validation-gate framework, a goal engine, or a provider abstraction
until a pipeline stage proves it needs one.

---

## 2. Input contract

| Field | Rule |
|---|---|
| Source | local file, Moxfield URL, Archidekt URL, or pasted text |
| Normalization | counts preserved (`2 Sol Ring` → two entries); never strip a leading number from a name |
| Zones | `commander`, `mainboard`; 100 total per rule 903.5a (1–2 commanders) |
| Freeze | on ingest, write an immutable snapshot: raw text + normalized list + SHA-256 |
| Fingerprint | `sha256(raw decklist)` stored with every downstream result |
| Failure | unresolvable card → recorded as `UNRESOLVED_CARD`, never dropped |

A result without a fingerprint is not a Nebula result.

---

## 3. Evidence labels

Every claim in the output carries exactly one:

- `VERIFIED` — read from a named source (rule number, Scryfall oracle text, TID).
- `MEASURED` — computed by Nebula from the frozen deck (counts, densities, curves).
- `SIMULATED` — a rate from a declared run (target, zone, turn, games, settings, interval).
- `INTERPRETED` — theory or Jin's judgement. Never stated as fact.
- `UNRESOLVED` — the pipeline does not know. Printed, not omitted.

Silence is not a status. A section that could not run says so and names the reason.

---

## 4. Module contract

Each module returns `{status, data, caveats}`:

| status | meaning |
|---|---|
| `AVAILABLE` | ran, produced data |
| `PARTIAL` | ran incompletely — **caveat is mandatory** |
| `UNSUPPORTED` | cannot answer this input — caveat mandatory |
| `FAIL` | errored — error text captured, pipeline continues |

The aggregator derives the report status **from the modules**. A module may not be
reported as available because it was called. (The 2026-10-26 prototype hardcodes
`"status": "available"` for all seven adapters, which erases three stubs that return
PARTIAL — that defect is the reason this rule exists.)

---

## 5. Simulation contract

**The question, and only this one:** `P(this deck can cast card X by turn N)`.

- **Casting, not seeing.** The metric is *cast*: mana was available and the sequence was
  legal. "In hand" and "seen" are not this metric and are not what a run reports.
- **One target card per run.** Multi-card questions are out of scope by decision
  (2026-11-21). Per-card results are reported separately and never combined into a
  composite rate — no "any of these K cards" number exists anywhere in Nebula.
- **The simulator is the tool for this** because casting depends on mana and sequencing.
  A draw-only question ("when do I see X") is not simulated at all; if one is ever
  needed it is an exact hypergeometric calculation, not a run.

**Recorded per run:** target card id, turn N, game count, mulligan policy, play/draw,
`registryVersion`, capture date, cast rate, interval, deck fingerprint.

**Unmodelled cards.** A card with no behavioural definition is inert in the model. A cast
rate for such a target is not a low number, it is a **blank**: reported as
`UNRESOLVED — no behavioural definition`, never as 0% and never silently omitted.
Expanding that coverage is a separate workstream (§8), not a pipeline stage.

### 5.1 Never

Win rate. Win probability. "Performs better." An unmodelled target is reported as
`UNRESOLVED`, never as a low percentage (the 2026-11-19 investigation found 45 of 100
cards inert on the sampled list).

---

## 6. Output contract

One markdown report per deck, 12 sections in fixed order:

1. Deck information · 2. Deck validation · 3. Role balance · 4. Commander assessment ·
5. Combo certification · 6. Tournament (TopDeck) evidence · 7. Density calculations ·
8. Package analysis · 9. Theory evaluation · 10. Laya recommendation ·
11. Verification · 12. Historical continuity

Each section header carries: its status, its evidence label mix, and its sources.
Jin's two-pass output is §9–10 material, marked `INTERPRETED`; it never gains a tool,
never retrieves, never rewrites the evidence sections.

A report is valid when it is generated *with* sections marked `UNRESOLVED` — completeness
of structure is the requirement, not completeness of data (step 243).

---

## 7. Human authority

- Nebula proposes; it never mutates a deck.
- No automatic promotion of any interpretation into `VERIFIED`.
- A simulator run is an observation attached to a claim, never the claim itself.
- Decklist egress: the 2026-11-19 approval covers driving the cEDHData page for a deck.
  It does not extend to other sites, and it is not blanket consent for vault data.

---

## 8. Tracked workstreams (not pipeline stages)

- **Simulator card coverage.** Inert cards in the cEDHData model are a separate problem
  (2026-11-21). A target with no behaviour definition yields a blank, not a rate; raising
  coverage is studied on its own and does not gate P0.
- **Tag coverage gaps.** Cards the community has not tagged carry no role and are listed
  by name in every coverage report. The list is evidence, not noise — it says which
  cards the taxonomy cannot speak about yet.
- **Laya's role** given 55/70 answers sit below 0.30 confidence.

## 9. Role coverage (D6)

| Role | Tagger anchor | Covers |
|---|---|---|
| `ramp` | ramp | rocks, dorks, land ramp |
| `draw` | card advantage | draw, selection, wheels |
| `tutor` | tutor | finding a specific card |
| `removal` | removal | answering a permanent |
| `counter` | counterspell | answering a spell |
| `wipe` | sweeper | answering the board |
| `protection` | protection | keeping your own things alive |
| `stax` | hate | taxing or denying resources |
| `recursion` | recursion | graveyard returns |

Two rules that keep the numbers honest:

1. **Ancestry, not string matching.** `tutor-creature-giant` counts as `tutor` because
   the Tagger tree says so, not because the word appears.
2. **The denominator is nonland cards.** A land has no role to cover; land count is its
   own diagnostic. Every report prints classified / nonland, untagged cards by name, and
   the tag-store version.
3. **Overlap is disclosed, not suppressed (D7).** Role counts are per role and do not sum
   to the deck size. The report lists every card in more than one role, so a card doing
   double duty is visible rather than averaged away.

## 10. Not yet decided

- Report delivery target (file, Obsidian, Discord) — deferred per design step 248.
- Whether land ramp (Ancient Tomb, land-fetching) belongs in the `ramp` figure or only in
  the land diagnostic. Default today: excluded, lands reported separately.
