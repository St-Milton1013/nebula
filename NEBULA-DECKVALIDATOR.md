# NEBULA — DECK VALIDATOR ADAPTER

**Capability ID:** `archetype.deck_validator`
**Owner:** Codie (measurement) + Jin (interpretation)
**Date:** 2026-10-24
**Status:** DESIGN REFERENCE — not implemented

---

## 1. Package contents

The deck validator adapter is a **foundational** component that every other
adapter depends on. It validates the input decklist against MTG construction
rules before any other analysis runs.

| Check | What it verifies |
|---|---|
|| **Format** | Format-specific construction rules (Commander, Standard, etc.) |
| **Card count** | Deck size limits (mainboard + commander/partners/companions) |
| **Commander inclusion** | Exactly one commander card present |
| **Partner/companion detection** | Identify partner/companion cards (extra values) |
| **Singleton rules** | No duplicate non-commander cards (one copy each) |
| **Color identity** | Commander color identity consistency |
| **Banned cards** | Cards banned by format (banned cards list) |
| **Mainboard count** | Actual mainboard size (includes partners/companions) |

### Data sources

| Source | Role | Notes |
|---|---|---|
| `cards.json` | Local cache (card facts) | Mana cost, CMC, color identity, type line, keywords |
| Scryfall ban list | Optional (local cache) | Commander/banned cards by format. If missing, mark `PARTIAL`. |
| `NEBULA-ARCHETYPE-CLASSIFICATION.md` | Reference | Commander color identity rules |

### Key fields

| Field | Source | Notes |
|---|---|---|
|| `format` | Input (e.g., "commander", "standard") | Format to validate against |
| `decklist` | Input (parsed card names) | Raw decklist |
| `card_count` | Input (post-parsing) | Total cards after parsing |
| `commander_count` | `cards.json` | Number of commander cards found |
| `partner_count` | `cards.json` | Number of partner cards found |
| `companion_count` | `cards.json` | Number of companion cards found |
| `duplicates` | `cards.json` | List of cards with >1 copy (non-commander) |
| `format_legal` | `cards.json` | Format legality per card from `cards.json` |
| `banned` | Scryfall ban list | Banned cards |
| `color_identity` | `cards.json` | Commander color identity |
| `mainboard_count` | Derived | Actual mainboard size (card_count - commander_count - partner_count - companion_count) |
| `status` | Derived | `AVAILABLE` / `PARTIAL` / `UNSUPPORTED` |

---

## 2. Delivery packet schema

### 2.1 Input schema

