# NEBULA — META COMPARE ADAPTER

**Capability ID:** `archetype.meta_compare`
**Owner:** Codie (measurement) + Jin (interpretation)
**Date:** 2026-10-24
**Status:** DESIGN REFERENCE — not implemented

---

## 1. Package contents

The Meta Compare adapter compares a deck against the CEDH meta using
**CEDHStats** aggregate data. Unlike the frequency pool approach (TopDeck
Top-16 decks), CEDHStats provides:

- **Aggregate statistics** (tournament counts, players, entries, draw rates)
- **Seat dynamics** (seat-by-seat PPG, win/draw percentages)
- **Player tiers** (Floor, Veterans, Ceiling)
- **Draw dynamics** (draw rate trends, Swiss pressure, draw-adjusted metrics)

### Data sources

| Source | Role | Notes |
|---|---|---|
| `https://cedhstats.org/stats` | Primary | Aggregate stats, draw dynamics, seat metrics |
| `https://cedhstats.org/commanders/<id>` | Commander profile | Per-commander stats |
| `https://cedhstats.org/decklists?commander_id=<id>` | Per-commander decks | Tournament-by-tournament results |
| `cards.json` | Local cache | Card facts |

### What the adapter provides

| Metric | Description | Source |
|---|---|---|
| **Deck classification** | Tier, performance band, meta position | CEDHStats profile |
| **Deck strength** | Record, PPG, rank | CEDHStats profile |
| **Meta context** | Aggregate stats, draw rate, seat distribution | CedhStats stats |
| **Seat breakdown** | Seat-by-seat PPG, win/draw | CedhStats stats |
| **Player tiers** | Floor/Veterans/Ceiling PPG, rank | CedhStats profile |
| **Draw dynamics** | Draw rate, Swiss pressure, draw-adjusted metrics | CedhStats stats |

---

## 2. Delivery packet schema

### 2.1 Input schema

{
  "adapter": "num_adapter",
  "mode": "meta_compare",
  "commander": "Tymna the Weaver",
  "metadata": {
    "deck_name": "Tymna Thrasios",
    "format": "commander",
    "audit_date": "2026-10-24"
  }
}

### 2.2 Output schema

{
  "adapter": "num_adapter",
  "mode": "meta_compare",
  "status": "AVAILABLE",
  "commander": {
    "name": "Tymna the Weaver",
    "stats": {
      "entries": 1000,
      "record": "1.29",
      "swiss_wr": "27.7%",
      "top_cut_wr": "27.9%",
      "meta_share": "3.0%",
      "floor_ppg": 1.04,
      "veterans_ppg": 1.34,
      "ceiling_ppg": 2.57,
      "rank": "#4 / 30"
    }
  },
  "meta_context": {
    "6mo": {
      "tournaments": 2920,
      "pods": 73052,
      "players": 33783,
      "entries": 79216,
      "draw_rate": "22.44%",
      "draw_rate_swiss": "32.69%",
      "neutral_ppg": 1.194
    },
    "all_time": {
      "tournaments": 10451,
      "pods": 276914,
      "players": 95094,
      "entries": 277901
    }
  },
  "seat_breakdown": {
    "all_players_6mo": [
      {"seat": 1, "ppg": 1.68, "pods": 50047},
      {"seat": 2, "ppg": 1.38, "pods": 50038},
      {"seat": 3, "ppg": 1.14, "pods": 50034},
      {"seat": 4, "ppg": 0.92, "pods": 43275}
    ],
    "top_100_players_6mo": [
      {"seat": 1, "ppg": 2.86, "pods": 1822},
      {"seat": 2, "ppg": 2.46, "pods": 1649},
      {"seat": 3, "ppg": 2.18, "pods": 1607},
      {"seat": 4, "ppg": 2.04, "pods": 1428}
    ]
  },
  "draw_dynamics": {
    "6mo": {
      "draw_rate": "22.44%",
      "swiss_draw_rate": "32.69%",
      "draw_records": 63495,
      "neutral_ppg": 1.194
    },
    "swiss_pressure": [
      {"quarter": "Q2", "draw_rate": "36.75%", "pods": 19670, "change": "+4.06pp"},
      {"quarter": "Q3", "draw_rate": "33.47%", "pods": 17146, "change": "+0.77pp"},
      {"quarter": "Q4", "draw_rate": "30.05%", "pods": 23012, "change": "-2.65pp"},
      {"quarter": "Q1", "draw_rate": "29.43%", "pods": 9868, "change": "-3.26pp"}
    ]
  },
  "caveats": [
    "CEDHStats data is aggregated and may not reflect current meta",
    "Draw rate is a proxy for table pressure, not a direct metric"
  ]
}

