---
name: nebula-adapters
description: Nebula adapter framework design.
---

# NEBULA — ADAPTER FRAMEWORK DESIGN

**Repo:** `nebula` (Desktop/project front gate/Projects/nebula)
**Status:** DESIGN — not implemented
**Last updated:** 2026-10-24

## Capability inventory

| Capability | Status | Detail file |
|---|---|---|
| `archetype.scryfall` | AVAILABLE | `NEBULA-SCRYFALL.md` |
| `archetype.deck_validator` | AVAILABLE | `NEBULA-DECKVALIDATOR.md` |
| `archetype.learncedh` | AVAILABLE | `NEBULA-LEARNCEDH.md` |
| `archetype.commander_spellbook` | PROPOSED | `NEBULA-COMMANDER-SPELLBOOK.md` |
| `archetype.hypercalculator` | PROPOSED | `NEBULA-HYPERCALCULATOR.md` |
| `archetype.tagger` | PROPOSED | `NEBULA-TAGGER.md` |
| `archetype.meta_compare` | PROPOSED | `NEBULA-META-COMPARE.md` |
| `archetype.classify` | NOT IMPLEMENTED (dropped per user) | — |

---

## Design principles

1. **Tag-based probability** — hypercalculator computes probability per tag (not per card)
2. **Commander Spellbook REST API** — use backend.commanderspellbook.com (not client-side JSX)
3. **Tagger design** — artwork tags excluded, card tags + inherited tags included
4. **Meta compare via CEDHStats** — not TopDeck Top-16 (16-player events fail 50+ filter)
5. **Meta context vs archetype classification** — separate meta context (CEDHStats) from archetype stance

## Storage layout

- nebula repo = design files + adapter code only
- CEDHStats/other fetched data = local codie cache (`mtg_laya_project/config/`)
- Research notes → Obsidian vault
- Cache files use Windows paths: `C:/tmp/learncedh_cached_decks.json`

## Common pitfalls

| Pitfall | Solution |
|---|---|
| 99 hardcoded | Use `deck_size` from `archetype.deck_validator` |
| `commader_count` typo | Use `commander_count` |
| Terminal path issues | Use `Python313/python.exe` |
| MSYS path conversion | Use `C:/tmp/` not MSYS paths |
| Google Sheets API blocked | Don't hardcode API keys |

## Reference data (verified 2026-10-24)

### CEDHStats
- 6mo: 2,920 tournaments, 73,052 pods, 33,783 players, 79,216 entries
- All time: 10,451 tournaments, 276,914 pods, 95,094 players, 277,901 entries
- Draw rate: 22.44%, Swiss-only: 32.69%
- Thrasios/Tymna: record 1.29, Swiss WR 27.7%, meta share 3.0%

### Commander Spellbook REST API
- Base: `https://backend.commanderspellbook.com/`
- Endpoints: `cards`, `find-my-combos`, `explain-query`, `card-list-from-url`, `card-list-from-text`, `estimate-bracket`

### Tagger (verified)
- Thrasios, Triton Hero (SPG #16): 14 card tags, 10 inherited card tags, 13 artwork tags (excluded)

*Design framework for nebula adapters. Update when new adapters are added.*
