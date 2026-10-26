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

### 2.1 Link Input (Decklink / Moxfield / Other)

The program accepts decklist URLs from multiple sources, detected by host:

1. **Moxfield URLs** (`moxfield.com/decks/<id>`) — the most common link format
   today. The program resolves the decklist via the Moxfield API (MCP
   `get_moxfield_deck`), bypassing Cloudflare. Although mtg-parser lists
   `moxfield.com` as a supported site, Moxfield's Terms of Service prohibit
   scraping, so we use the official API path instead. Fallback: paste decklist.

2. **Decklink URLs** (`decklink.com/decks/<id>`) — the legacy format.
   The program sends an HTTP GET request and receives a JSON payload.

3. **Library-Based Parsers (mtg-parser)** — for any other URL (e.g.,
   archidekt.com, mtggoldfish.com, tappedout.net, etc.), the program uses
   the `mtg-parser` Python library to fetch and parse the decklist.
   Supported sites include aetherhub.com, archidekt.com, deckstats.net,
   mtggoldfish.com, mtgjson.com, scryfall.com, tappedout.net, tcgplayer.com.

Processing (identical for all sources):
1. Sends an HTTP GET request to the URL (using the appropriate client
   for each site — e.g., cloudscraper for Cloudflare-protected sites)
2. Receives a JSON payload or HTML with decklist data
3. Parses the decklist to extract card names and quantities
4. Normalizes quantities — expands "2 Sol Ring" into two "Sol Ring" entries,
   and expands "2 basics" into two basic-land entries (generic placeholder;
   the exact basic lands are resolved during canonicalization in Section 4)
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

- Moxfield and Archidekt URLs: direct HTTP fetch returns Cloudflare (403).
  Use the respective MCP tools (`get_moxfield_deck`, `get_archidekt_deck`)
  from the MTG MCP as the primary ingestion path — call it with the deck
  URL. Fallback only if MCP returns empty/fail: paste the decklist directly.

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
- Format legality (format_legal)

---

## 4. Canonicalization

After validation, the program canonicalizes each card using the Scryfall API.

1. For each card name in the decklist, query the Scryfall API for card data.
   - Collects the card's face data (including `card_faces` when the card has
     multiple faces) via the Scryfall API.
   - On cards lacking a root-level `oracle_id` (e.g., reversible cards whose
     face-level records carry their own Oracle IDs), the face-level record is
     used as the canonical identity. The adapter handles this exceptional
     layout explicitly rather than assuming every Scryfall card object
     always has a root-level identifier.

2. **Deck identity**: `oracle_id` plus quantity and commander designation.
   - Each unique card is identified by its `oracle_id`; quantity and
     commander designation are tracked separately as deck-level metadata.

3. **Canonical records**: one canonical record per Oracle ID.
   - All face data (complete `card_faces` when present) is retained in the
     canonical record.

4. **Reference data**: retain the Scryfall fields needed by downstream
   adapters:
   - oracle_id (primary key)
   - name
   - mana_cost
   - cmc
   - color_identity
   - type_line
   - keywords
   - oracle_text_preview
   - status
   - card_faces (when present, for face-level data)

5. **Reproducibility**: preserve the captured canonical records and their
   version or content hash. Later runs can reuse the same evidence without
   making redundant requests — the captured snapshot (record + hash) is the
   basis for reproducibility, not printing-specific identifiers.

Output: A canonicalized card list with full card facts for each card, keyed by
oracle_id. This output is saved and referenced by all downstream adapters.

---

## 5. Adapter Pipeline

The program runs all adapters in sequence. Each adapter receives the validated, canonicalized decklist.

### 5.1 Adapter Run Order

