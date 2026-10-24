# NEBULA — SCRYFALL ADAPTER (card info adapter)

**Capability ID:** `archetype.scryfall`
**Owner:** Codie (measurement) + Jin (interpretation)
**Date:** 2026-10-24
**Status:** DESIGN REFERENCE — not implemented

---

## 1. Package contents

The Scryfall adapter provides the full **card information** for each card in a deck, complementary to the Tagger adapter's card tags. Together they give a complete picture of every card.

| Source | Data | Package use |
|---|---|---|
| **Tagger** | Card tags (mechanical/behavioural) | What the card does (behavioural analysis) |
| **Scryfall** | Card info (oracle text, mana, type, keywords) | What the card is (structural analysis) |
| **Both** | Combined | Role classification, combo detection, mana analysis |

### Data sources

| Source | Role | Notes |
|---|---|---|
| **Scryfall API** | Primary (authoritative) | `https://api.scryfall.com` — provides EVERY field needed: name, mana cost, CMC, color identity, type line, power/toughness, keywords, oracle text, EDHREC rank, set, collector number, status |
| `cards.json` | Optional local cache | 33,777 cards from Scryfall bulk data. Faster lookup (no network) during audit. **Not required** — the adapter can work with just the API. |
| `tagger.scryfall.com` | Separate adapter (card tags) | Card tags (mechanical/behavioural); never merged into this adapter |

> **Lock-down note:** The adapter does NOT depend on `cards.json`. The local file is an optional cache for audit speed; the Scryfall API is the single source of truth. If `cards.json` is missing or a card is not found, the adapter falls back to the API. During the audit, `cards.json` must be a pre-fetched snapshot (no live API calls).

### Key fields

| Field | Source | Notes |
|---|---|---|
| `name` | Scryfall / `cards.json` | Canonical card name |
| `lowercase_name` | Scryfall / `cards.json` | Fast lookup key |
| `mana_cost` | Scryfall / `cards.json` | E.g., `{R}{W}` |
| `cmc` | Scryfall / `cards.json` | Converted mana cost (float) |
| `color_identity` | Scryfall / `cards.json` | WUBRG string/list |
| `color_identity_count` | Scryfall / `cards.json` | Number of colored pips |
| `type_line` | Scryfall / `cards.json` | E.g., "Legendary Creature — Kor Soldier Ally" |
| `power` | Scryfall / `cards.json` | E.g., "1" |
| `toughness` | Scryfall / `cards.json` | E.g., "1" |
| `keywords` | Scryfall / `cards.json` | List of keyword names |
| `keyword_count` | Scryfall / `cards.json` | Count of keywords |
| `oracle_text_preview` | Scryfall / `cards.json` | Oracle text (full text from API) |
| `edhrec_rank` | Scryfall / `cards.json` | EDHREC rank (numeric or null) |
| `scryfall_uri` | Scryfall / `cards.json` | Scryfall card URL |
| `scryfall_set` | Scryfall / `cards.json` | Set code |
| `scryfall_collector_number` | Scryfall / `cards.json` | Collector number |
| `status` | Scryfall / `cards.json` | Card status (ok) |

### Fallback chain (locked down)

1. **Local cache check** — if `cards.json` has the card, use it (fast)
2. **Scryfall API** — fetch any card not in the cache (canonical source)
3. **Skip** — card not found in either source; return `PARTIAL`

### Pipeline stage

**Before the LLM sees the deck.** The adapter returns card info per card; the package uses this alongside the Tagger's card tags to determine what a card is and what it does. The adapter is the single data-fetching layer; the LLM never reads files directly.

---

## 2. Delivery packet schema

### 2.1 Input schema — what the LLM/Llama passes to `num_adapter`

