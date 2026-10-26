# NEBULA — Export Generator Plan

**Project:** Nebula Deck Analyzer
**Format:** Design document / implementation plan (no code)
**Status:** PLANNED
**Last updated:** 2026-10-25

---

## 1. Overview

The export generator is the central program of the nebula package. It takes a decklink URL or a local decklist file and outputs a comprehensive report that combines data from all adapters into a single, unified output.

The program follows a linear pipeline:
1. **Ingest** — read the input (URL or file)
2. **Validate** — check Commander format
3. **Canonicalize** — resolve cards to canonical data via Scryfall
4. **Adapters** — run each adapter in sequence, accumulating results
5. **Report** — combine all results into a unified output

No adapter runs in isolation. Every adapter receives the validated, canonicalized decklist as input.

---

## 2. Input Handling

### 2.1 Link Input (Decklink / Moxfield)

The program accepts decklist URLs from two supported sources, detected by host:

1. **Moxfield URLs** (`moxfield.com/decks/<id>`) — the most common link format
   today. The program resolves the decklist JSON via the Moxfield API.

2. **Decklink URLs** (`decklink.com/decks/<id>`) — the legacy format.
   The program sends an HTTP GET request and receives a JSON payload.

Processing (identical for both sources):
1. Sends an HTTP GET request to the URL
2. Receives a JSON payload (decklist data)
3. Parses the JSON to extract card names and quantities
4. Normalizes quantities — expands "2 Sol Ring" into two "Sol Ring" entries,
   and expands "2 basics" into two basic-land entries (generic placeholder; the
   exact basic lands are resolved during canonicalization in Section 4)
5. Returns a flat array of card names, with each count expanded

URL detection:
- Host `moxfield.com` → Moxfield deck
- Host `decklink.com` → Decklink deck
- Other hosts → report PARTIAL and continue (see Section 2.5)

Status: AVAILABLE for both source types.


### 2.3 Local File

If the user passes a local file path:
1. Reads the file line by line
2. For each line:
   - Split on whitespace with maxsplit=1
   - If the first token is a digit: "count card name" format → expand (repeat card name count times)
   - If the first token is not a digit: treat the whole line as a card name
3. Returns a flat array of card names

**Example:** File content "Sol Ring" → `["Sol Ring"]`
**Example:** File content "2 Sol Ring" → `["Sol Ring", "Sol Ring"]`

### 2.4 Architecture Decision

Do NOT build a remote loader class. The URL fetching logic stays local. The program handles:
- ✓ Decklink URLs (JSON response)
- ✓ Local file paths (text file with card names)

### 2.5 Known Limitations

- Moxfield URLs: direct HTTP fetch returns Cloudflare (403). Use MCP
  `get_moxfield_deck` (MTG MCP) as the primary ingestion path — call it
  with the deck URL. Fallback only if MCP returns empty/fail: paste the
  decklist directly.
- Archidekt URLs: direct HTTP fetch returns Cloudflare (403). Use MCP
  `get_archidekt_deck` (MTG MCP) as the primary ingestion path — call it
  with the deck URL. Fallback only if MCP returns empty/fail: paste decklist

---

## 3. Validation

After ingesting the decklist, the program validates the Commander format:

1. **Card count check**: Deck must have 100 cards total (1 commander + 99 mainboard), optionally including partners/companions
2. **Commander detection**: Exactly 1 commander card in the deck (a commander pair counts as 2)
3. **Partner/companion detection**: Partners and companions are allowed in Commander format
4. **Singleton rules**: No duplicate non-commander cards, EXCEPT basic lands (including Snow-Covered) and cards with "this can have any number in a deck"
5. **Color identity**: Derived from the commander's color identity. Partner color identity combines with the commander's; if a partner has a different color identity, the combined identity is used for all cards
6. **Banned cards**: Check against the Commander ban list (if cached)

**validate_deck tool**: The program uses the `validate_deck` tool from the mtg-mcp package (nathanmartins/mtg-mcp) for Commander format validation. This tool:

- 100-card deck size check
- Commander eligibility (rule 903.3) and ban check
- Singleton rule, exempting basic lands (including Snow-Covered) and cards like Relentless Rats
- Every card checked against the commander's color identity and the Commander banned list
- Flags names Scryfall does not recognize
- Looks cards up in batches of 75, so a full deck costs two Scryfall requests
- Supports JSON array or text format decklists