| Order | Adapter | Input | Source | Output |
|---|---|---|---|---|
| 1. **deck_validator** | Decklink (flat card array) | Decklink JSON | decklink.com | Format validation results (status, card count, commander count, duplicates, color identity, banned cards) |
| 2. **scryfall** | Validated decklist + cache | Scryfall API | scryfall.com | Card info (oracle_id, name, mana_cost, cmc, color_identity, type_line, keywords, oracle_text_preview, status) for each card |
| 3. **tagger** | Validated card names | tagger.scryfall.com API | tagger.scryfall.com | Tag data for each card (card_tags, inherited_card_tags) |
| 4. **commander_spellbook** | Validated cards (by oracle_id) | REST API | backend.commanderspellbook.com | Combo data (cards, steps, resolution order) |
| 5. **hypercalculator** | Validated cards + tags | tagger.scryfall.com (tags) | tagger.scryfall.com | Probability data (tag_draw_probability, opening_hand_distribution, combo_tag_chances) |
| 6. **meta_compare** | Commanders + validated layout | CEDHStats.org + EDHTop16.com | cedhstats.org, cedhtop16.com | Meta context (aggregate stats, seat breakdown, draw dynamics) |
| 7. **learncedh** | Validated decklist | GitHub JSON + LearnCEDH website | learncedh.com, GitHub (ranked-decks.json) | Deck summary (conversion rate, meta share, 95% range) |

### 5.2 Adapter Details

#### 5.2.1 Deck Validator

- **Source:** Decklink JSON (decklink.com)
- Validates Commander format rules
- Returns: card_count, commander_count, duplicates, color_identity, banned, format_legal
- Status: AVAILABLE / PARTIAL

#### 5.2.2 Scryfall

- **Source:** Scryfall API (scryfall.com)
- Looks up each card in the local cache by oracle_id
- Falls back to Scryfall API if not in cache
- Data extraction details: see Section 4 (Canonicalization)
- Returns: card info (oracle_id, name, mana_cost, cmc, color_identity, type_line, keywords, oracle_text_preview, status) for each card, keyed by oracle_id
- Source label: scryfall.com

> Note: `tagger` (Section 5.2.3) is responsible for card tags. Scryfall provides card data only; do not include tags here.

#### 5.2.3 Tagger

- **Source:** tagger.scryfall.com API
- Queries tagger.scryfall.com for card tags
- Filters out artwork tags (visual only)
- Returns: card_tags, inherited_card_tags
- Source label: tagger.scryfall.com

