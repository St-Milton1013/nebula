# NEBULA — FREQUENCY POOL / META-COMPARE PACKAGE

**Capability ID:** `archetype.meta_compare` (extension)
**Owner:** Codie (measurement) + Jin (interpretation)
**Date:** 2026-10-24
**Status:** DESIGN REFERENCE — not implemented

---

## 1. Package contents

The meta-compare package is built around a **frequency pool** of TopDeck.gg Top-16 decks. This is the meta reference (not the archetype distribution). The frequency pool is delivered in the **headers section** of the report.

> **Verified data snapshot (2026-10-24):** 25 tournaments × 16 players = **400 top-16 decks**. All events share date `2026-10-18 17:00:00 UTC`, status `Complete`. `cedh_eligibility = CANDIDATE_UNCONFIRMED` for all. The local data has **no 50+-player events** — the 50+ filter must come from the live TopDeck API.

### Ranked component list (value × feasibility)

| Rank | Component | Status | Pipeline stage | Primary source |
|---|---|---|---|---|
| 1 | **Frequency pool** (card frequency across top-16 decks) | PARTIAL (local); AVAILABLE with live API | Before LLM; adapter output | TopDeck.gg API (cached Top-16 snapshot) |
| 2 | **Typing averages** (color pips, mana types, CMC, card-type breakdown) | PARTIAL (local); AVAILABLE with live API | Before LLM; adapter output | cards.json (Scryfall bulk) |
| 3 | **Headers section** (meta reference metadata) | AVAILABLE | Before LLM; adapter output | TopDeck.gg events (cache) |
| 4 | **Deck validation** (format, card count, commander inclusion) | AVAILABLE | Before LLM; adapter input | cards.json + decklist |
| 5 | **Archetype band result** (turbo/stax/control/storm) | PROPOSED (not implemented) | Before LLM; archetype.scores | Steps 7/9 metrics (deterministic) |
| 6 | **Card count distribution** (mana curve) | AVAILABLE | Before LLM; shares Step 7 | cards.json (cmc histogram) |
| 7 | **Comparison to other decks** (vs cohort) | PARTIAL | Before LLM; derived | frequency pool + archetype band |
| 8 | **Display of power level** (TURBO-STORM style render) | PARTIAL (once band implemented) | Report stage (Step 15) | archetype band result |
| 9 | **Scryfall info** (bulk data, legalities) | AVAILABLE (bulk); PARTIAL (Commander legality) | Before LLM; cards.json bulk data | cards.json (bulk) |
| 10 | **Rules index lookups** (Academy Ruins) | AVAILABLE | Report stage (Step 15) | rules_index_academyruins.json |
| 11 | **Win rate / tournament data from CEDHStats** | UNSUPPORTED | — | CEDHStats.org API (not live-callable in audit) |
| 12 | **Turn count / game length** | UNSUPPORTED | — | No source provides this |

### Notes on the ranked list

- **Items 1–3 are the core meta-compare package.** Frequency pool + typing averages + headers are one pipeline that ships together in the adapter output.
- **Item 4 is foundational.** Deck validation must run before any frequency computation (card resolution and commander removal depend on a clean card list).
- **Item 5 (archetype band)** is a separate capability (`archetype.classify`, per `NEBULA-ARCHETYPE-CLASSIFICATION.md`), but it feeds the meta-compare comparison and the "power level" display. It is PROPOSED, not implemented.
- **Item 8 is presentation.** It renders the archetype band result in the report; it becomes available once item 5 ships.
- **Items 11–12 are UNSUPPORTED.** They have no current source in the frozen snapshot. They are not skipped silently — the report states `NOT AVAILABLE`.
- **Item 10 (rules index)** is available but used narrowly (card-interaction lookups only). It is not part of the frequency pool pipeline.

### Pipeline stage summary