**Output:** A validation report with:

- Status: AVAILABLE / PARTIAL (for any format issue found)
- Card count
- Commander count
- Partners/companions count
- Duplicates list (if any)
- Color identity
- Banned cards (if any)

---

## 4. Canonicalization

After validation, the program canonicalizes each card using the Scryfall API.

1. For each card name in the decklist, query the Scryfall API for card data
2. Discards the concept of a local cache — card data is fetched on demand
   from Scryfall (no full-deck local storage)
3. **Primary reference**: Use the Scryfall `oracle_id` as the internal
   card identifier for all downstream adapters
4. Extract the following fields:
   - oracle_id (primary key)
   - name
   - mana_cost
   - cmc
   - color_identity
   - type_line
   - keywords
   - oracle_text_preview
   - status

Output: A canonicalized card list with full card facts for each card, keyed by oracle_id.

---

## 5. Adapter Pipeline

The program runs all adapters in sequence. Each adapter receives the validated, canonicalized decklist.

### 5.1 Adapter Run Order

| Order | Adapter | Input | Output |
|---|---|---|---|
1. **deck_validator** | Decklink (flat card array) | Format validation results (status, card count, commander count, duplicates, color identity, banned cards) |
2. **scryfall** | Validated decklist + cache | Card info (oracle_id, name, mana_cost, cmc, color_identity, type_line, edhrec_rank, keywords, oracle_text_preview, status) for each card |
3. **tagger** | Validated card names | Tag data for each card (card_tags, inherited_card_tags) |
4. **commander_spellbook** | Validated cards (by oracle_id) | Combo data (cards, steps, resolution order) |
5. **hypercalculator** | Validated cards + tags | Probability data (tag_draw_probability, opening_hand_distribution, combo_tag_chances) |
6. **meta_compare** | Commanders + validated layout | Meta context (aggregate stats, seat breakdown, draw dynamics) |
7. **learncedh** | Validated decklist | Deck summary (conversion rate, meta share, 95% range) |

### 5.2 Adapter Details

#### 5.2.1 Deck Validator
- Validates Commander format rules
- Returns: card_count, commander_count, duplicates, color_identity, banned, format_legal
- Status: AVAILABLE / PARTIAL

#### 5.2.2 Scryfall
- Looks up each card in the local cache by oracle_id
- Falls back to Scryfall API if not in cache
- Data extraction details: see Section 4 (Canonicalization)
- Returns: card info (oracle_id, name, mana_cost, cmc, color_identity, type_line, keywords, oracle_text_preview, status) for each card, keyed by oracle_id

> Note: `tagger` (Section 5.2.3) is responsible for card tags. Scryfall provides card data only; do not include tags here.

#### 5.2.3 Tagger
- Queries tagger.scryfall.com for card tags
- Filters out artwork tags (visual only)
- Returns: card_tags, inherited_card_tags

#### 5.2.4 Commander Spellbook
- Queries the REST API at backend.commanderspellbook.com
- Finds combos involving the cards
- Returns: combo data (cards, steps, resolution order)

#### 5.2.5 Hypercalculator
- Computes tag-based probabilities
- Uses hypergeometric distribution
- Returns: tag_draw_probability, opening_hand_distribution, combo_tag_chances

#### 5.2.6 Meta Compare
- Fetches CEDHStats data
- Returns: aggregate stats, seat breakdown, draw dynamics

#### 5.2.7 LearnCEDH
- Fetches deck summary from LearnCEDH
- Returns: conversion rate, meta share, 95% range

### 5.3 Continuity

If an adapter is unable to run:
- Mark its status as PARTIAL
- Include a caveat explaining why
- Continue to the next adapter
- Do NOT return early

---

## 6. Report Generation

After all adapters run, the program combines the results into a unified report.

### 6.1 Report Structure

The report has the following top-level sections:

1. **Header**
   - Report title
   - Generated timestamp
   - Source (decklink URL or file path)

2. **Deck Summary**
   - Total card count
   - Commander count
   - Deck name (if available)

3. **Adapter Summary**
   - For each adapter: status, key data
   - Status: AVAILABLE / PARTIAL / UNSUPPORTED