### 2.3 Report section mapping

| Report section | Source output key | Status |
|---|---|---|
| **Commander profile** | `commander.stats` | AVAILABLE |
| **Meta context** | `meta_context` | AVAILABLE |
| **Seat breakdown** | `seat_breakdown` | AVAILABLE |
| **Draw dynamics** | `draw_dynamics` | AVAILABLE |
| **Deck classification** | From `archetype.classify` (not used — user decision) | N/A |

### 2.4 Caveats to state

The report must state:

1. **Data source:** CEDHStats is aggregated data, not individual tournament
   records. Data may not reflect the current meta.
2. **Proxy metrics:** Draw rate is a proxy for table pressure, not a direct
   measure. Swiss-only draw rate is more accurate.
3. **Commander-specific data:** Commander stats are based on all decks with
   that commander, not just yours.

---

## 3. Integration with other components

| Source | Data | Package use |
|---|---|---|
| **CEDHStats** | Aggregate stats, seat metrics, draw dynamics | Meta context |
| **LearnCEDH** | Deck summary, performance metrics | What the deck is (narrative) |
| **Commander Spellbook** | Combo data | What the deck can do (gameplan) |
| **Tagger** | Card tags | What the cards do (behavioural) |
| **Scryfall** | Card info | What the cards are (structural) |

The Meta Compare adapter provides the **meta context** for a deck, answering:
*Where does this deck sit in the CEDH meta? What does the meta look like?*

---

## 4. Open questions (resolved)

### 4.1 Commander identification

**Decision:** Commander identification uses the `commander` parameter. If the
deck is a two-commander deck, the adapter uses the commander with the most
data (based on entries).

### 4.2 Data window

**Decision:** Use 6-month window (`period=6m`) for recent performance, plus
all-time data for context.

### 4.3 Data freshness

**Decision:** CEDHStats data is updated with each data sync. The adapter notes
the `timeframe` field in the output.

---

## 5. Implementation note

### Files to create

| File | Purpose |
|---|---|
| `NEBULA-META-COMPARE.md` | **This document** — the Meta Compare adapter blueprint. |
| `archetype/meta_compare.py` | New module: `num_adapter(mode="meta_compare", commander, options)` — fetches meta data from CEDHStats. |

### Library dependencies

| Dependency | Purpose |
|---|---|
| `requests` | HTTP requests to CEDHStats API |
| `json` | Parse JSON responses |

### Constraints

- Read-only access to CEDHStats (no data submission)
- Caching allowed locally for audit speed
- No live API calls during the audit — use cached data for testing

---

## 6. Reference — Tymna the Weaver example

### Test case

Commander: `Tymna the Weaver`

### Expected output

| Section | Data |
|---|---|
| **Commander stats** | `entries: 1000`, `record: 1.29`, `swiss_wr: 27.7%`, `top_cut_wr: 27.9%`, `meta_share: 3.0%`, `floor_ppg: 1.04`, `veterans_ppg: 1.34`, `ceiling_ppg: 2.57` |
| **Meta context (6mo)** | `2,920 tournaments`, `73,052 pods`, `33,783 players`, `79,216 entries`, `draw_rate: 22.44%`, `swiss_draw_rate: 32.69%`, `neutral_ppg: 1.194` |
| **Seat breakdown** | Seat 1: 1.68 PPG, Seat 2: 1.38 PPG, Seat 3: 1.14 PPG, Seat 4: 0.92 PPG |
| **Draw dynamics** | Q2 Swiss: 36.75% (baseline 32.69%, +4.06pp), Q3: 33.47%, Q4: 30.05%, Q1: 29.43% |

---

*This completes the Meta Compare adapter design. It provides meta context from CEDHStats, complementing the structural, behavioural, and gameplan data from the other adapters.*