```json
{
  "adapter": "num_adapter",
  "mode": "scryfall",
  "decklist": ["Sol Ring", "Ancestral Recall", "Thrasios, Triton Hero", "Tymna the Weaver"],
  "metadata": {
    "deck_name": "Kraum/Tymna (example)",
    "format": "EDH",
    "audit_date": "2026-10-24"
  },
  "options": {
    "include_oracle_text": true,
    "include_keywords": true,
    "include_color_identity": true,
    "include_edhrec_rank": true,
    "include_power_toughness": true
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `decklist` | array of strings | yes | Card names (mainboard + commanders). Resolved via `cards.json`. |
| `options.include_oracle_text` | boolean | no | `true` (default) |
| `options.include_keywords` | boolean | no | `true` (default) |
| `options.include_color_identity` | boolean | no | `true` (default) |
| `options.include_edhrec_rank` | boolean | no | `true` (default) |
| `options.include_power_toughness` | boolean | no | `true` (default) |

### 2.2 Output schema — what the adapter returns

```json
{
  "adapter": "num_adapter",
  "mode": "scryfall",
  "status": "AVAILABLE",
  "card_info": [
    {
      "card": "Thrasios, Triton Hero",
      "scryfall_set": "spg",
      "scryfall_collector_number": "16",
      "name": "Thrasios, Triton Hero",
      "lowercase_name": "thrasios, tyson hero",
      "mana_cost": "{R}{W}",
      "cmc": 3,
      "color_identity": ["W", "R"],
      "color_identity_count": 2,
      "type_line": "Legendary Creature — Kor Soldier Ally",
      "power": "1",
      "toughness": "1",
      "keywords": ["ally", "first strike"],
      "keyword_count": 2,
      "oracle_text_preview": "First strike, vigilance...",
      "edhrec_rank": null,
      "scryfall_uri": "https://scryfall.com/card/spg/16/thrasios-triton-hero",
      "status": "ok"
    },
    {
      "card": "Sol Ring",
      "scryfall_set": "spg",
      "scryfall_collector_number": "241",
      "name": "Sol Ring",
      "lowercase_name": "sol ring",
      "mana_cost": "{R}{W}",
      "cmc": 2,
      "color_identity": ["W", "R"],
      "color_identity_count": 2,
      "type_line": "Artifact — Spell",
      "power": null,
      "toughness": null,
      "keywords": ["land"],
      "keyword_count": 1,
      "oracle_text_preview": "Obtain a land card from your graveyard...",
      "edhrec_rank": null,
      "scryfall_uri": "https://scryfall.com/card/spg/241/sol-ring",
      "status": "ok"
    }
  ]
}
```

### 2.3 Report section mapping

| Report section | Source output key | Status |
|---|---|---|
| **Card facts** (name, mana cost, CMC, type line, power/toughness) | `card_info[]` | AVAILABLE |
| **Oracle text** (rules text) | `card_info[].oracle_text_preview` | AVAILABLE |
| **Keywords** | `card_info[].keywords` | AVAILABLE |
| **EDHREC rank** | `card_info[].edhrec_rank` | AVAILABLE |
| **Color identity** | `card_info[].color_identity` | AVAILABLE |
| **Scryfall URI** | `card_info[].scryfall_uri` | AVAILABLE (reference link) |

### 2.4 Caveats to state

The report must state all of the following:

1. **`oracle_text_preview` is a preview.** It is a truncated excerpt of the full Oracle text, not the complete rules text. The full text is available via the Scryfall API (rate-limited); during the audit, only the preview is available.
2. **Keywords are derived from `cards.json`.** The list is accurate for standard keywords (e.g., "first strike", "trample") but may miss edge cases or multi-word keywords with special parsing.
3. **EDHREC rank is community data.** EDHREC rank is from the EDHREC community, not Scryfall or authoritative sources. It reflects popularity, not quality.
4. **Card info is the card's structural facts.** It describes what the card is (mana, type, keywords), not what it does (that comes from the Tagger's card tags and the oracle text).

---

## 3. Integration with Tagger

The Scryfall adapter and the Tagger adapter are independent but complementary. The package combines both into a single `card_profile` per card.

```json
"card_profile": {
  "card": "Thrasios, Triton Hero",
  "scryfall": {
    "mana_cost": "{R}{W}",
    "cmc": 3,
    "type_line": "Legendary Creature — Kor Soldier Ally",
    "keywords": ["ally", "first strike"],
    "oracle_text_preview": "First strike, vigilance. Partner...",
    "edhrec_rank": null,
    "scryfall_uri": "https://scryfall.com/card/spg/16/thrasios-triton-hero"
  },
  "tagger": {
    "card_tags": ["alt-commander", "pair-commander", "draw engine", "impulse-onto-battlefield", "repeatable scry", ...],
    "inherited_card_tags": ["artifact count matters", "cycle", "synergy-artifact"],
    "artwork_tags": []  // filtered out
  },
  "combined": {
    "what_it_is": "Legendary Creature — Kor Soldier Ally, 3 CMC, white/red (R/W)",
    "what_it_does": "Draws a card, changes name, gains power based on artifact count, and is a cycle partner",
    "role": "cycle spouse / draw engine / synergy piece"
  }
}
```

| Source | Data | Package use |
|---|---|---|
| **Tagger** | `card_tags`, `inherited_card_tags` | What the card does (behavioural), where it helps |
| **Scryfall** | `card_info` (oracle text, mana, type, power, EDHREC) | What the card is (structural), rules text context |
| **Both** | Combined | Full card profile for role classification, combos, and comparison |

---

## 4. Open questions (resolved)

### 4.1 Tag count / game length — NOT AVAILABLE, skip

**Decision:** Mark as `NOT AVAILABLE` and skip. No source in the frozen snapshot provides turn count or game length. The Tagger and Scryfall provide card tags and card info, not game data.

### 4.2 CEDHStats integration — player rankings, separate module, PARTIAL

**What stats:** Use CEDHStats **player rankings** (entries, PPG, top cut %, floor, veterans, ceiling) — NOT tournament win rates.

**How fetched & cached:** Fetch via `cedhstats.org/players` API, cache to `cedhstats/player_rankings.json`. No live calls during the audit.

**Where it plugs in:** Separate module, context layer only.

### 4.3 Scryfall integration — primary source, locked down

**What info is used:** Scryfall API is the single authoritative source for every card field. The local `cards.json` is an optional cache (pre-fetched from bulk API) for audit speed. The adapter does NOT depend on `cards.json`.

**Fallback chain (locked down):**
1. Local cache check — `cards.json` (33,777 cards, pre-fetched from bulk API)
2. Scryfall API — fetch any card not in the cache (canonical source, every field available)
3. Skip — card not found in either source; return `PARTIAL`

**Commanders legality:** `cards.json` has `edhrec_rank` but not Commander legality. Mark as `PARTIAL`.

### 4.4 Tagger tag resolution — how tags are fetched per card

**Lookup path:** For each card, resolve to Scryfall canonical form (set code + collector number), then query the Tagger.

**Fallback chain:**
1. `cards.json` (optional local cache — fast lookup, pre-fetched from bulk API)
2. Scryfall API (`/cards/:name`) — fall back if the card is not in the cache, may 400 for some queries
3. No tags — `tags_missing` increments, entry still returned

**Tag extraction:** Card tags are those under the `#card/` namespace (mechanical/behavioural); artwork tags under `#artwork/` are filtered out; inherited card tags are included (from the `Inherits` section).

