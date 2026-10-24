# NEBULA — LEARNCEDH ADAPTER

**Capability ID:** `archetype.learncedh`
**Owner:** Codie (measurement) + Jin (interpretation)
**Date:** 2026-10-24
**Status:** DESIGN REFERENCE — not implemented

---

## 1. Package contents

The LearnCEDH adapter provides deck summaries and performance metrics from
the LearnCEDH community database. It complements the TopDeck adapter by
providing:

- **Deck summaries** — narrative description, strategy/gameplan, synergies, combos
- **Performance metrics** — conversion rate, meta share, 95% range, entrants, events, pilots
- **Deck classification** — turbo/stax/control/storm identification (complements `archetype.classify`)

### Data sources

| Source | Role | Notes |
|---|---|---|
| `learncedh.com` | Primary (read-only) | Deck summaries, strategy, synergies, combos, performance metrics |
| `cedhstats.org` | Complementary | Tournament results, player rankings (separate module) |
| `cards.json` | Local cache | Card facts (mana, type, color) |
| `tagger.scryfall.com` | Separate adapter | Card tags (mechanical/behavioural) |
| Scryfall API | Fallback for card info | Full oracle text, keywords, legalities |

### Key fields

| Field | Source | Notes |
|---|---|---|
| `deck_name` | LearnCEDH | Deck name (e.g., "Tymna Thrasios") |
| `commanders` | LearnCEDH | Card names (from deck list) |
| `summary` | LearnCEDH | Short summary description |
| `strategy` | LearnCEDH | Strategy / gameplan text |
| `synergies` | LearnCEDH | Key synergies (card names + description) |
| `combos` | LearnCEDH | Defined combos (card pairs + steps) |
| `conversion_rate` | LearnCEDH | Deck's conversion rate (as % of field) |
| `meta_share` | LearnCEDH | Deck's meta share (as % of field) |
| `range_95` | LearnCEDH | 95% range of performance |
| `entrants` | LearnCEDH | Number of entrants |
| `events` | LearnCEDH | Number of events |
| `pilots` | LearnCEDH | Number of pilots |
| `timeframe` | LearnCEDH | Reporting period |
| `archetype` | Derived | turbo/stax/control/storm (from classification) |
| `card_tags` | Tagger | Card tags (mechanical/behavioural) |
| `card_info` | Scryfall | Card info (mana, type, keywords, oracle text) |

---

## 2. Delivery packet schema

### 2.1 Input schema

