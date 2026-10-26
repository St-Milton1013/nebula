import io

file_path = '/c/Users/Main/Desktop/mtg_laya_project/nebula_repos/EXPORT_GENERATOR_PLAN.md'

# Read the file
with io.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the section 5.2.7
idx = content.find('5.2.7 LearnCEDH')
if idx >= 0:
    end_idx = content.find('### 5.3 Continuity', idx)
    if end_idx >= 0:
        # Complete new section content
        new_section = """#### 5.2.7 LearnCEDH

Fetches deck summary from LearnCEDH (learncedh.com), the cEDH community deck statistics platform.

**Expected Output:**
1. **Conversion rate** — percentage of games in which this deck wins when played
2. **Meta share** — percentage of all decks on the platform that use this deck
3. **95% range** — the statistical 95% confidence interval for the true win rate

---

### Data Acquisition

**Primary Data Source:**
LearnCEDH loads deck data from a GitHub-hosted JSON file:
```
https://raw.githubusercontent.com/evanpierceunm/learncedh/main/ranked-decks.json
```
This JSON contains 953 ranked decks with the following structure per deck:
- **name**: Deck name (e.g., 'Arcum Dagsson')
- **conversionRate**: Win rate as a decimal (e.g., 0.28169014084507044)
- **metaShare**: Meta share as a decimal (e.g., 0.0033971291866028708)

**JavaScript Rendering:**
The LearnCEDH website itself is a Squarespace-based page. The deck summary display uses:
- Element IDs: `#deck-conversion-rate`, `#deck-metashare`
- The page loads `ranked-decks.json` via JavaScript
- GraphQL API calls to `https://edhtop16.com/api/graphql` for live EDH data

**How to Fetch the Data (web client):**
1. Fetch `ranked-decks.json` from GitHub raw URL
2. Parse JSON to extract deck name, conversionRate, and metaShare
3. For the 95% range, no sample size is available in LearnCEDH data — the site shows conversion rate and meta share only

**How to Fetch the Data (API):**
- LearnCEDH does not expose a direct REST API
- The site uses GraphQL to query `https://edhtop16.com/api/graphql` for live EDH statistics
- For the 95% range, you would need to query EDHTop16 directly for the commander's match data:
  - `GET https://cedhtop16.com/api/commanders?search=<commander_name>`
  - Retrieve the `games`, `wins`, `draws`, `losses` fields
  - Calculate 95% CI: `p ± 1.96 * sqrt(p * (1-p) / n)` where p = win rate, n = games

---

### Test Results: Arcum Dagsson

**Source:** `https://learncedh.com/decklists?author=arcum-dagsson`

**Findings:**
- LearnCEDH is functional and loads deck data via the GitHub-hosted `ranked-decks.json`
- Found 1 deck by Arcum Dagsson:
  - **Deck name:** Arcum Dagsson
  - **Conversion rate:** 28.17% (0.28169014084507044)
  - **Meta share:** 0.34% (0.0033971291866028708)
- The site displays these values in the deck summary section using element IDs `#deck-conversion-rate` and `#deck-metashare`

**95% Range:**
- LearnCEDH does NOT provide the 95% confidence range in its data
- The site only exposes conversion rate and meta share
- To compute the 95% range, you must query EDHTop16 for the underlying match data (games, wins, draws, losses) and calculate:
  - `p = wins / total_games` (win rate)
  - `n = total_games` (sample size)
  - 95% CI = `p ± 1.96 * sqrt(p * (1-p) / n)`

---

### Implementation Notes

1. **Data source:** GitHub `ranked-decks.json` (953 decks) — preferred for deck summaries
2. **Live data:** EDHTop16 GraphQL API — required for 95% range calculation
3. **Conversion rate:** Displayed as percentage; stored as decimal in JSON
4. **Meta share:** Displayed as percentage; stored as decimal in JSON
5. **95% range:** NOT available from LearnCEDH directly; requires EDHTop16 API for sample size
6. **Deck filtering:** The JSON contains 953 decks; filter by deck name to find specific decks
7. **Fallback:** If GitHub JSON is unavailable, use the GraphQL API or paste decklist directly

---

**Status:** AVAILABLE (conversion rate and meta share); 95% range requires EDHTop16 API (PARTIAL)"""

        # Replace the section
        new_content = content[:idx] + new_section + content[end_idx:]
        
        # Write the file back
        with io.open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print('Section replaced successfully')
        print('File size:', len(new_content), 'bytes')
    else:
        print('### 5.3 Continuity not found')
else:
    print('5.2.7 LearnCEDH not found')
