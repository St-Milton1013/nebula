# NEBULA — DESIGN PLAN

**Repo:** `nebula` (St-Milton1013/nebula, `main`)
**Purpose:** Top-down design planning for the nebula tool — catalog every capability, extension, and idea so nothing is lost while work proceeds.

**Design philosophy:** modular — parts feed each other but aren't dependent. A module failure returns `AVAILABLE`/`PARTIAL`/`UNSUPPORTED` and the report keeps going. Meta sources are all free and usable.

---
## How to keep this plan useful

- **Capabilities** (e.g. `archetype.classify`) are detailed in dedicated files in the repo root.
- **Ideas** (proposed extensions, reference candidates, "nice-to-have but not decided") live in the `NEBULA-IDEAS/` folder. Read them there, not in the main plan.
- When an idea graduates to a full capability, move it out of `NEBULA-IDEAS/` and into the repo root as a dedicated file. Never delete an idea file; archive it in `NEBULA-IDEAS/ARCHIVED/` with a one-line note.
- Write + read this file as the source of truth for what exists, what's proposed, and what's open.

---
## Icon legend

| Marker | Meaning |
|---|---|
| **PROPOSED** | Concept approved, not implemented. No code, no data, no commitments. |
| **AVAILABLE** | Source data / code exists; module ready. |
| **PARTIAL** | Module exists but incomplete. |
| **UNSUPPORTED** | Cannot do this with current sources. |
| **BLOCKED** | Waiting on a decision or external input. |
| **deferred** | Next step; pick one item at a time. |

---
## Open directions (must confirm before each pick)

At the start of every session, confirm the 2 open directions, then pick ONE
ideas item at a time from `NEBULA-IDEAS/`. Never move to multi-deck tooling or
final report architecture until the current item is decided.

See `NEBULA-CHECKLIST.md` for the full open menu.

---
## Capability inventory (as of 2026-10-24)

### Core (in-progress)

- **Step 7 — Metrics:** card metrics (castability, mana curve, combos, roles, tournament usage). [[NEBULA-STEPS-DETAIL.md]]
- **Step 9 — Roles/packages:** card role graph, relationship classification. [[NEBULA-STEPS-DETAIL.md]]
- **Step 10 — Metagame:** cohort prevalence, tournament usage, sandbox/legality context.

### Report (in-progress)

- **Step 15 — Final report:** deck facts + metrics + roles + recommendations,
  with evidence and provenance. [[NEBULA-STEPS-DETAIL.md]]

### Capabilities (PROPOSED — reference detail files)

- **`archetype.classify`** — turbo/stax/control/storm classification with 2×2
  quadrant + two polar bar tick-marks. Detailed in
  `NEBULA-ARCHETYPE-CLASSIFICATION.md`. [PROPOSED]
- **`archetype.meta_compare`** — compare a deck against the CEDH meta via
  TopDeck.gg Top-16 decks (400 decks from 25 tournaments, local cache). The
  package is built around a **frequency pool** of top-16 decks (card frequency
  + typing averages + headers), delivered in the report's headers section.
  See `NEBULA-FREQUENCY-POOL.md` (repo root) and `NEBULA-META-COMPARE.md`.
  Frequency pool is PARTIAL locally (50+ filter blocked — see `NEBULA-FREQUENCY-POOL.md`).

- **`archetype.learncedh`** — deck summary and performance metrics from
  LearnCEDH (narrative, strategy, synergies, combos, performance). Detailed in
  `NEBULA-LEARNCEDH.md`. [AVAILABLE]

- **`archetype.commander_spellbook`** — combo data from Commander Spellbook
  (cards, steps, rank, votes, salt). Detailed in
  `NEBULA-COMMANDER-SPELLBOOK.md`. [PROPOSED]

- **`archetype.tagger`** — card tags from Tagger (mechanical/behavioural, filtered for artwork). Detailed in `NEBULA-TAGGER.md`. [PROPOSED]

- **`archetype.hypercalculator`** — probability/chance metrics for cards in a
  deck (tag draw probability, opening hand tag distribution, combo tag chance, mana curve odds). Detailed in `NEBULA-HYPERCALCULATOR.md`. [PROPOSED]

- **`archetype.scryfall`** — card info retrieval (oracle text, mana, type, keywords, EDHREC rank, set, collector number) via the Scryfall API (with optional local cache). Detailed in `NEBULA-SCRYFALL.md`. [AVAILABLE]

- **`archetype.deck_validator`** — foundational adapter: validates decklist against Commander format rules (card count, commander inclusion, singleton, color identity, banned cards). Detailed in `NEBULA-DECKVALIDATOR.md`. [AVAILABLE]

### Frequency pool — extension to meta_compare

Reference: `NEBULA-FREQUENCY-POOL.md` (repo root) + archived vault note at
`NEBULA-IDEAS/ARCHIVED/frequency_pool_design.md` (and the Obsidian vault note
at ObsidianVault/user data/nebula/frequency_pool_design.md).

**Frequency pool design:**
- Build a **frequency pool** from TopDeck.gg Top-16 decks
- Always filter: **remove stickers**, **remove commanders**
- Filter tournaments to **last 6 months** (reference date = audit date)
- Compute **average typing** (color pips, mana types, CMC) per card
- All of this goes in the **headers** section of the report

**Verified local snapshot (2026-10-24):** 25 tournaments × 16 players = **400
top-16 decks**. All events dated 2026-10-18 (within 6 months of the audit date
2026-10-24). `cedh_eligibility = CANDIDATE_UNCONFIRMED` for all.

**Important status:** The **50+-player filter is NOT satisfiable locally**
(all events have exactly 16 players). The frequency pool is therefore
**PARTIAL** when based on the local snapshot. The 50+ filter applies only when
the live TopDeck API is available (future work). See `NEBULA-FREQUENCY-POOL.md`
§2 for the full schema, §3 for open-question resolutions.

### Ideas (NOT implemented — see NEBULA-IDEAS/)

The following are reference candidates only. They are NOT decisions. See
`NEBULA-IDEAS/` for full detail:

- `ideas.topdeck_meta` — TopDeck Top-16 meta comparison vs the 400 decks from
  25 tournaments. [PROPOSED] — read `NEBULA-IDEAS/00-topdeck_meta_meta.md`.

---
## Reference locations

| Purpose | Path |
|---|---|
| Main design plan | `NEBULA-DESIGN-PLAN.md` |
| Capability detail: archetype classification | `NEBULA-ARCHETYPE-CLASSIFICATION.md` |
| Capability detail: meta comparison (TopDeck Top-16) | `NEBULA-META-COMPARE.md` |
| Steps 7/9/10/15 detail | `NEBULA-STEPS-DETAIL.md` |
| **Ideas / reference folder** | **`NEBULA-IDEAS/`** |

---
*Design planning session — strict. Nothing sealed. Nothing marked DONE until a
decision exists. Pick one item at a time.*
