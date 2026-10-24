# NEBULA — Comprehensive Transfer Document

**File:** `NEBULA-TRANSFER.md`
**Purpose:** Complete documentation for moving the nebula project to another chat/system
**Last updated:** 2026-10-24

---

## 1. Project Overview

### What is nebula?
A deck analysis tool for Commander (cEDH) format. Takes a deck or card link and spits out all the info about the deck in one place.

### Core capability
**One program:** `nebula.py` — takes a link or decklist file, outputs a unified report using all adapters.

### Architecture
```
Input (link or file)
    ↓
nebula.py (unified entry point)
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│  Scryfall       │  Deck Validator │  Tagger         │
│  (card info)    │  (format rules) │  (card tags)    │
├─────────────────┼─────────────────┼─────────────────┤
│  Commander      │  Hypercalc.     │  Meta Compare   │
│  Spellbook      │  (probabilities)│  (CEDHStats)    │
│  (combos)       │                 │                 │
├─────────────────┼─────────────────┼─────────────────┤
│  LearnCEDH      │                 │                 │
│  (deck summary) │                 │                 │
└─────────────────┴─────────────────┴─────────────────┘
    ↓
Unified report (text or JSON)
```

---

## 2. File Structure

```
nebula/
├── nebula.py                      # The unified entry point (one program)
├── NEBULA-TRANSFER.md             # This document
├── NEBULA-*:                      # Design document references
│   ├── NEBULA-TAGGER.md
│   ├── NEBULA-COMMANDER-SPELLBOOK.md
│   ├── NEBULA-META-COMPARE.md
│   ├── NEBULA-HYPERCALCULATOR.md
│   ├── NEBULA-SCRYFALL.md
│   ├── NEBULA-DECKVALIDATOR.md
│   ├── NEBULA-LEARNCEDH.md
│   ├── NEBULA-DESIGN-PLAN.md
│   └── NEBULA-FREQUENCY-POOL.md
├── archetype/                     # Adapter implementations
│   ├── scryfall.py                # Card info + tags (Scryfall API)
│   ├── deck_validator.py          # Format validation (community rules)
│   ├── learncedh.py               # Deck summary (LearnCEDH API)
│   ├── commander_spellbook.py     # Combo data (REST API)
│   ├── hypercalculator.py         # Tag-based probability
│   ├── meta_compare.py            # CEDHStats meta context
│   └── classify.py                # ARCHETYPE BAND (skipped per user)
└── skills/
    └── nebula-adapters.md         # Design framework (saved as skill)
```

### Notes on the architecture

#### Cut item: `archetype/classify.py`
- **Status:** DELETED from build plan
- **Reason:** User decided archetype classification (turbo/stax/control) is not needed for the current scope
- **Evidence:** `NEBULA-ARCHETYPE-CLASSIFICATION.md` is kept as reference but not used

---

## 3. The Unified Program (nebula.py)

### What it does
Takes a link or decklist file and returns:
1. **Card info** — name, mana cost, CMC, type, keywords, oracle text (Scryfall)
2. **Deck validation** — Commander format rules (card count, commander, singletons, color identity, banned cards)
3. **Card tags** — mechanical/behavioural tags from tagger.scryfall.com
4. **Commander Spellbook combos** — cards that combo together
5. **Hypercalculator probabilities** — tag-based (e.g., chance of finding a tutor/ramp)
6. **Meta context** — CEDHStats aggregate stats, seat breakdown, draw dynamics
7. **LearnCEDH summary** — deck performance, strategy, meta position

### How to use

```bash
# Analyze a decklink.com URL
python nebula.py --link "https://decklink.com/deck/abc123"

# Analyze a kitncode URL
python nebula.py --link "https://www.kitincode.com/decks/xyz789"

# Analyze a local file
python nebula.py --decklist "my_deck.txt"

# Get just card info (single card)
python nebula.py --card "Thrasios, Triton Hero"

# Output in JSON format
python nebula.py --link "https://decklink.com/deck/abc123" --format json
```