### 4.5 Tag quality & reliability

**User-submitted vs authoritative:** Tags are community-submitted. The adapter notes this in the report. Tags are supplementary, not authoritative.

**Missing tags:** Cards with no tagger entry return `tags_missing > 0`. The adapter returns them anyway (with empty tags) rather than failing.

---

## 5. Decision priorities

Ranked 1 = do first. Balances value to the audit against feasibility.

| Rank | Component | Status | Rationale |
|---|---|---|---|
|| 1 | **Card info retrieval** (oracle text, mana, type, keywords) | AVAILABLE (API) | Core deliverable — gives the card's rules text and structure. Full card info via Scryfall API; locked down, no cards.json dependency. |
|| 2 | **Tag integration** (Combining Scryfall info + Tagger tags) | PARTIAL | The package combines both; requires the tagger adapter to ship first. |
|| 3 | **Oracle text extraction** (full text, not preview) | AVAILABLE (with Scryfall API) | Needs live API; preview available locally. |
|| 4 | **EDHREC rank integration** | AVAILABLE | Low effort, from Scryfall API. |
|| 5 | **Mana analysis** (using Scryfall info) | AVAILABLE | Already supported by the combined data. |

---

## 6. Implementation note

### Files to create

| File | Purpose |
|---|---|
| `NEBULA-SCRYFALL.md` | **This document** — the Scryfall adapter blueprint. |
| `archetype/scryfall.py` | New module: `num_adapter(mode="scryfall", decklist, options)` — resolves card names, fetches card info from the Scryfall API (with `cards.json` as optional local cache). |

