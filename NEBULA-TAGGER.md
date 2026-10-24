# NEBULA — TAGGER ADAPTER

**Capability ID:** `archetype.tagger`
**Owner:** Codie (measurement) + Jin (interpretation)
**Date:** 2026-10-24
**Status:** DESIGN REFERENCE — not implemented

---

## 1. Package contents

The Tagger adapter pulls **card tags** from Tagger (https://tagger.scryfall.com/).
These tags are the **behavioural/structural fingerprint** of a card — what it
does, how it's played, and where it helps.

### Data source

| Source | Role | Notes |
|---|---|---|
| `tagger.scryfall.com` | Primary | Card tags (card tags, inherited tags, artwork tags) |
| `cards.json` | Local cache | Card facts (optional) |
| Scryfall API | Fallback for card info | Full oracle text, keywords, legalities |

### What Tagger provides

| Tag type | Included? | Description |
|---|---|---|
| **Card tags** | ✅ Yes | Mechanical/behavioural: `ramp`, `draw engine`, `mana sink`, `discard`, etc. |
| **Inherited card tags** | ✅ Yes | Tags inherited from related cards (e.g., `cycle`, `artifact count matters`) |
| **Artwork tags** | ❌ No | Visual only (`digital painting`, `human`, `merfolk`) — filtered out |

### Tag filtering

| Filter | Applied? | Description |
|---|---|---|
| Artwork tags | Removed | Visual only — never sent to the package |
| Card tags | Included | Mechanical/behavioural — always included |
| Inherited card tags | Included | Inherited tags from related cards — always included |

---

## 2. Delivery packet schema

### 2.1 Input schema

```json
{
  "adapter": "num_adapter",
  "mode": "tagger",
  "card_name": "Thrasios, Triton Hero",
  "metadata": {
    "deck_name": "Tymna Thrasios",
    "format": "commander",
    "audit_date": "2026-10-24"
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `card_name` | string | yes | Card name to look up tags for |
| `metadata.deck_name` | string | no | Deck name (for context) |
| `metadata.format` | string | no | e.g., "commander", "edh" |

### 2.2 Output schema

```json
{
  "adapter": "num_adapter",
  "mode": "tagger",
  "status": "AVAILABLE",
  "card": {
    "name": "Thrasios, Triton Hero",
    "card_tags": [
      "activated ability", "alliteration", "alt-commander",
      "bottomless mana sink", "cycle-c16-r-partner",
      "draw engine", "impulse-onto-battlefield",
      "land or hand", "land ramp", "pair-commander",
      "repeatable card advantage", "repeatable draw",
      "scry", "sneak from library", "top deck manipulation"
    ],
    "inherited_card_tags": [
      "activated ability", "alliteration", "alt-commander",
      "cycle-c16-r-partner", "pair-commander",
      "repeatable card advantage", "repeatable draw",
      "scry", "sneak from library", "top deck manipulation"
    ],
    "artwork_tags": [ /* excluded */ ],
    "tag_summary": {
      "card_tags": 14,
      "inherited_card_tags": 10,
      "artwork_tags_excluded": 13
    },
    "tag_frequency": {
      "ramp": 2,
      "draw": 2,
      "mana sink": 1,
      "card advantage": 2,
      "library manipulation": 1
    }
  },
  "caveats": [
    "Tags are community-submitted on Tagger (not official)",
    "Some cards may have missing or incomplete tags",
    "Artwork tags are excluded from the package"
  ]
}
```

### 2.3 Report section mapping

| Report section | Source output key | Status |
|---|---|---|
| **Card tags** | `card.card_tags` | AVAILABLE |
| **Inherited tags** | `card.inherited_card_tags` | AVAILABLE |
| **Tag summary** | `card.tag_summary` | AVAILABLE |
| **Tag frequency** | `card.tag_frequency` | AVAILABLE |
| **Artwork tags** | `card.artwork_tags` (excluded) | FILTERED OUT |

### 2.4 Caveats to state

The report must state:

1. **Data source:** Tags from Tagger are community-submitted, not official.
2. **Tag quality:** Some cards may have incomplete or sparse tags.
3. **Artwork tags filtered:** Visual tags (artwork) are always excluded from the package.

---

## 3. Integration with other components

| Source | Data | Package use |
|---|---|---|
| **Tagger** | Card tags, inherited tags | What the cards do (behavioural) — **key input** |
| **Hypercalculator** | Tag-based probability | Chances of drawing cards with specific tags |
| **Archetype classify** | Tag-based classification | Not used (user decision) |

### How Tagger feeds other components

1. **Hypercalculator:** Uses `tag_frequency` to group cards by tag and compute
   probability of drawing at least one card with a specific tag.
2. **Report:** The `card_tags` and `tag_frequency` appear in the report's
   card-level analysis sections, giving the user a behavioural fingerprint
   of each card.

---

## 4. Open questions (resolved)

### 4.1 Card identification

**Decision:** Card lookup uses the `card_name` parameter. The adapter queries
Tagger by card name (`https://tagger.scryfall.com/card/<set>/<num>`) or searches
by name if the exact card is not found.

### 4.2 Tag extraction

**Decision:** Extract all three tag types from the Tagger page:
- Card tags (mechanical/behavioural)
- Inherited card tags
- Artwork tags (filtered out)

### 4.3 Data freshness

**Decision:** Tag data is a live snapshot from Tagger. The adapter can cache
results locally (to a `tagger/cached_tags.json` file) for audit speed. Tags
are community-submitted and may change.

---

## 5. Implementation note

### Files to create

| File | Purpose |
|---|---|
| `NEBULA-TAGGER.md` | **This document** — the Tagger adapter blueprint. |
| `archetype/tagger.py` | New module: `num_adapter(mode="tagger", card_name, options)` — fetches card tags from Tagger. |

### Library dependencies

| Dependency | Purpose |
|---|---|
| `requests` | Fetch Tagger pages |
| `bs4` (BeautifulSoup) | Parse Tagger HTML |
| `re` | Extract tag names from HTML |

### Data sources

| Source | Role | Notes |
|---|---|---|
| `tagger.scryfall.com/card/<set>/<num>` | Primary | Card tags page |
| `tagger.scryfall.com/tags/card/<tag>` | Tag reference | Tag definitions |
| `cards.json` | Local cache | Card facts (optional) |

### Constraints

- Read-only access to Tagger (no data submission)
- Caching allowed locally for audit speed
- Artwork tags always filtered out
- No live API calls during the audit — use cached data for testing

---

## 6. Reference — Tymna Thrasios, Triton Hero (example)

### Test case

Card: `Thrasios, Triton Hero` (SPG #16)

### Expected output

| Field | Value |
|---|---|
| `card_tags` | 14 tags — `activated ability`, `alliteration`, `alt-commander`, `bottomless mana sink`, `cycle-c16-r-partner`, `draw engine`, `impulse-onto-battlefield`, `land or hand`, `land ramp`, `pair-commander`, `repeatable card advantage`, `repeatable draw`, `scry`, `sneak from library`, `top deck manipulation` |
| `inherited_card_tags` | ~10 tags — `activated ability`, `alliteration`, `alt-commander`, `cycle-c16-r-partner`, `pair-commander`, `repeatable card advantage`, `repeatable draw`, `scry`, `sneak from library`, `top deck manipulation` |
| `artwork_tags` | 13 tags (excluded) — `digital painting`, `fin hair`, `flying fish`, `ixalan (plane)`, `muscular`, `not canon`, `pecs`, `right-facing`, `tentacle`, `thrasios`, `topless`, `trident`, `water`, `wave` |
| `tag_summary` | `{card_tags: 14, inherited_card_tags: 10, artwork_tags_excluded: 13}` |
| `tag_frequency` | `{ramp: 2, draw: 2, mana sink: 1, card advantage: 2, library manipulation: 1, ...}` |

### How this is used

1. **Hypercalculator:** Groups cards by tag and computes probability of drawing
   at least one card with each tag (e.g., "47% chance of drawing ≥1 ramp card").
2. **Report:** The card's tags appear in the card-by-card analysis, giving the
   user a behavioural fingerprint.

---

*This completes the Tagger adapter design. It provides card tags (mechanical/behavioural, filtered for artwork), complementing the structural data from Scryfall and the probability metrics from the Hypercalculator.*