> Reference: [mtg_ultimate_tag](https://github.com/benjamin-fouilleul/mtg_ultimate_tag) — Elixir + Phoenix web app that scrapes tags from `tagger.scryfall.com` for decklists. Confirms `tagger.scryfall.com` as the correct tag source.

#### 5.2.4 Commander Spellbook

- **Source:** REST API (backend.commanderspellbook.com)
- Finds combos involving the cards
- Returns: combo data (cards, steps, resolution order)
- Source label: backend.commanderspellbook.com

#### 5.2.5 Hypercalculator

- **Source:** tagger.scryfall.com (card tags); local computation
- Computes tag-based probabilities using the hypergeometric distribution
- Default hand size: 7 cards
- Input: validated mainboard cards only (commander(s) and companions excluded)
- Input: card tags from the tagger section (Section 5.2.3)

**Calculations:**

1. **Tag draw probability**: For each tag, calculate the probability of drawing at least one card with that tag in the opening hand.
2. **Opening hand distribution**: Probability distribution of card counts per tag in the opening hand.
3. **Combo tag chances**: Probability of drawing specific tag combinations in the opening hand.
4. **Average lands in opener**: Expected number of lands in the opening hand, based on land count and opening hand size (7 cards by default).

**Metric definitions (this section constitutes the contract; required for every metric):**

| Metric | Population | Sample Size | Excluded Cards | Mathematical Event | Assumptions |
|---|---|---|---|---|---|
| Tag draw probability | All mainboard cards in the validated deck | 7 cards drawn without replacement (default opening hand) | Commander(s) and partners/companions are excluded | P(draw at least 1 card with tag X in the 7-card hand) = 1 - P(draw 0 cards with tag X) | Cards are drawn uniformly at random; each card has equal probability of selection; tags are fixed properties of each card |
| Opening hand distribution | All mainboard cards in the validated deck | 7 cards drawn without replacement (default opening hand) | Commander(s) and partners/companions are excluded | P(n cards with tag X in hand) = hypergeometric probability | Same as above; tag categories are defined by the tagger section |
| Combo tag chances | All mainboard cards in the validated deck | 7 cards drawn without replacement (default opening hand) | Commander(s) and partners/companions are excluded | P(have at least one card from each of N tag groups) = drawing from the intersection of tag groups | This is a tag-draw probability, NOT a playable-combo completion rate. Cards may have overlapping tags (see below). Category probabilities cannot be treated as independent when tags overlap |
| Average lands in opener | All land cards in the validated deck | 7 cards drawn without replacement (default opening hand) | Commander(s) and partners/companions are excluded | E[lands in hand] = 7 x (land_count / mainboard_count) | Cards are drawn uniformly at random; expected value is linear regardless of independence |

**Important interpretations:**

- **Tag-based estimates, not combo completion rates or deck performance.** All metrics in this section are tag-draw probabilities computed from tagged card lists. They do NOT measure whether a playable combo exists, whether a card combination can be executed, or overall deck strength. A "combo tag chance" means only that at least one card with each of the listed tags is present in the opening hand-not that those cards can be played together.
- **Overlapping tags.** Many cards carry multiple tags (e.g., a card may be both "artifact" and "enchantment"). Tag-draw probabilities must not be treated as independent events, because a card drawing a card with tag A may also satisfy tag B. The hypergeometric calculation for each individual tag assumes no overlap; when tags overlap, the joint probability of drawing at least one card from each group in a set is strictly less than the product of the individual probabilities. Do not multiply individual tag probabilities to estimate combined chances.
- **Sample size.** The default opening hand size is 7 cards, but adapters may expose this as a configurable parameter. When changed, sample size must be updated accordingly.
- **Excluded cards.** Commander(s) and partners/companions are always excluded from the Hypercalculator population, even if they carry tags. This ensures probability calculations reflect only the playable mainboard.

#### 5.2.6 Meta Compare

- **Source:** CEDHStats.org + EDHTop16.com
- Fetches CEDHStats data (cedhstats.org) and/or EDHTop16 data (cedhtop16.com)
- Returns: aggregate stats, seat breakdown, draw dynamics, meta share, board
  (power level), decklist context
- Source label: cedhstats.org, cedhtop16.com

**Data Sources:**
- **cedhstats.org** — free, tracks competitive EDH from TopDeck.gg; provides
  player experience bands, PPG, win rates, deck trends
- **cedhtop16.com** — free, public EDH Top 16 data; provides tournament
  standings, player results, color identity, commander entries

**Statistics Available:**
1. **Aggregate Stats**
   - Top 16 standings (win rate, draws, losses, average standing)
   - Meta share (deck popularity as % of entries)
   - Board (power level) estimation for the commander

2. **Seat Breakdown**
   - Player performance by seat
   - Win rate by seat position
   - Representation in top cut vs swiss

3. **Draw Dynamics**
   - Points per game (PPG) by pilot experience band (floor, veterans, ceiling)
   - 90% confidence interval on PPG estimates
   - Meta trends over time (30d, 90d, 180d windows)

4. **Deck Context**
   - Top played cards for this commander (inclusion rate, field inclusion, lift)
   - Card PPG delta (performance when card present vs absent)
   - 90% Bayesian uncertainty range

**Data Source Details:**
- Dataset window: 6 months of decklists from eligible 16+ player events
- Commander cards excluded from card stats
- Gates: only decks with 0.2%+ meta share over their period are eligible
- Rate limits: 120 requests/minute (EDHTop16 API)

**Output:** Structured data for each adapter, combining aggregate stats,
seat breakdown, draw dynamics, and card context into a unified report.

#### 5.2.7 LearnCEDH

- **Source:** GitHub `ranked-decks.json` + LearnCEDH website (learncedh.com)
- Fetches deck summary from LearnCEDH (learncedh.com), the cEDH community deck statistics platform
- Returns: conversion rate, meta share, 95% range, text explanations
- Source label: learncedh.com, GitHub (raw.githubusercontent.com/evanpierceunm/learncedh)

**Expected Output:**
1. **Conversion rate** — percentage of games in which this deck wins when played
2. **Meta share** — percentage of all decks on the platform that use this deck
3. **95% range** — the statistical 95% confidence interval for the true win rate
4. **Text explanations** — deck narrative: gameplan, strengths, weaknesses, core combos, and win conditions (available on the deck page, e.g., `learncedh.com/decklists/<deck_name>`)

---

### Data Acquisition

**Primary Data Source (numeric data):**
LearnCEDH loads deck data from a GitHub-hosted JSON file:
```
https://raw.githubusercontent.com/evanpierceunm/learncedh/main/ranked-decks.json
```
This JSON contains 953 ranked decks with the following structure per deck:
- **name**: Deck name (e.g., 'Arcum Dagsson')
- **conversionRate**: Win rate as a decimal (e.g., 0.28169014084507044)
- **metaShare**: Meta share as a decimal (e.g., 0.0033971291866028708)

**Website Rendering (text explanations):**
The LearnCEDH website is a Squarespace-based page. Deck detail pages (e.g.,
`learncedh.com/decklists/arcum-dagsson`) contain:
- Deck summary section (conversion rate, meta share)
- **Core Gameplan** — step-by-step strategy description
- **Strengths and Weaknesses** — detailed analysis of the deck's approach
- **Core Combos** — multi-card combo breakdowns with step-by-step resolution
- **Win Conditions** — how the deck wins the game
- **Tips for Playing** — strategic advice for mulligan, protection, fetch selection

**Element IDs (deck summary):**
The deck summary display uses:
- Element IDs: `#deck-conversion-rate`, `#deck-metashare`
- The page loads `ranked-decks.json` via JavaScript
- GraphQL API calls to `https://edhtop16.com/api/graphql` for live EDH data

**How to Fetch the Data (web client):**
1. Fetch `ranked-decks.json` from GitHub raw URL
2. Parse JSON to extract deck name, conversionRate, and metaShare
3. For text explanations, fetch the deck detail page:
   - `https://learncedh.com/decklists/<deck_name_slug>` (e.g.,
     `https://learncedh.com/decklists/arcum-dagsson`)
   - Extract text from sections: Core Gameplan, Strengths and Weaknesses,
     Core Combos, Win Conditions, Tips for Playing

**How to Fetch the Data (API):**
- LearnCEDH does not expose a direct REST API
- The site uses GraphQL to query `https://edhtop16.com/api/graphql` for live EDH data
- For the 95% range, you would need to query EDHTop16 directly for the commander's match data:
  - `GET https://cedhtop16.com/api/commanders?search=<commander_name>`
  - Retrieve the `games`, `wins`, `draws`, `losses` fields
  - Calculate 95% CI: `p ± 1.96 * sqrt(p * (1-p) / n)` where p = win rate, n = games

---



### Implementation Notes

1. **Data source:** GitHub `ranked-decks.json` (953 decks) — preferred for deck summaries
2. **Live data:** EDHTop16 GraphQL API — required for 95% range calculation
3. **Conversion rate:** Displayed as percentage; stored as decimal in JSON
4. **Meta share:** Displayed as percentage; stored as decimal in JSON
5. **95% range:** NOT available from LearnCEDH directly; requires EDHTop16 API for sample size
6. **Text explanations:** Available on deck detail pages (e.g., `learncedh.com/decklists/arcum-dagsson`) — extract via HTML scraping, not from the GitHub JSON
7. **Deck filtering:** The JSON contains 953 decks; filter by deck name to find specific decks
8. **Fallback:** If GitHub JSON is unavailable, use the GraphQL API or paste decklist directly

---

**Status:** AVAILABLE (conversion rate, meta share, text explanations); 95% range requires EDHTop16 API (PARTIAL)

### 5.3 Continuity

Adapters that cannot run normally are handled as follows. There is a
distinction between two failure modes, and each is logged differently:

**FAIL (adapter failed):**
- Status: FAIL
- A hard failure — the adapter raised an error, returned a falsy result where
  a result was expected, or otherwise failed in a way that is treated as a
  definite failure rather than an incomplete run.
- Logged as FAIL, not PARTIAL.
- The error is captured in the adapter's output and included in the report's
  Caveats section.
- Continue to the next adapter. Do NOT return early.

**PARTIAL (adapter unable to run):**
- Status: PARTIAL
- The adapter could not complete, but the failure is not a hard "no result".
  Examples: missing external API key, service not responding, rate-limited and
  not recoverable within the run window, or the adapter was expressly skipped.
- Include a caveat explaining why the adapter is PARTIAL.
- Continue to the next adapter. Do NOT return early.

The report's Caveats section collects every PARTIAL / FAIL note from every
adapter so the user sees, at a glance, which adapters did not fully complete
and why.

The linear pipeline (Section 1) is not branched. An adapter that fails or is
PARTIAL does not halt the pipeline; it only marks its own status and moves on.
Exactly one adapter may be in FAIL at a time per deck run; all others that
could not complete are PARTIAL with caveats.

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
  - For each adapter: status, key data, and source
  - Status: AVAILABLE / PARTIAL / UNSUPPORTED

4. **Adapter Details**
  - For each adapter: full output with source attribution
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
| Text | Human-readable summary | Console display; also written to the Obsidian vault |
| JSON | Structured data | Machine processing, further analysis |

**Text file contents** — the text report captures every adapter export, in
adapter order, followed by the Caveats section:

1. **Deck Validator** — format status, card count, commander count,
   duplicates, color identity, banned cards
2. **Scryfall** — card facts per card (oracle_id, name, mana_cost, cmc,
   color_identity, type_line, keywords, oracle_text_preview,
   status)
3. **Tagger** — card_tags, inherited_card_tags
4. **Commander Spellbook** — combos found (cards, steps, resolution order)
5. **Hypercalculator** — tag draw probabilities, opening hand distribution,
   combo tag chances, average lands in opener (with tag-based estimate
   labeling and metric definitions per Section 5.2.5)
6. **Meta Compare** — aggregate meta context, seat breakdown, 95% range
7. **LearnCEDH** — conversion rate, meta share, 95% range, text
   explanations (gameplan, strengths, weaknesses, combos, win conditions)
8. **Caveats** — every PARTIAL / FAIL note from every adapter

### 6.3 File Output

**Text output:**
1. Write to the Obsidian vault at
   `C:\Users\Main\Documents\cedh data\audit package export`
2. Content: the full text report (all adapter sections plus Caveats), in
   human-readable format

**Naming convention:**

Text files are named: `YYYY-MM-DD_Commanders_HHMMSS.txt`

- **Date** — generation date, `YYYY-MM-DD`
- **Commanders** — the deck's commander name(s), taken verbatim from the
  validated deck, space-joined (e.g. `Arcum Dagsson`, `Korvold Warped
  Eclipse`). Illegal file-name characters are replaced with `-`.
- **Time** — local time, `HHMMSS`

Example: `2026-10-26_Arcum Dagsson_281702.txt`
Example: `2026-10-26_Korvold Warped Eclipse_281702.txt`

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
The single-file package is generated via:
```bash
python export_generator.py --single nebula_package_single.py
```

**Naming:** The generated file uses the same naming convention as the
text output (`YYYY-MM-DD_Commanders_HHMMSS.txt`), with the extension
`.py`:

- Pattern: `YYYY-MM-DD_Commanders_HHMMSS_nebula_package_single.py`
- **Date** — generation date, `YYYY-MM-DD`
- **Commanders** — the deck's commander name(s), taken verbatim from the
  validated deck, space-joined (e.g. `Arcum Dagsson`, `Korvold Warped
  Eclipse`). Illegal file-name characters are replaced with `-`.
- **Time** — local time, `HHMMSS`

Example: `2026-10-26_Arcum Dagsson_281702_nebula_package_single.py`
Example: `2026-10-26_Korvold Warped Eclipse_281702_nebula_package_single.py`

The single-file package is self-contained (no external imports) and can be
distributed and used without the original repo.

## 8. Test Reporting

### 8.1 Test Results Directory

All test results are saved to `test_results/` (relative to the repo).

### 8.2 Test Cases

For each URL tested, record a separate verdict:

| Test | Input | Source | Expected Result | Actual Result |
|---|---|---|---|---|
| Decklink JSON | `https://decklink.com/deck/abc123` | decklink.com | Decklist array | Decklist array |
| Moxfield | `https://www.moxfield.com/decks/abc` | moxfield.com | PARTIAL | PARTIAL |
| Local file | `test_deck.txt` | local file | Decklist array | Decklist array |

### 8.3 Test Report Requirements

Every test report must contain:
- Per-card records with fields: name, source, status, mana_cost, cmc, color_identity, type_line
- Adapter summary stats (e.g., # cards in local cache, # cards missing)
- Deck summary: card count, decklist array, status
- Source attribution: for each adapter result, record the source (e.g., scryfall.com, tagger.scryfall.com, cedhstats.org, cedhtop16.com, learncedh.com, GitHub)
- A test report that only shows `[AVAILABLE] scryfall` with no card records or source attribution is incomplete.

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