### Fallback chain (locked down)

1. **Local cache check** — `cards.json` (33,777 cards, pre-fetched from bulk API) — use if present
2. **Scryfall API** — fetch any card not in the cache (canonical source, every field available)
3. **Skip** — card not found in either source; return `PARTIAL`

### Files to modify

| File | Change |
|---|---|
| `NEBULA-DESIGN-PLAN.md` | Add `archetype.scryfall` to the capability inventory. |
| `NEBULA-FREQUENCY-POOL.md` | Add `archetype.scryfall` + `archetype.tagger` as supporting capabilities. |
| `NEBULA-META-COMPARE.md` | Add Scryfall section to report. |

### Constraints

- **No live API calls during the audit.** The adapter uses the local cache (`cards.json`) or pre-fetched data. The adapter can be tested with the live API in a separate pass.
- `num_adapter` is the single data-fetching layer; the LLM never reads files directly.
- `cedh_eligibility = CANDIDATE_UNCONFIRMED` is cited in the report.
- Design philosophy: modular; failures return `AVAILABLE` / `PARTIAL` / `UNSUPPORTED`.
- **Lock-down:** The adapter does NOT depend on `cards.json`. The local file is an optional cache (pre-fetched from bulk API). The Scryfall API is the single authoritative source for every card field. If `cards.json` is missing or stale, the adapter falls back to the API. The adapter must never hard-fail because `cards.json` is absent.

---

## 7. Reference — Thrasios, Triton Hero (spg #16) card info

The following is the exact card info the adapter would return for Thrasios, Triton Hero, as a concrete example:

- **Name:** Thrasios, Triton Hero
- **Set:** SPG (Ixalan)
- **Mana cost:** `{R}{W}`
- **CMC:** 3
- **Color identity:** W, R (2 pips)
- **Type line:** Legendary Creature — Kor Soldier Ally
- **Power/Toughness:** 1/1
- **Keywords:** ally, first strike
- **Oracle text preview:** "First strike, vigilance, and an ability that lets you change your... [full text available via Scryfall]"
- **EDHREC rank:** null (low rank in the format)
- **Scryfall URI:** `https://scryfall.com/card/spg/16/thrasios-triton-hero`
- **Card tags (from Tagger, PZ2 #48):** `alt-commander`, `cranial plating`, `cycle-c16-r-partner`, `pair-commander`, `unique type line`
- **Inherited card tags:** `artifact count matters`, `cycle`, `synergy-artifact`

---

*This completes the Scryfall adapter design. It provides the card info (rules text, mana, type) that complements the Tagger's card tags. Together, they give the full picture of what each card in the deck is and what it does.*