4. **Adapter Details**
   - For each adapter: full output
   - Structured data for further processing

5. **Caveats**
   - List of caveats from all adapters
   - Example: "Commander ban list not cached; banned-card check is PARTIAL"

6. **Decklist**
   - The full decklist (for verification)

### 6.2 Output Format

Two output formats are supported:

| Format | Output | Use case |
|---|---|---|
| Text | Human-readable summary | Console display |
| JSON | Structured data | Machine processing, further analysis |

### 6.3 File Output

When outputting in JSON format:
1. Write to the specified output file
2. File name: derived from the source (decklink URL or file path)
3. Content: the full report in JSON format

---

## 7. Single-File Package

The export generator can also generate a single-file package that contains all adapters in one file.

### 7.1 How It Works

1. The main program is `export_generator.py`
2. All adapter modules are combined into `nebula_package_single.py`
3. The single file is self-contained (no external imports)
4. The single file can be distributed and used without the original repo

### 7.2 Generation

The single-file package is generated via:
```bash
python export_generator.py --single nebula_package_single.py
```

---

## 8. Test Reporting

### 8.1 Test Results Directory

All test results are saved to `test_results/` (relative to the repo).

### 8.2 Test Cases

For each URL tested, record a separate verdict:

| Test | Input | Expected Result | Actual Result |
|---|---|---|---|
| Decklink JSON | `https://decklink.com/deck/abc123` | Decklist array | Decklist array |
| Moxfield (Cloudflare) | `https://www.moxfield.com/decks/abc` | PARTIAL | PARTIAL |
| Local file | `test_deck.txt` | Decklist array | Decklist array |

### 8.3 Test Report Requirements

Every test report must contain:
- Per-card records with fields: name, source, status, mana_cost, cmc, color_identity, type_line
- Adapter summary stats (e.g., # cards in local cache, # cards missing)
- Deck summary: card count, decklist array, status

A test report that only shows `[AVAILABLE] scryfall` with no card records is incomplete.

---

## 9. End-to-End Run

The program must be run end-to-end and produce output before the package is declared done.

### 9.1 Minimum Run

Run the program with a test decklist:
```bash
python export_generator.py --decklist test_deck.txt --output deck.json --format json
```

### 9.2 Verification

The run must:
1. Ingest the decklist
2. Validate the format
3. Canonicalize the cards
4. Run all 7 adapters
5. Generate the unified report
6. Write the output file

---

## 10. Design Document Reference

The following design documents contain the detailed spec for each adapter:

| Document | Adapter | Key Design Decisions |
|---|---|---|
| NEBULA-DECKVALIDATOR.md | deck_validator | Format rules, singleton, color identity |
| NEBULA-SCRYFALL.md | scryfall | Cache lookup, API fallback, tag filtering |
| NEBULA-TAGGER.md | tagger | Tag filter (artwork excluded), card + inherited tags |
| NEBULA-COMMANDER-SPELLBOOK.md | commander_spellbook | REST API endpoints |
| NEBULA-HYPERCALCULATOR.md | hypercalculator | Tag-based probability, hypergeometric |
| NEBULA-META-COMPARE.md | meta_compare | CEDHStats data source |
| NEBULA-LEARNCEDH.md | learncedh | Deck summary, performance metrics |

---

## 11. Git Workflow

### 11.1 Branch Strategy

- `master` branch: production code
- `develop` branch: feature development (optional)
- Feature branches: for new features (optional)

### 11.2 Commit Messages

Use conventional commit messages:
- `feat: add export generator`
- `fix: correct tagger output format`
- `docs: update export generator plan`
- `test: add test deck and results`

### 11.3 Push to GitHub

After committing:
```bash
git add -A
git commit -m "message"
git push origin master
```

---

## 12. Summary

The export generator is the single entry point for the nebula package. It:
1. Takes a decklink URL or local decklist file
2. Validates the Commander format
3. Canonicalizes cards via Scryfall
4. Runs all 7 adapters in sequence
5. Combines results into a unified report
6. Outputs as text or JSON

The program follows a linear, deterministic pipeline with no branching logic. Each adapter receives the same validated, canonicalized input. The final report combines all adapter outputs into a cohesive document.

---
