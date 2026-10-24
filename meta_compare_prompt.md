# PROMPT — nebula: meta-compare deliverable packet

Copy this prompt into a fresh chat to continue working on the meta-compare package.

---

## Context

You are working on the **nebula** project — a Magic: The Gathering deck audit tool built on GitHub (St-Milton1013/nebula). The user is a MTG cEDH deck audit specialist.

**Active files (in the nebula repo at `nebula/`):**
- `NEBULA-DESIGN-PLAN.md` — main design plan (331 lines)
- `NEBULA-ARCHETYPE-CLASSIFICATION.md` — archetype band (turbo/stax/control/storm)
- `NEBULA-META-COMPARE.md` — meta comparison (TopDeck Top-16)
- `NEBULA-IDEAS/frequency_pool_design.md` — **frequency pool design (NEW, this session)**
- `NEBULA-IDEAS/00-topdeck_meta_meta.md` — TopDeck Top-16 idea

**Vault (Obsidian) — saved files:**
- `/Users/Main/ObsidianVault/user data/nebula/high_value_repo_research.md` — repo research
- `/Users/Main/ObsidianVault/user data/nebula/frequency_pool_design.md` — frequency pool design

**Local data (mounted on this machine):**
- `mtg_laya_project/config/topdeck_tournament_top16.json` + `topdeck_events.json` (400 top-16 decks, 25 CEDH tournaments, each 16 players)
- `mtg_laya_project/config/topdeck_all_tournaments.json` (1275 tournaments)
- `mtg_laya_project/cards.json` (102-card card truth database)
- `mtg_laya_project/config/rules_index_academyruins.json` (3,166 rules from Academy Ruins API)
- CEDHStats / Scryfall data available locally and via MCP tools

---

## Current state of the frequency pool

The meta-compare package (`archetype.meta_compare`) is being built around a **frequency pool** of TopDeck.gg Top-16 decks. The following constraints are already set:

1. **Remove stickers** — always exclude sticker-sheet cards (no gameplay effect)
2. **Remove commanders** — exclude the Commander card from the pool
3. **Limit to 6 months** — only tournaments within the last 6 months
4. **Averages of each typing** — compute average color pips, mana types, CMC per card
5. **All in headers** — the frequency pool is delivered in the headers section of the report

**Already identified gap:** there is no way to check turn count or game length — these data are not available from the current sources.

---

## What to work on

In the new chat, deliver the following for the frequency pool package:

### A. Complete the package contents

List every component that should go into the meta-compare / frequency pool delivery packet. For each component:

1. **Name** — e.g., "Frequency pool", "Archetype band", "Deck validation", etc.
2. **Input** — what data it consumes
3. **Output** — what it produces
4. **Pipeline stage** — where it runs (before the LLM sees data, or as part of the report)
5. **Sources used** — which data sources (TopDeck.gg API, CEDHStats, Scryfall, local cards.json, local rules index, etc.)

Components to evaluate (not all will make it in — rank by value and feasibility):

- Frequency pool (card frequency across top-16 decks)
- Archetype band (turbo/stax/control/storm)
- Deck validation (format, card count, commander inclusion)
- Card count distribution (mana curve, drop frequency)
- Deck lifecycle (turn distribution, game length) — **note: these data are not currently available**
- Win rate / tournament data (from CEDHStats, MTGGoldfish)
- Archentype band result (from archetype.classify)
- Comparison (vs other decks)
- Rules index (Academy Ruins)
- Card database (local cards.json)

### B. Define the delivery packet structure

Propose a concrete structure for the delivery packet. Define:

1. **Input schema** — what the LLM passes in (decklist, metadata)
2. **Output schema** — what the adapter returns (headers, frequency pool, typing averages)
3. **Report section** — where each component appears in the final report
4. **Caveats to state** — what the data can and cannot support

### C. Resolve the open questions

- **Turn count / game length:** do we mark these as "not available" and skip them, or do we find another source? Be explicit.
- **CEDHStats integration:** what specific stats would we use (commanders, tournaments, meta)? How would they be fetched and cached?
- **Scryfall integration:** what info would we use (bulk data, card details, legalities)?
- **6-month window:** define the reference date (current date, or last retrieval date). Which events actually qualify (the local data has 25 tournaments, each 16 players — none have 50+ players, and the dates are all 2026-10-18)?

### D. Decision priorities

Rank the following by priority (1 = do first):

- [ ] Frequency pool (card frequency) — HIGHEST priority
- [ ] Typing averages
- [ ] Headers section
- [ ] Display of power level (e.g., "TURBO-STORM" style result)
- [ ] Deck validation
- [ ] Card count distribution
- [ ] Win rate data from CEDHStats
- [ ] Scryfall info (bulk data, legalities)
- [ ] Turn count / game length
- [ ] Comparison to other decks
- [ ] Rules index lookups
- [ ] Archetype band result

---

## Constraints

- Everything stays local — no cloud upload, no live API calls during the audit.
- The adapter is the single data-fetching layer — the LLM calls `num_adapter`, never reads files directly.
- `cedh_eligibility` = `CANDIDATE_UNCONFIRMED` for all TopDeck tournaments — cite this.
- No sticks in the pool (remove sticker sheets).
- The frequency pool is the meta reference, not the archetype distribution.
- Follow the design philosophy: modular, parts feed each other but aren't dependent, failures return `AVAILABLE`/`PARTIAL`/`UNSUPPORTED`.

---

## Deliverable format

Produce a markdown document (or a series of documents in the nebula repo) that covers:

1. **Package contents** — complete list of components with inputs, outputs, and pipeline stages
2. **Delivery packet schema** — input and output JSON schemas
3. **Report section mapping** — where each component appears in the report
4. **Open questions** — with proposed resolutions
5. **Decision priorities** — ranked list with rationale
6. **Implementation note** — which files to create/modify in the nebula repo (NEBULA-*, NEBULA-IDEAS/*, vault notes)

Deliver a complete, actionable design document that can serve as the blueprint for the meta-compare package.