```json
{
  "adapter": "num_adapter",
  "mode": "deck_validator",
  "decklist": ["Sol Ring", "Ancestral Recall", "Thrasios, Triton Hero"],
  "metadata": {
    "format": "commander",
    "deck_name": "Example deck",
    "audit_date": "2026-10-24"
  },
  "options": {
    "include_banned_check": true,
    "include_color_identity": true,
    "show_details": true
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `decklist` | array of strings | yes | Card names (parsed from raw text) |
| `metadata.format` | string | yes | e.g., "commander", "standard", "modern" |
| `options.include_banned_check` | boolean | no | `true` |
| `options.include_color_identity` | boolean | no | `true` |
| `options.show_details` | boolean | no | `true` |

### 2.2 Output schema

```json
{
  "adapter": "num_adapter",
  "mode": "deck_validator",
  "status": "AVAILABLE",
  "deck": {
    "format": "commander",
    "card_count": 100,
    "commander_count": 1,
    "partner_count": 1,
    "companion_count": 0,
    "mainboard_count": 98,
    "duplicates": [],
    "has_commander": true,
    "color_identity": ["W", "R"],
    "banned": [],
    "format_legal": true
  },
  "issues": [],
  "warnings": [],
  "caveats": [
    "Commander ban list not cached; banned-card check is PARTIAL",
    "Commander legality needs ban list (not cached)"
  ]
}
```

### 2.3 Report section mapping

| Report section | Source output key | Status |
|---|---|---|
| **Deck validation** | `deck` + `issues` + `warnings` | AVAILABLE |
| **Card count** | `deck.card_count` | AVAILABLE |
| **Commander inclusion** | `deck.has_commander` | AVAILABLE |
| **Singleton check** | `deck.duplicates` | AVAILABLE |
| **Color identity** | `deck.color_identity` | AVAILABLE |
| **Banned cards** | `deck.banned` | PARTIAL (ban list not cached) |

### 2.4 Caveats to state

The report must state:

1. **Commander ban list** — Commander legality requires the ban list (not cached locally). Mark as `PARTIAL`.
2. **Card count** — Commander decks require 99 cards (1 commander + 98 mainboard). Standard decks require 60 cards (no commander). Mark per format.
3. **Singleton rules** — Non-commander cards must appear exactly once. Commander is exempt.

---

## 3. Integration with other components

| Source | Data | Package use |
|---|---|---|
| `cards.json` | Card facts (mana, type, color) | Card validation |
| Scryfall ban list | Banned cards | Banned card check |
| `NEBULA-ARCHETYPE-CLASSIFICATION.md` | Commander color identity rules | Commander color validation |

The deck validator is the **first step** in the pipeline. Every other
component depends on a clean card list.

---

## 4. Open questions (resolved)

### 4.1 Deck validation — scope

**Decision:** Validate against the specified format only. Commander format is
the primary target (the meta-compare package is Commander-focused).

### 4.2 Commander color identity

**Decision:** Commander color identity is derived from the commander's colors
as stored in `cards.json`. No additional derivation needed.

### 4.3 Banned cards

**Decision:** Commander banned cards require the Commander ban list (from
`mcp__mtg_unified__bulk_ban_list`). If not cached locally, mark as `PARTIAL`.
Do not fabricate legality verdicts.

---

## 5. Decision priorities

| Rank | Component | Status | Rationale |
|---|---|---|---|
| 1 | **Deck validation** | AVAILABLE (design) | Foundational — every other component depends on it |
| 2 | **Frequency pool** | PARTIAL (local) | Core deliverable; 50+ filter blocked |
| 3 | **Typing averages** | PARTIAL (local) | Ships with frequency pool |
| 4 | **Tagger** | PARTIAL | Needed for role classification |
| 5 | **Archetype classify** | PARTIAL | Future work |

---

## 6. Implementation note

### Files to create

| File | Purpose |
|---|---|
| `NEBULA-DECKVALIDATOR.md` | **This document** — the deck validator blueprint. |
| `archetype/deck_validator.py` | New module: `num_adapter(mode="deck_validator", decklist, options)` — validates decklist against format rules. |

### Files to modify

| File | Change |
|---|---|
| `NEBULA-DESIGN-PLAN.md` | Add `archetype.deck_validator` to capability inventory. |
| `NEBULA-FREQUENCY-POOL.md` | Add deck validation to package contents. |
| `NEBULA-META-COMPARE.md` | Update the frequency-pool section to reflect the validated input schema. |

### Constraints

- Everything stays local; no live API calls during the audit.
- `num_adapter` is the single data-fetching layer; the LLM never reads files directly.
- `cedh_eligibility = CANDIDATE_UNCONFIRMED` is cited in the report.
- Design philosophy: modular; failures return `AVAILABLE` / `PARTIAL` / `UNSUPPORTED`.
- Commander ban list is optional; missing → `PARTIAL`, not `UNSUPPORTED`.

---

## 7. Reference — Thrasios, Triton Hero

Example deck: `Thrasios, Triton Hero` + 98 other cards.

Expected validation output:

```json
{
  "status": "AVAILABLE",
  "deck": {
    "format": "commander",
    "card_count": 99,
    "commader_count": 1,
    "duplicates": [],
    "has_commander": true,
    "color_identity": ["W", "R"],
    "banned": [],
    "format_legal": true
  },
  "issues": [],
  "warnings": [
    "Commander ban list not cached"
  ]
}
```

---

*This completes the deck validator adapter design. It validates the decklist before any other component runs.*
