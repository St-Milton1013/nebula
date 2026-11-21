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
| D3 | **The simulator answers one question:** probability that a *target card* reaches a *zone* by *turn N*. Not "can we win". | No win-rate field anywhere in Nebula. See §5. |
| D4 | Nebula builds the **pipeline** (P0 → P3 in that order). | Later stages may not be built before their prerequisites. |
| D5 | Single-deck review; Jin's two-pass critic is the review layer. | Multi-deck is out of scope; `/compare` is not in the pipeline. |

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

**The question:** `P(target card reaches zone Z by turn N)`.

Separate metrics, never merged (design steps 139–140, 144):

| Metric | Meaning |
|---|---|
| `cast_by_turn` | the card was *cast* by turn N (mana was available and sequenced) |
| `in_hand_by_turn` | the card was *in hand* by turn N |
| `seen_by_turn` | drawn, tutored, revealed, or otherwise accessed by turn N — definition recorded per run |

**Recorded per run:** target card id, zone, turn N, game count, mulligan policy, play/draw,
`registryVersion`, capture date, rate, interval, coverage limits.

### 5.1 Two tools, not one

- **"When do we see cards?"** is a card-draw question with no mana or interaction in it.
  Compute it exactly: hypergeometric, stdlib only, no browser, no egress, no simulation.
- **"When can we cast cards?"** depends on mana and sequencing. That is the simulator's
  job, and the only job it is uniquely qualified for.

### 5.2 Multi-card questions

Per-card rates **must not** be multiplied into `1 − Π(1 − pᵢ)`. Draws come from one
100-card deck, so the events are negatively correlated and share mana; that formula
overstates the answer. Permitted forms:

- report the set of per-card rates separately (default), or
- a union bound `Σ pᵢ` as an explicit upper bound, labelled as such, or
- an exact hypergeometric for "at least one of these K cards" when the question is
  purely about access, not casting.

A composite "any target" number is not a substitute for per-card results (step 144).

### 5.3 Never

Win rate. Win probability. "Performs better." Cards not modelled are reported as
limitations, not treated as blanks (the 2026-11-19 investigation found 45 of 100 cards
inert on the sampled list).

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

## 8. Not yet decided

- Code home: fresh package in `St-Milton1013/nebula` vs reviving the `master` prototype.
- Whether `master` is reference-only or the seed of the build.
- Report delivery target (file, Obsidian, Discord) — deferred per design step 248.
- Laya's role given 55/70 answers sit below 0.30 confidence.
