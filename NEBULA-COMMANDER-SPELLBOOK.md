# NEBULA — COMMANDER SPELLBOOK ADAPTER

**Capability ID:** `archetype.commander_spellbook`
**Owner:** Codie (measurement) + Jin (interpretation)
**Date:** 2026-10-24
**Status:** DESIGN REFERENCE — not implemented

---

## 1. Package contents

The Commander Spellbook adapter provides combo data from the Commander Spellbook
community database via the **REST API**. It complements the LearnCEDH adapter
by providing:

- **Combo data** — cards that combo together (community-verified)
- **Combo details** — steps, requirements, and resolution order
- **Combo popularity** — rank, votes, and salt ratings
- **Combo validation** — verified community data, not theoretical

### Data sources

| Source | Role | Notes |
|---|---|---|
| `https://backend.commanderspellbook.com/` | **Primary** | REST API endpoints |
| `commanderspellbook.com` | Frontend | User-facing site (uses REST API) |
| `cards.json` | Local cache | Card facts (mana, type, color) |
| `tagger.scryfall.com` | Separate adapter | Card tags (mechanical/behavioural) |
| Scryfall API | Fallback for card info | Full oracle text, keywords, legalities |

### REST API endpoints

| Endpoint | Purpose |
|---|---|
| `https://backend.commanderspellbook.com/cards` | Card database (lookup card details) |
| `https://backend.commanderspellbook.com/find-my-combos` | Search combos involving specific cards |
| `https://backend.commanderspellbook.com/explain-query` | Explain/validate a combo query |
| `https://backend.commanderspellbook.com/card-list-from-url` | Parse card list from decklist URL |
| `https://backend.commanderspellbook.com/card-list-from-text` | Parse card list from text |
| `https://backend.commanderspellbook.com/estimate-bracket` | Estimate bracket power level |

### Key fields

| Field | Source | Notes |
|---|---|---|
| `deck_name` | LearnCEDH | Deck name (for lookup) |
| `commanders` | LearnCEDH | Card names (from deck list) |
| `combos` | Commander Spellbook (REST API) | Combo data (cards, steps, rank, votes, salt) |
| `combo_details` | Commander Spellbook | Full description, requirements, resolution |
| `combo_rank` | Commander Spellbook | Rank by popularity |
| `combo_votes` | Commander Spellbook | Vote count |
| `combo_salt` | Commander Spellbook | Salt rating |
| `card_tags` | Tagger | Card tags (mechanical/behavioural) |
| `card_info` | Scryfall | Card info (mana, type, keywords, oracle text) |

---

## 2. Delivery packet schema

### 2.1 Input schema