```text
LLM (decklist, metadata)  ──►  num_adapter("meta_pool", decklist, options)
         │
         ▼
   1. Deck validation  (format, count, commander)  [AVAILABLE]
         │
         ▼
   2. Fetch TopDeck events  (play >= 50)  [UNSUPPORTED locally; live API]
         │
         ▼
   3. Filter to <= 6 months  [AVAILABLE locally — all 25 events are 2026-10-18]
         │
         ▼
   4. Parse top-16 decklists  [AVAILABLE — text → card list via cards.json]
         │
         ▼
   5. Remove stickers  [AVAILABLE — Sticker Sheet AR4 + equivalents]
         │
         ▼
   6. Remove commanders  [AVAILABLE]
         │
         ▼
   7. Compute card frequency  [AVAILABLE]
         │
         ▼
   8. Compute typing averages  [AVAILABLE]
         │
         ▼
   9. Return headers + frequency pool + typing averages  [adapter output]
         │
         ▼
   10. Archetype band (archetype.classify)  [PROPOSED — separate]
         │
         ▼
   11. Report (Step 15)  [render frequency pool, typing averages, band, caveats]
```

---

## 2. Delivery packet schema

### 2.1 Input schema — what the LLM passes to `num_adapter`

```json
{
  "adapter": "num_adapter",
  "mode": "meta_pool",
  "decklist": ["Sol Ring", "Ancestral Recall", "Kraum, Ludevic's Opus", "Tymna the Weaver"],
  "metadata": {
    "deck_name": "Kraum/Tymna (example)",
    "format": "EDH",
    "player_seat": "Jake M [UNCS]",
    "audit_date": "2026-10-24"
  },
  "options": {
    "remove_stickers": true,
    "remove_commanders": true,
    "date_window_months": 6,
    "min_players": 50,
    "top_n": 100
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `decklist` | array of strings | yes | Card names, mainboard + commanders. Resolved via `cards.json` search_index. |
| `metadata.deck_name` | string | no | Human-readable label. |
| `metadata.format` | string | no | Expected format (e.g. `EDH`). |
| `metadata.player_seat` | string | no | Attribution if the deck came from a public Top-16 listing. |
| `metadata.audit_date` | string (ISO) | no | Reference date for the 6-month window. Default: audit run date. |
| `options.remove_stickers` | boolean | no | Always `true` in this package. |
| `options.remove_commanders` | boolean | no | Always `true` in this package. |
| `options.date_window_months` | integer | no | 6 (recommended). |
| `options.min_players` | integer | no | 50 (target; may be UNSUPPORTED locally). |
| `options.top_n` | integer | no | How many cards to emit in the frequency table (default 100). |

### 2.2 Output schema — what the adapter returns

```json
{
  "adapter": "num_adapter",
  "mode": "meta_pool",
  "status": "PARTIAL",
  "headers": {
    "source": "TopDeck.gg Top-16",
    "tournament_count": 25,
    "total_decks": 400,
    "dates": { "earliest": "2026-10-18", "latest": "2026-10-18" },
    "commander_removed": true,
    "stickers_removed": true,
    "min_players_requirement": 50,
    "min_players_applied": false,
    "cedh_eligibility": "CANDIDATE_UNCONFIRMED",
    "pool_note": "50+ filter not applied; local data has 16-player events only"
  },
  "frequency_pool": {
    "top_n": 100,
    "entries": [
      { "card": "Sol Ring", "frequency": 0.42, "rank": 1, "typing_avg": { "color_pips": 2.0, "mana_types": 1.0, "cmc": 2.0 } },
      { "card": "Ancestral Recall", "frequency": 0.38, "rank": 2, "typing_avg": { "color_pips": 3.0, "mana_types": 1.0, "cmc": 3.0 } }
    ]
  },
  "typing_averages": {
    "color_pips_avg": 2.4,
    "mana_types_avg": 1.8,
    "cmc_avg": 2.1,
    "card_type_breakdown": { "creature": 0.35, "land": 0.25, "instant": 0.15, "sorcery": 0.10, "artifact": 0.10, "planeswalker": 0.05 }
  },
  "archetype_band": null,
  "comparison": null,
  "caveats": [
    "400 decks is a top-16 sample, not the full CEDH meta.",
    "cedh_eligibility = CANDIDATE_UNCONFIRMED — flag, do not over-claim.",
    "50+ player filter not applied (local data: 16-player events).",
    "Static snapshot as of retrieved_at; not live."
  ]
}
```

| Output key | Type | Present when | Notes |
|---|---|---|---|
| `adapter` / `mode` | string | always | Identifies the caller and mode. |
| `status` | enum | always | `AVAILABLE` / `PARTIAL` / `UNSUPPORTED`. |
| `headers` | object | always | Meta-reference metadata, ships in the report's headers section. |
| `frequency_pool.entries` | array | always (even PARTIAL) | Sorted by frequency descending. |
| `typing_averages` | object | always | Pool-level average typing. |
| `archetype_band` | object \| null | when archetype.classify is wired | PROPOSED; currently `null`. |
| `comparison` | object \| null | when comparison is wired | Relative positioning vs cohort. |
| `caveats` | array of strings | always | Always state the data's limits. |

### 2.3 Report section mapping

| Report section | Source output key | Status |
|---|---|---|
| **Headers** (meta reference: pool size, dates, commander/sticker flags, eligibility) | `headers` | AVAILABLE |
| **Frequency pool** (table: card, frequency, rank, typing_avg) | `frequency_pool.entries` | AVAILABLE (PARTIAL w.r.t. 50+ filter) |
| **Typing averages** (color pips avg, mana types avg, CMC avg, card-type breakdown) | `typing_averages` | AVAILABLE |
| **Deck facts** (format, count, commander inclusion, validation) | deck validation (input passthrough) | AVAILABLE |
| **Power level** (archetype band result: turbo/stax/control/storm + axis ticks) | `archetype_band` | PROPOSED — PARTIAL until implemented |
| **Comparison** (nearest cohort, axis sigma deviations) | `comparison` | PARTIAL — pending archetype band + cohort |
| **Rules lookups** (specific card-interaction checks) | `rules_index_academyruins.json` | AVAILABLE (narrow use) |
| **Frequency context** (per-card: "X is top-10% in top-16") | derived from `frequency_pool` + decklist | AVAILABLE |
| **Deck lifecycle** (turn distribution, game length) | — | UNSUPPORTED — not available |

### 2.4 Caveats to state (required, verbatim text supported)

The report must state all of the following when the frequency pool is active:

1. **Sample scope:** "400 decks is a Top-16 sample, not the full CEDH meta. It represents the format's most competitive tier."
2. **CEDH eligibility:** "`cedh_eligibility = CANDIDATE_UNCONFIRMED` for all tournaments. The format field says `EDH`; the events file labels them 'CEDH' but the eligibility claim is not confirmed. Do not over-claim."
3. **50+ filter:** "The 50+-player filter was not applied: the local snapshot contains 16-player events only. Results are therefore a Top-16 reference, not a large-field meta reference."
4. **Data freshness:** "Data is a static snapshot (retrieved `2026-10-20T04:22:41Z`). Not live."
5. **Frequency pool vs archetype distribution:** "The frequency pool is the meta reference (card frequencies), not the archetype distribution. Archetype distribution is a separate output."
6. **No turn count / game length:** "Turn count and game length are not available from any source in the frozen snapshot."

---

## 3. Open questions (resolved)

### 3.1 Turn count / game length — NOT AVAILABLE, skip

**Decision:** Mark as `NOT AVAILABLE` and skip. No source in the frozen snapshot provides turn count, game length, or play-by-play data. TopDeck top-16 decklists are raw text with no game records.

- Do **not** fabricate turn counts or game lengths.
- Do **not** attempt to infer them from decklist text (no deterministic mapping exists).
- The report must state: "Turn count / game length: NOT AVAILABLE (no source in the frozen snapshot)."
- If a future source (e.g., TopDeck API with play-by-play, or tournament game records) becomes available, revisit this as a separate module. It is out of scope for this package.

### 3.2 CEDHStats integration — player rankings, separate module, PARTIAL

**What stats:** Use CEDHStats **player rankings** (entries, PPG, top cut %, floor, veterans, ceiling) — NOT tournament win rates. Player rankings are context only, never authority. This matches the existing `cedhstats/player_rankings.json` (300 players parsed).

**How fetched & cached:**
- Fetch via CEDHStats.org API (`cedhstats.org/players`), cache to `cedhstats/player_rankings.json`.
- Do **not** fetch live during the audit (constraint: no live API calls). Use the cached file.
- If the cached file is missing/partial, mark `PARTIAL` in the report and continue without it.

**Where it plugs in:** As a separate module, not core to `meta_compare`. It enriches the "context" layer (Step 10/12), e.g. "Krau/Tymna is a top-ranked commander." It does not prove or disprove anything about the audited deck.

**Failure handling:** Missing/partial data → `PARTIAL`; no data at all → `UNSUPPORTED`, continue.

### 3.3 Scryfall integration — bulk data from cards.json; legalities PARTIAL

**What info is used:** Bulk data from `cards.json` (already localized, 33,777 cards):
- `name`, `lowercase_name` (for fast lookup)
- `mana_cost`, `cmc`, `color_identity` (WUBRG)
- `type_line`, `keywords`, `power`, `toughness`
- `edhrec_rank`, `oracle_text_preview`, `scryfall_set`, `scryfall_collector_number`, `status`

**Commanders legality:** `cards.json` contains `edhrec_rank` but **not** Commander legality or the ban list. The Commander ban list requires `mcp__mtg_unified__bulk_ban_list` (external) or a locally cached banned-list file. During the audit, mark Commander legality as `PARTIAL` (bulk data available; ban-list check not cached) and do not fabricate legality verdicts.

**Live Scryfall calls:** None during the audit. Use only the local `cards.json` snapshot.

### 3.4 6-month window — reference date and qualifying events

**Reference date:** The current audit date (`2026-10-24`), not the retrieval date. The adapter computes the window as `audit_date - 6 months` to `audit_date`.

**Which events qualify (local data):**
- All 25 local events have `date = "2026-10-18 17:00:00 UTC"`, within 6 months of `2026-10-24`.
- So the **6-month filter is satisfied** by local data (all events pass).
- The **50+-player filter is NOT satisfiable** locally: every event has exactly 16 players.
- Result: the frequency pool is **PARTIAL** — the 6-month window passes, but the 50+ representativeness filter does not.

**Implementation note for the 50+ filter:** The live TopDeck API is the only source for `play >= 50` events. Since the audit cannot make live calls, the adapter must:
1. Operate on the cached 25-event snapshot.
2. Set `headers.min_players_applied = false` with `headers.pool_note` explaining why.
3. Return `status = PARTIAL` so the report does not over-claim representativeness.

**Frozen window fix (90-day lapse):** The underlying metagame window (Step 10, `NEBULA-STEPS-DETAIL.md` §10.3) was previously a 3-month (90-day) frozen window — past 90 days the adapter fell back to `UNSUPPORTED`. This is fixed by extending the frozen window to **6 months** and adding a **monthly rolling recompute** (see `NEBULA-STEPS-DETAIL.md` §10.3). The frequency pool's 6-month filter is consistent with this: the adapter always uses the most recent 6-month frozen window, and a stale window (>30 days old) is reported as `PARTIAL (stale window)`, never silently dropped to `UNSUPPORTED`.

**Proposed report text:** "Frozen window: 6 months (recomputed monthly). Latest recompute: 2026-10-01. Reference date: 2026-10-24."

**Proposed reference-date text for the report:** "Reference date: 2026-10-24. All 25 local top-16 events (dated 2026-10-18) fall within the 6-month window; none meet the 50+-player criterion."

---

## 4. Decision priorities

Ranked 1 = do first. This ranking balances **value to the audit** and **feasibility in the frozen-snapshot audit** (no live API calls).

| Rank | Component | Status | Rationale |
|---|---|---|---|
| 1 | **Frequency pool** (card frequency) | PARTIAL (local) | HIGHEST priority — this is the core deliverable. The computation is available; only the 50+ filter is blocked. Even PARTIAL output is useful as a Top-16 reference. |
| 2 | **Typing averages** | PARTIAL (local) | Ships with the frequency pool. Low effort, high signal ("this format's meta averages 2.4 color pips, 1.8 mana types"). |
| 3 | **Headers section** | AVAILABLE | The container; trivial and always works. |
| 4 | **Deck validation** | AVAILABLE | Foundational. Every other component depends on a clean card list. Do this first internally. |
| 5 | **Archetype band result** (turbo/stax/control/storm) | PROPOSED | The "power level" classification. Not implemented yet; depends on Steps 7/9. Highest-value future work. |
| 6 | **Card count distribution** (mana curve) | AVAILABLE | Shares Step 7. Enriches the report; low effort. |
| 7 | **Comparison to other decks** (vs cohort) | PARTIAL | Needs the frequency pool + archetype band. Derive once those ship. |
| 8 | **Display of power level** (TURBO-STORM render) | PARTIAL | Presentation of item 5. Available once the band ships. |
|| 9 | **Scryfall info** (bulk data, legalities) | AVAILABLE (full card info); PARTIAL (legality) | Full card info (oracle text, mana, type, keywords, EDHREC rank) is available via the Scryfall API — the adapter is locked down and doesn't depend on cards.json. Commander legality needs the ban list (not cached). Keep to card identification only. |
| 10 | **Rules index lookups** | AVAILABLE | Narrow use: specific card-interaction checks only (e.g., "does card X interact with Y?"). Not part of the frequency pipeline. |
| 11 | **Win rate / tournament data from CEDHStats** | UNSUPPORTED | Player rankings are context-only; live API not callable in the audit. Separate module; do not block the core package. |
| 12 | **Turn count / game length** | UNSUPPORTED | No source exists. Mark `NOT AVAILABLE`; do not chase. Skipped. |

**Sequencing note:** Items 1–3 and 4 can ship in the same adapter pass. Items 5–8 are gated on `archetype.classify` implementation. Items 11–12 are never gating; they are always report-only caveats.

---

## 5. Implementation note

### Files to create

| File | Purpose |
|---|---|
| `NEBULA-FREQUENCY-POOL.md` | **This document** — the blueprint. (new, in repo root) |
| `archetype/meta_pool.py` | New module: `num_adapter("meta_pool", decklist, options)` — the single data-fetching layer. Parse decklists, apply filters, compute frequency + typing averages, return the output schema. |

### Files to modify

| File | Change |
|---|---|
| `NEBULA-DESIGN-PLAN.md` | Add `archetype.meta_compare` to the capability inventory; mark the frequency pool as a graduated extension of `archetype.meta_compare` (move out of `NEBULA-IDEAS/` when implemented). |
| `NEBULA-META-COMPARE.md` | Update the frequency-pool section to reflect the verified local snapshot (25 events, 16 players each, no 50+ filter), the resolved 6-month reference date, and the `CANDIDATE_UNCONFIRMED` citation requirement. |
| **Frozen-window fix:** The underlying metagame window was extended from 3 months (90 days) to 6 months, and the failure status was upgraded from `UNSUPPORTED` to `PARTIAL` with explicit staleness reporting. See `NEBULA-STEPS-DETAIL.md` §10.3 and the frequency-pool §3.4. The rolling refresh protocol (monthly recompute) prevents the 90-day lapse. |
| `NEBULA-IDEAS/frequency_pool_design.md` | Archive (do not delete): mark this design reference as read and add the data-verified note about the 50+ filter and the 6-month window. Keep the file; archive it per the design plan. |
| Obsidian vault `frequency_pool_design.md` | Sync with the archived `NEBULA-IDEAS/frequency_pool_design.md` (update status to "archived design reference"). |

### Data-file references (verified on this machine)

| Path | Verified shape |
|---|---|
| `mtg_laya_project/config/topdeck_events.json` | list of 25 events; each: `{id, name, date: "2026-10-18 17:00:00 UTC", players: 16, status: "Complete"}` |
| `mtg_laya_project/config/topdeck_tournament_top16.json` | dict keyed by TID; each: `{TID, cedh_eligibility: "CANDIDATE_UNCONFIRMED", evidence_status: "AVAILABLE", retrieved_at, top16_count, top16: [{decklist: "raw text", standing, points, ...}]}` |
| `mtg_laya_project/nodes/00_CardTruth/cards.json` | 33,777 cards; `cards[]` + `search_index` (lowercase_name → card); each card: `{name, lowercase_name, mana_cost, cmc, color_identity, type_line, keywords, edhrec_rank, status}` |
| `mtg_laya_project/config/rules_index_academyruins.json` | 3,166 rules (Academy Ruins API) |

### Constraint compliance (recap)

- Everything stays local; no live API calls during the audit.
- `num_adapter` is the single data-fetching layer; the LLM never reads files directly.
- `cedh_eligibility = CANDIDATE_UNCONFIRMED` is cited in the report.
- No stickers in the pool (remove sticker sheets).
- The frequency pool is the meta reference, not the archetype distribution.
- Design philosophy: modular; parts feed each other but aren't dependent; failures return `AVAILABLE` / `PARTIAL` / `UNSUPPORTED`.