### Output format
- **Text** (default): Human-readable summary
- **JSON**: Full structured data, save as `.json` file

### Dependencies
- `requests` (HTTP requests to APIs)
- `json` (built-in)
- `argparse` (built-in)

### Data sources
| Source | Role | Status |
|---|---|---|
| Scryfall API | Card info, tags | Available (no API key needed) |
| Commander Spellbook REST API | Combos | Available |
| CEDHStats | Meta context | Available (fetched data cached locally) |
| LearnCEDH API | Deck summary | Available (cached data in `learncedh/cached_decks.json`) |
| TopDeck API | Not used — TOP-16 data is PARTIAL (16-player events) |

---

## 4. Individual Adapters

### 4.1 Scryfall Adapter (`archetype/scryfall.py`)
**Purpose:** Card info + tags

**Input:** List of card names
**Output:** Card info (name, mana, CMC, type, keywords, oracle text) + tags (card tags, inherited tags, artwork-filtered)

**Data source:** Scryfall API (no API key needed for basic card info; tags come from tagger.scryfall.com)

**Test case:** Mind Rot (M21 #115) — `status: AVAILABLE`

### 4.2 Deck Validator Adapter (`archetype/deck_validator.py`)
**Purpose:** Commander format rules

**Input:** List of card names
**Output:** Card count, commander count, duplicates, color identity, banned cards, format_legal

**Rules checked:**
- Exactly 1 commander
- Card count ≤ 99
- No duplicate non-commander cards
- Commander color identity (from cached data)
- Banned cards (if cached ban list available)

**Test case:** 3-card Commander deck — `status: AVAILABLE`

### 4.3 Tagger Adapter (`archetype/tagger.py`)
**Purpose:** Card tags (mechanical/behavioural)

**Input:** List of card names
**Output:** Card tags, inherited card tags, artwork tags (filtered out)

**Tag filter:** Artwork tags (visual only) are always removed. Card tags (mechanical) + inherited tags are sent to the package.

**Data source:** tagger.scryfall.com (open read-only access)

**Test case:** Thrasios, Triton Hero (SPG #16) — 14 card tags, 10 inherited card tags, 13 artwork tags filtered

### 4.4 Commander Spellbook Adapter (`archetype/commander_spellbook.py`)
**Purpose:** Combo data

**Input:** List of card names (or commander card names)
**Output:** Cards that combo together, steps, resolution order, popularity, salt ratings

**Data source:** REST API at `https://backend.commanderspellbook.com/`
- Endpoints: `find-my-combos`, `cards`, `explain-query`, `card-list-from-url`, `card-list-from-text`, `estimate-bracket`

**Implementation:** `requests` + JSON parsing (no headless browser needed)

### 4.5 Hypercalculator Adapter (`archetype/hypercalculator.py`)
**Purpose:** Tag-based probability

**Input:** Decklist, tags (from tagger), deck_size (from deck_validator)
**Output:** Tag draw probability, opening hand distribution, combo tag chances, mana curve odds

**Algorithm:** Multivariate hypergeometric distribution (tag-based, not per-card)

**Key design:** `deck_size` is the actual mainboard count from deck_validator (handles partners/companions, e.g., 100-card decks)

**Example:** Cards with `ramp` tag: K cards in deck, n draws → P(X ≥ 1) = 1 − P(X = 0)

### 4.6 Meta Compare Adapter (`archetype/meta_compare.py`)
**Purpose:** CEDHStats meta context

**Input:** Commander name (optional)
**Output:** Aggregate stats, seat breakdown, draw dynamics, meta share

**Data sources:**
- `cedhstats.org/stats` — aggregate stats (6mo, all-time)
- `cedhstats.org/commanders/<id>` — per-commander profile
- `cedhstats.org/decklists?commander_id=<id>` — per-commander decks

**Key metrics:**
- Draw rate (6mo: 22.44%, Swiss-only: 32.69%)
- Seat PPG (Seat 1: 1.68, Seat 2: 1.38, Seat 3: 1.14, Seat 4: 0.92)
- Player tiers (Floor/Veterans/Ceiling)

### 4.7 LearnCEDH Adapter (`archetype/learncedh.py`)
**Purpose:** Deck summary and performance

**Input:** Decklist
**Output:** Deck summary, strategy, performance metrics (conversion rate, meta share, 95% range)

**Data cache:** `learncedh/cached_decks.json` (local cache for audit speed)

**Test case:** Tymna Thrasios — conversion 25.2%, meta share 1.5%, 95% range 97–128, 498 entrants

---

## 5. Data Storage

### Where data lives
| Location | Contents |
|---|---|
| `nebula/` | Code + design docs |
| `mtg_laya_project/config/` | CEDHStats data cache |
| `mtg_laya_project/learncedh/` | LearnCEDH cache |
| Obsidian vault (`ObsidianVault/user data/nebula/`) | Research notes |
| `C:/tmp/learncedh_cached_decks.json` | LearnCEDH cache (Windows path for terminal/MSYS) |

### Rules
- **nebula repo** = code + design docs only (no fetched data)
- **CEDHStats/other fetched data** = local codie cache (`mtg_laya_project/config/`), NOT in nebula repo
- **Research notes** → Obsidian vault

---

## 6. Git / GitHub Sync

### Current state
- **Repo:** `https://github.com/St-Milton1013/nebula`
- **Branch:** master
- **Commit:** `ba3df1c` — "Update nebula repo to current design state"

### Sync commands
```bash
cd nebula
git add -A
git commit -m "Update with latest design and code"
git push origin master
```

### What's tracked
All files in the `nebula/` directory (code, design docs, skill)

---

## 7. Known Issues & Limitations

| Issue | Workaround |
|---|---|
| Commander Spellbook REST API — batch mode not fully tested | Use single-card mode temporarily |
| TopDeck Top-16 data — 16-player events fail 50+ filter | Use CEDHStats instead (no longer used) |
| Moxfield/Archidekt URL fetching — not implemented yet | Provide decklist file or expand supported URL formats |
| LearnCEDH cache — uses Windows path | Use `C:/tmp/learncedh_cached_decks.json` |
| LF→CRLF warnings on Windows | Not an issue — cosmetic only |

---

## 8. Quick Reference

### Commands
```bash
# Run the unified program
python nebula.py --link "https://decklink.com/deck/abc123"
python nebula.py --decklist "my_deck.txt"
python nebula.py --card "Mind Rot"

# Install dependencies
pip install requests

# Update repo
cd nebula && git add -A && git commit -m "update" && git push
```

### File locations
| File | Path |
|---|---|
| Main program | `nebula/nebula.py` |
| Scryfall adapter | `nebula/archetype/scryfall.py` |
| Deck validator | `nebula/archetype/deck_validator.py` |
| Tagger adapter | `nebula/archetype/tagger.py` |
| Commander Spellbook | `nebula/archetype/commander_spellbook.py` |
| Hypercalculator | `nebula/archetype/hypercalculator.py` |
| Meta compare | `nebula/archetype/meta_compare.py` |
| LearnCEDH | `nebula/archetype/learncedh.py` |
| Design docs | `nebula/NEBULA-*` |
| Skill | `nebula/skills/nebula-adapters.md` |

---

## 9. Future Work (Not Started)

- Implement Moxfield/Archidekt URL fetching
- Implement batch mode for Commander Spellbook
- Full tests for all adapters
- Report generation (report template)
- More adapters (if needed)

---

## 10. Summary

The nebula project is now a single entry-point program (`nebula.py`) that takes a link or decklist and returns a unified report using all adapters. The individual adapters are well-documented in the `NEBULA-*` design files. The project is ready for the next chat to pick up.