```json
{
  "adapter": "num_adapter",
  "mode": "commander_spellbook",
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
  "mode": "commander_spellbook",
  "status": "AVAILABLE",
  "deck": {
    "deck_name": "Tymna Thrasios",
    "commanders": ["Tymna the Weaver", "Thrasios, Triton Hero"],
    "combos": [
      {
        "cards": ["Tymna the Weaver", "Thrasios, Triton Hero"],
        "description": "Seedborn Muse provides unparalleled synergy with Thrasios, Triton Hero...",
        "steps": 3,
        "rank": 5,
        "votes": 124,
        "salt": 3
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
  "caveats": [
    "Data sourced from Commander Spellbook community (not official tournament records)",
    "Combos are community-submitted and may vary in quality"
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

1. **Data source:** Commander Spellbook is a community database, not an
   official tournament source. Data may be incomplete or inaccurate.
2. **Combo quality:** Combos are community-submitted and may vary in quality.
   Some may be theoretical or unplayable in competitive formats.
3. **Salt rating is subjective:** Salt ratings are community opinions, not
   objective quality measures.

---

## 3. Integration with other components

| Source | Data | Package use |
|---|---|---|
| **LearnCEDH** | Deck summaries, performance metrics | What the deck is (narrative) |
| **Commander Spellbook** | Combo data (cards, steps, rank, votes, salt) | What the deck can do (gameplan) |
| **Tagger** | Card tags | What the cards do (behavioural) |
| **Scryfall** | Card info (mana, type, keywords) | What the cards are (structural) |
| **Archetype classify** | turbo/stax/control/storm | Classification of the deck |

The Commander Spellbook adapter provides the **gameplan and combo data** for a
deck, complementing the **narrative and structural** context from LearnCEDH
and the other adapters.

---

## 4. Open questions (resolved)

### 4.1 Deck identification

**Decision:** Deck identification uses the `deck_name` parameter. If the deck
is a two-commander deck, the adapter looks up the deck by name or searches by
commander.

### 4.2 Combo search

**Decision:** Use the Commander Spellbook REST API (`find-my-combos` endpoint)
to find combos involving the deck's cards. The API returns combos sorted by
popularity.

### 4.3 Data freshness

**Decision:** Commander Spellbook data is a live snapshot. The adapter notes
the `timeframe` field in the output. The adapter can cache results locally
(to a `commanderspellbook/cached_combos.json` file) for audit speed.

---

## 5. Decision priorities

| Rank | Component | Status | Rationale |
|---|---|---|---|
| 1 | **Combo data** | AVAILABLE | Core deliverable — gives the deck's gameplan |
| 2 | **Combo details** | AVAILABLE | Steps, requirements, resolution |
| 3 | **Combo rank / votes** | AVAILABLE | Validates combo quality |
| 4 | **Combo salt** | AVAILABLE | Community opinion, useful context |
| 5 | **Deck summary** | AVAILABLE | From LearnCEDH adapter |
| 6 | **Card tags** | AVAILABLE | From `archetype.tagger` |
| 7 | **Card info** | AVAILABLE | From `archetype.scryfall` |

---

## 6. Implementation note

### Files to create

| File | Purpose |
|---|---|
| `NEBULA-COMMANDER-SPELLBOOK.md` | **This document** — the Commander Spellbook adapter blueprint. |
| `archetype/commander_spellbook.py` | New module: `num_adapter(mode="commander_spellbook", deck_name, options)` — fetches combo data from Commander Spellbook REST API. |

### Implementation approach

The Commander Spellbook REST API provides direct JSON endpoints. The adapter
will:

1. **Query the `find-my-combos` endpoint** — request combos involving the deck's
   card names:
   ```
   GET https://backend.commanderspellbook.com/find-my-combos?q=<card1>+<card2>+...
   ```
2. **Parse the JSON response** — extract combo data:
   - Combo cards
   - Combo description/steps
   - Rank, votes, salt ratings
3. **Return the data** — structure it as `combo` objects in the output schema.

### Library dependencies

| Dependency | Purpose |
|---|---|
| `requests` | HTTP requests to REST API |
| `json` | Parse JSON responses |

### Constraints

- Read-only access to Commander Spellbook REST API (no data submission)
- Caching allowed locally for audit speed
- No live API calls during the audit — use cached data for testing

---

## 7. Reference — Tymna Thrasios (LearnCEDH example)

The following is the deck summary the adapter would return for Tymna Thrasios, based on the LearnCEDH page.

### Deck summary

> **Tymna Thrasios** — A flexible and resilient midrange deck that blends card draw, ramp, and combo potential to dominate cEDH pods. The deck excels in resource generation and adaptability, allowing it to pivot between control, stax, and explosive combo strategies depending on the game state.

### Strategy / gameplan

> The deck's game plan revolves around leveraging Tymna the Weaver's card draw and Thrasios, Triton Hero's mana sink to develop resources and control the game. Early game efforts focus on efficient ramp and establishing card advantage while deploying stax pieces or interaction to disrupt opponents.

### Synergies

| Card | Synergy |
|---|---|
| Seedborn Muse | Unparalleled synergy with Thrasios, Triton Hero — repeated activations, massive card advantage and mana |
| Culling Ritual | Board wipe and ramp spell — clears stax pieces, mana rocks, and small creatures while generating mana to transition into a winning turn |

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

### Commander Spellbook combo data (expected)

The Commander Spellbook REST API will search for combos involving the deck's cards:

- **Search query:** `thrasios tymna` (or `thrasios tymna weaver`)
- **Expected results:** Combos involving Thrasios, Triton Hero and/or Tymna the Weaver, including:
  - Thrasios + Witch Card (or similar) — instant draw
  - Thrasios + Jace, Counter-Trait Master — exile + reanimate
  - Tymna the Weaver + Sol Ring / Ancestral Recall — card advantage
  - Tymna the Weaver + Tormod's Crypt — card disadvantage
  - Thrasios + Seedborn Muse — card advantage loop
  - Thrasios + Culling Ritual — board wipe and mana burst

### Notes

- **Combination data** is community-submitted and may vary in quality
- **Salt ratings** are community opinions, not objective quality measures
- **Popularity** is tracked by votes and rank; highly voted combos are more reliable

---

*This completes the Commander Spellbook adapter design. It provides combo data, gameplan details, and performance metrics from Commander Spellbook, complementing the structural and statistical context from Scryfall, Tagger, and LearnCEDH adapters.*


## 7. Reference — Tymna Thrasios (LearnCEDH example)

The following is the deck summary the adapter would return for Tymna Thrasios, based on the LearnCEDH page.

### Deck summary

> **Tymna Thrasios** — A flexible and resilient midrange deck that blends card draw, ramp, and combo potential to dominate cEDH pods. The deck excels in resource generation and adaptability, allowing it to pivot between control, stax, and explosive combo strategies depending on the game state.

### Strategy / gameplan

> The deck's game plan revolves around leveraging Tymna the Weaver's card draw and Thrasios, Triton Hero's mana sink to develop resources and control the game. Early game efforts focus on efficient ramp and establishing card advantage while deploying stax pieces or interaction to disrupt opponents.

### Synergies

| Card | Synergy |
|---|---|
| Seedborn Muse | Unparalleled synergy with Thrasios, Triton Hero — repeated activations, massive card advantage and mana |
| Culling Ritual | Board wipe and ramp spell — clears stax pieces, mana rocks, and small creatures while generating mana to transition into a winning turn |

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

### Commander Spellbook combo data (expected)

The Commander Spellbook adapter will search for combos involving the deck's cards:

- **Search query:** `thrasios tymna` (or `thrasios tymna weaver`)
- **Expected results:** Combos involving Thrasios, Triton Hero and/or Tymna the Weaver, including:
  - Thrasios + Witch Card (or similar) — instant draw
  - Thrasios + Jace, Counter-Trait Master — exile + reanimate
  - Tymna the Weaver + Sol Ring / Ancestral Recall — card advantage
  - Tymna the Weaver + Tormod's Crypt — card disadvantage
  - Thrasios + Seedborn Muse — card advantage loop
  - Thrasios + Culling Ritual — board wipe and mana burst

### Notes

- **Combination data** is community-submitted and may vary in quality
- **Salt ratings** are community opinions, not objective quality measures
- **Popularity** is tracked by votes and rank; highly voted combos are more reliable

---

*This completes the Commander Spellbook adapter design. It provides combo data, gameplan details, and performance metrics from Commander Spellbook, complementing the structural and statistical context from Scryfall, Tagger, and LearnCEDH adapters.*