```json
{
  "adapter": "num_adapter",
  "mode": "learncedh",
  "deck_name": "Tymna Thrasios",
  "metadata": {
    "deck_name": "Tymna Thrasios",
    "format": "commander",
    "audit_date": "2026-10-24"
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `deck_name` | string | yes | Deck name (or commander name) to look up |
| `metadata.format` | string | yes | e.g., "commander", "edh" |
| `metadata.audit_date` | string | yes | Audit date for context |

### 2.2 Output schema

```json
{
  "adapter": "num_adapter",
  "mode": "learncedh",
  "status": "AVAILABLE",
  "deck": {
    "deck_name": "Tymna Thrasios",
    "commanders": ["Tymna the Weaver", "Thrasios, Triton Hero"],
    "summary": "A flexible and resilient midrange deck blending card draw, ramp, and combo potential...",
    "strategy": "The deck's game plan revolves around leveraging Tymna the Weaver's card draw...",
    "synergies": [
      {
        "card": "Seedborn Muse",
        "description": "Provides unparalleled synergy with Thrasios, Triton Hero..."
      },
      {
        "card": "Culling Ritual",
        "description": "A powerful board wipe and ramp spell, Culling Ritual clears..."
      }
    ],
    "combos": [
      {
        "cards": ["Devoted Druid", "Swift Reconfiguration"],
        "description": "Enchant Devoted Druid with Swift Reconfiguration, turning it into a vehicle...",
        "steps": 5
      }
    ],
    "performance": {
      "conversion_rate": 25.2,
      "meta_share": 1.5,
      "range_95": [97, 128],
      "entrants": 498,
      "events": 236,
      "pilots": 309,
      "timeframe": "180 days through 2026-10-16"
    }
  },
  "archetype": "control",
  "caveats": [
    "Data sourced from LearnCEDH community database (not official tournament records)",
    "Performance metrics are relative to the LearnCEDH player base, not global cEDH"
  ]
}
```

### 2.3 Report section mapping

| Report section | Source output key | Status |
|---|---|---|
| **Deck summary** | `deck.summary` | AVAILABLE |
| **Strategy / gameplan** | `deck.strategy` | AVAILABLE |
| **Synergies** | `deck.synergies[]` | AVAILABLE |
| **Combos** | `deck.combos[]` | AVAILABLE |
| **Performance metrics** | `deck.performance` | AVAILABLE |
| **Archetype classification** | `archetype` | PROPOSED (from `archetype.classify`) |
| **Card tags** | `tagger` | AVAILABLE (from `archetype.tagger`) |
| **Card info** | `scryfall` | AVAILABLE (from `archetype.scryfall`) |

### 2.4 Caveats to state

The report must state:

1. **Data source:** LearnCEDH is a community database, not an official tournament source. Data may be incomplete or inaccurate.
2. **Performance metrics:** Conversion rate, meta share, and 95% range are relative to the LearnCEDH player base (180 days through `2026-10-16` per the example). Not comparable to global cEDH statistics.
3. **Strategy text is community-written:** Summaries, strategies, and combos are community contributions, not official source.

---

## 3. Integration with other components

| Source | Data | Package use |
|---|---|---|
| **LearnCEDH** | Deck summaries, strategy, synergies, combos | What the deck is (narrative) |
| **Tagger** | Card tags | What the cards do (behavioural) |
| **Scryfall** | Card info (mana, type, keywords) | What the cards are (structural) |
| **Archetype classify** | turbo/stax/control/storm | Classification of the deck |
| **TopDeck** | Performance metrics | Meta comparison context |

The LearnCEDH adapter provides the **narrative and classification** context for a deck, complementing the **structural and statistical** context from the other adapters.

---

## 4. Open questions (resolved)

### 4.1 Deck identification

**Decision:** Deck identification uses the `deck_name` parameter. If the deck is a two-commander deck, the adapter looks up the deck by name or searches by commander.

### 4.2 Performance metrics availability

**Decision:** Performance metrics are optional. If the deck is not found on LearnCEDH, the adapter returns `PARTIAL` with the `deck` object containing only the summary fields.

### 4.3 Data freshness

**Decision:** LearnCEDH data is a live snapshot. The adapter notes the `timeframe` field in the output. The adapter can cache results locally (to a `learncedh/cached_decks.json` file) for audit speed.

---

## 5. Decision priorities

| Rank | Component | Status | Rationale |
|---|---|---|---|
| 1 | **Deck summary** | AVAILABLE | Core deliverable — gives the deck's narrative |
| 2 | **Strategy / gameplan** | AVAILABLE | Useful for interpretation |
| 3 | **Synergies** | AVAILABLE | Card-specific context |
| 4 | **Combos** | AVAILABLE | Gameplan detail |
| 5 | **Performance metrics** | AVAILABLE | Contextual data |
| 6 | **Archetype classification** | PROPOSED | Complement to `archetype.classify` |
| 7 | **Card tags** | AVAILABLE | From `archetype.tagger` |
| 8 | **Card info** | AVAILABLE | From `archetype.scryfall` |

---

## 6. Implementation note

### Files to create

| File | Purpose |
|---|---|
| `NEBULA-LEARNCEDH.md` | **This document** — the LearnCEDH adapter blueprint. |
| `archetype/learncedh.py` | New module: `num_adapter(mode="learncedh", deck_name, options)` — fetches deck summaries from LearnCEDH. |

### Files to modify

| File | Change |
|---|---|
| `NEBULA-DESIGN-PLAN.md` | Add `archetype.learncedh` to capability inventory. |
| `NEBULA-FREQUENCY-POOL.md` | Add LearnCEDH summary section. |

### Constraints

- Read-only access to LearnCEDH (no data submission)
- Caching allowed locally for audit speed
- No live API calls during the audit — use cached data

---

## 7. Reference — Tymna Thrasios (LearnCEDH example)

The following is the deck summary the adapter would return for Tymna Thrasios, based on the LearnCEDH page.

### Deck summary

> **Tymna Thrasios** — A flexible and resilient midrange deck that blends card draw, ramp, and combo potential to dominate cEDH pods. The deck excels in resource generation and adaptability, allowing it to pivot between control, stax, and explosive combo strategies depending on the game state.

### Strategy / gameplan

> The deck's game plan revolves around leveraging Tymna the Weaver's card draw and Thrasios, Triton Hero's mana sink to develop resources and control the game. Early game efforts focus on efficient ramp and establishing card advantage while deploying stax pieces or interaction to disrupt opponents.

As the game progresses, the deck transitions into assembling infinite mana combos or other synergistic lines to secure victory. By adapting to the pod's dynamics, Tymna the Weaver and Thrasios, Triton Hero can execute versatile strategies, ranging from stalling opponents to creating explosive game-ending plays.

### Synergies

| Card | Description |
|---|---|
| Seedborn Muse | Provides unparalleled synergy with Thrasios, Triton Hero, enabling repeated activations during opponents' turns. This generates massive card advantage and mana, allowing the deck to outpace its opponents in resource accumulation. |
| Culling Ritual | A powerful board wipe and ramp spell, Culling Ritual clears stax pieces, mana rocks, and small creatures while generating a significant burst of mana to transition into a winning turn. |

### Combos

| Cards | Steps | Description |
|---|---|---|
| Devoted Druid + Swift Reconfiguration | 5 | Enchant Devoted Druid with Swift Reconfiguration, turning it into a vehicle. Tap Devoted Druid for green mana. Activate Devoted Druid's untap ability by placing a -1/-1 counter on it. Repeat the process for infinite green mana. Use Thrasios, Triton Hero or other outlets to convert the mana into a win condition. |
| Hazel's Brewmaster + Devoted Druid | 5 | Activate Devoted Druid's second ability twice to kill it and put it in your graveyard. Cast Hazel's Brewmaster and target Devoted Druid with the enter the battlefield ability. Create a food token with Devoted Druid's activated abilities. Tap and untap the food token with Devoted Druid's abilities repeatedly, generating infinite green mana. Funnel the mana into Thrasios, Triton Hero or other win conditions. |
| Demonic Consultation or Tainted Pact + Thassa's Oracle | 3 | Cast Thassa's Oracle. While the trigger is on the stack, cast Demonic Consultation or Tainted Pact to exile your library. Resolve Thassa's Oracle's ability to win the game. |

### Performance metrics

| Metric | Value |
|---|---|
| Conversion rate | 25.2% |
| Meta share | 1.5% |
| 95% range | 97 to 128 |
| Entrants | 498 |
| Events | 236 |
| Pilots | 309 |
| Timeframe | 180 days through 2026-10-16 |

### Archetype classification (from `archetype.classify`)

- **Band:** `control` (midrange/resilient but with combo potential)
- **Rationale:** The deck balances card advantage, interaction, and efficient combos for adaptable and resilient gameplay. It can pivot between control, stax, and explosive combo strategies.

---

*This completes the LearnCEDH adapter design. It provides deck summaries, strategy, synergies, combos, and performance metrics from LearnCEDH, complementing the structural and statistical context from Scryfall, Tagger, and TopDeck adapters.*
