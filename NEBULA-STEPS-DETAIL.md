# NEBULA — STEPS-DETAIL — Deep Dive: Steps 6, 7, 9, 10, 11, 12

**Focus:** how each of these steps actually works, mechanically.
**Convention:** local paths are Windows-style; `C:\Users\Main\Desktop\project front gate\Projects\Codie\sessions\...` = `C:\Users\Main\Desktop\project front gate\Projects\Codie\sessions\...`
**Pre-flight:** codie-audit skill v0.8.0 (codieaudit profile). Frozen snapshot from `/audit` invocation anchors everything.

---
## STEP 6 — Evidence packet build

**Goal:** turn the frozen snapshot + canonical card facts + deterministic metrics into a single, provenance-tagged, hierarchy-ordered evidence object. Everything after this step reads from this packet, not from the raw deck.

### 6.1 The evidence-packet schema

The packet is a JSON object. Schema (per `evidence-packet.md` contract):

```json
{
  "packet_id": "ep-<snapshot_id>",
  "snapshot_id": "audit-<ts>-<sha256>",
  "generated_utc": "2026-10-24T01:15:00Z",
  "observations": [ { "type": "...", "source": "...", "content": "...", "timestamp": "..." } ],
  "measurements": [ { "type": "...", "key": "...", "value": "...", "uncertainty": "..." } ],
  "context": [ { "type": "...", "source": "...", "content": "...", "attribution": "..." } ],
  "provenance": {
    "deck": "snapshot_id (FROZEN)",
    "card_facts": "cards.json (Scryfall bulk, hashed fingerprint)",
    "rules": "rules_index_academyruins.json (Academy Ruins API)",
    "tournaments": "TopDeck.gg <3-mo frozen window>"
  },
  "status": "AVAILABLE"
}
```

### 6.2 Observations — how they are captured

Observations are the raw, timestamped records of what happened or was found. Each observation is an object with a `type` discriminator:

| type | captured as | schema |
|---|---|---|
| `decklist` | imported deck (mainboard + commanders + source URL + timestamp) | `{type:"decklist", source_url, mainboard:[{card, qty}], commanders:[...], timestamp}` |
| `card_facts` | one canonical record (name, oracle_id, cmc, color_identity, type, oracle_text, oracle_id) | `{type:"card_facts", card, source:"cards.json", content:{...}}` |
| `legality` | deck_validate result (VALID/INVALID + breakdown) | `{type:"legality", result, verdict}` |
| `tournament_usage` | dated inclusion count from TopDeck.gg | `{type:"tournament_usage", card, source:"TopDeck.gg", count, date_window}` |
| `player_ranking` | CEDHStats entry for a commander | `{type:"player_ranking", commander, source:"cedhstats.org", data:{...}}` |

### 6.3 Measurements — how they are captured

Measurements are **reproducible, deterministic** calculations. Algorithm + result. Schema:

```json
{
  "type": "metric",
  "key": "tutor_density",
  "value": 6,
  "uncertainty": null,
  "algorithm": "count of cards whose oracle text grants card advantage/acceleration",
  "inputs": ["frozen_snapshot", "cards.json"],
  "source": "local computation"
}
```

Metric keys produced (the full set, §7 below):
`tutor_density`, `protection_density`, `combo_density`, `mana_curve`, `castability_stage` (access/cast/assembly/generation/conversion counts), `deck_size`, `color_identity`, `commander_count`.

### 6.4 Context — how it is captured

Context is interpretive material that is NOT authoritative evidence on its own. Types:
- `theory_routing`: which Laya question IDs were selected and why (topic routing).
- `metagame_snapshot`: reference to the frozen 3-month metagame window.
- `primer_claims`: claims extracted from a deck primer (if any), flagged as `CONTEXT` (not `AUTHORITATIVE_TRUTH`).

Each context entry keeps `attribution` — who/when/whatever produced it — so it can be separated from source-authors' positions (per §12 of the design plan).

### 6.5 Evidence hierarchy enforcement

This is where the packet stops being a flat list. Every entry is classified into one of five layers:

1. **AUTHORITATIVE_TRUTH** — current rules, Oracle text, legality, scoped authoritative combo/card records. Source: Academy Ruins rules API + Scryfall oracle text.
2. **OBSERVATIONS** — tournament records, imported decklists, event results, dated source observations. Source: TopDeck, Moxfield, the deck itself.
3. **REPRODUCIBLE_MEASUREMENTS** — counts, densities, simulation results, uncertainty. Source: local computation (deterministic).
4. **CONTEXT** — primers, theory, community discussion, user hypotheses. Source: anywhere.
5. **DECISION_CONCLUSIONS** — recommendations generated through the governed decision process (Jin).

**Rule enforced:** a source being popular or a model being confident must NOT raise its evidence class. A tournament result must not overrule card text. Theory must not substitute for a missing calculation.

Implementation: the packet is stored as a flat array of entries, but each entry carries a `layer` field. Downstream readers (Jin's interpretation, the report generator) filter by `layer` to decide what counts as "evidence" vs "interpretation."

### 6.6 Provenance pointers

Every observation/measurement/context entry carries a `provenance` object:

```json
{
  "card_facts": "cards.json (Scryfall bulk, fingerprint abc123)",
  "rules": "rules_index_academyruins.json (Academy Ruins API, 20261007)",
  "tournaments": "TopDeck.gg /api/v2/tournaments (3-mo frozen, date 2026-10-24)",
  "deck": "snapshot_id (FROZEN)"
}
```

This lets `evidence.trace` and `evidence.against` (Step 13) trace any claim back to its underlying sources and calculations deterministically.

### 6.7 Concrete example (hypothetical)

```json
{
  "packet_id": "ep-audit-x1x2x3",
  "snapshot_id": "audit-2026-10-24T01:15:00Z-3f2a...",
  "observations": [
    {"type":"decklist","source_url":"moxfield.com/decks/abc","timestamp":"2026-10-24T01:14:00Z"},
    {"type":"card_facts","content":{"name":"Mox Field","oracle_id":"abc","cmc":1,"color_identity":"B","oracle_text":"Return target creature from graveyard to battlefield."}}
  ],
  "measurements": [
    {"type":"metric","key":"tutor_density","value":6,"algorithm":"count of cards granting card advantage/acceleration"}
  ],
  "context": [
    {"type":"theory_routing","source":"Laya framework","content":"[Mox Field appears in Q17, Q33]","attribution":"Laya"}
  ],
  "provenance": { "deck": "snapshot-id", "card_facts": "cards.json", "rules": "rules_index_academyruins.json", "tournaments": "TopDeck 3-mo" },
  "status": "AVAILABLE"
}
```

---
## STEP 7 — Deterministic metrics (deck.stats)

**Goal:** produce a set of reproducible, deterministic counts and densities that answer "what is this deck structurally like?" with no LLM involvement.

### 7.1 Common framework

All metrics share a common input: the frozen snapshot + `cards.json` (canonical card facts). The algorithm is:
1. For each card, look up its `color_identity` (WUBRG) and `oracle_text` from `cards.json`.
2. Apply a deterministic classifier (keyword + structural rules) to assign each card to zero or more metric-relevant categories.
3. Aggregate counts into a JSON object.

**No LLM is used for arithmetic.** The Laya framework is used only for question routing in Step 12, not here.

### 7.2 Per-metric algorithm

**7.2.1 Deck size & commanders**
- `deck_size` = mainboard cards + 2 commanders.
- `commander_count` = 2 (hard requirement for cEDH).
- Validate: `deck_validate` (Step 4) returns `VALID` / `INVALID` before metrics are computed.

**7.2.2 Tutor Density**
- Algorithm: count cards whose oracle text contains any tutor/acceleration/acceleration-indicating keyword.
- Keyword set (deterministic, from oracle text patterns): `return`, `draw`, `exile`, `choose one`, `counter`, `sacrifice target`, `which player` (card advantage context), `draw a card`, `shuffle`, `tap` (mana readability, not tutor per se).
- Classification is conservative: a card is a "tutor/acceleration" only if the text explicitly grants card advantage or resource generation.
- Output: integer count.
- Limitation: does not count cards that *would* be tutors if the deck played a specific card (e.g., a tutor card in hand). Those are measurement, not presence.

**7.2.3 Protection Density**
- Algorithm: count cards whose oracle text contains `return` (returning opponent's creature/artifact from graveyard, or protecting a line).
- Keyword set: `return target`, `return ... to battlefield`, `shield`, `put ... into your hand`.
- Output: integer count.
- Distinction: this is protection of a line, not just card draw.

**7.2.4 Combo Density**
- Algorithm: count cards whose oracle text contains combo-enabling keywords.
- Keyword set: `sacrifice`, `when [opponent]`, `[an opponent] sacrifices`, `brings a creature`, `zone`, `target adjacent`, `combat`, `each`, `enters the battlefield`, `become`.
- Classification is structural: a card is counted if it contributes to a combo machinery (not just a one-off effect).
- Output: integer count.
- Limitation: this is a heuristic; "combo potential" requires the simulate step (Step 11) to confirm.

**7.2.5 Mana curve**
- Algorithm: histogram of `cmc` values of mainboard cards (excluding cards with `cmc >= 6` grouped into `5+` bucket).
- Output: `{1: n1, 2: n2, 3: n3, 4: n4, 5+: n5p}`.
- Interpretation: a healthy curve has mass in 1–3, with a tail for 4–5 for late-game pressure.

**7.2.6 Castability stage breakdown** (the most important, most-misunderstood metric)

The framework separates five stages that are often conflated:

| Stage | Definition | Keyword/presence rule |
|---|---|---|
| **access** | The deck can obtain the card (e.g., it's in the deck early, tutor-accessible, or ranked-up). | Card present + (accessible via early card or tutor) |
| **cast** | The card can be legally cast (pays the mana, not countered, legal timing). | Card is castable by turn X under defined rules |
| **assembly** | The card can be assembled with other required cards (all combo pieces in hand + graveyard + battlefield). | All combo pieces present + reachable |
| **generation** | The card produces a resource needed for the win condition. | Card generates mana/resource |
| **conversion** | The resource is converted into a win. | Win condition reachable |

- A card at the "access" stage is NOT at the "cast" stage, and a card "seen by turn 2" is NOT "cast by turn 2."
- Command cards (Commander) are handled specially: if commander timing is not modeled, the whole metric reports `COMMANDER_TIMING: NOT_MODELED` and does not fabricate stage assignments.

**Output:** `{castability_stage: {access: n1, cast: n2, assembly: n3, generation: n4, conversion: n5}, commander_timing: "NOT_MODELED"}`.

### 7.3 Concrete metric computation example

**Deck:** 60-card mainboard + 2 commanders.
- 14 cards have tutor/acceleration keywords → `tutor_density = 14`.
- 5 cards have `return` protection keywords → `protection_density = 5`.
- 8 cards have combo-enabling keywords (`sacrifice`/`when opponent`) → `combo_density = 8`.
- Mana curve: `{1: 12, 2: 20, 3: 18, 4: 8, 5+: 2}`.
- Castability stage: `{access: 14, cast: 22, assembly: 3, generation: 1, conversion: 0}`.
- `commander_timing: "NOT_MODELED"`.

**Judgment from these numbers:** high tutor/protection density but low conversion — the deck has pieces but no proven win condition. The "conversion" stage is 0, which is the strongest signal.

### 7.4 Regression & verification

- Every metric is a pure function of (`frozen_snapshot`, `cards.json`). Given the same inputs, the same outputs.
- Unit tests exist for each keyword classifier (e.g., "return" → protection_density +1, exactly once per card even if keyword appears twice).
- Integration test: run `/audit` on a known deck; the metrics JSON must match a golden value recorded at freeze time.

---
## STEP 9 — Role & package mapping

**Goal:** build the many-to-many relationship graph: card→package, card→combo, card→resource, card→matchup. Each edge carries evidence, confidence, provenance, and conditions.

### 9.1 Role classification system

Roles are multi-label (a card can have multiple). The role set (deterministic, from keyword + structural analysis):

| Role label | What it means | Detection |
|---|---|---|
| `card_advantage` | Returns the opponent's card (recall/tutor) | oracle `return`, `draw`, `exile` |
| `card_destruction` | Removes opponent's cards | `destroy`, `sacrifice target` (to opponent) |
| `card_search` | Finds missing cards | `search`, `dig`, `look at` |
| `protection` | Protects a line from removal | `return ... to battlefield/committee` |
| `resource_generation` | Produces mana or a resource | `mana`, `tap`, `activate` |
| `card_draw` | Gains a card | `draw`, `upkeep` |
| `discard` | Removes your own cards | `discard` |
| `sacrifice` | Sacrifices for value | `sacrifice` |
| `damage` | Direct damage | `damage`, `combat damage` |
| `land` | Mana base | `land` type |
| `command` | Commander-specific action | `command` keyword |
| `UNCLASSIFIED` | No detectable role | — |
| `UNRESOLVED` | Evidence insufficient | — |

### 9.2 Role assignment algorithm

1. For each card, fetch `oracle_text` (canonical) from `cards.json`.
2. Apply a rule engine (deterministic priority):
   - If `type_line` contains `Land` → `{land}`.
   - If oracle contains `sacrifice` → `{sacrifice, card_destruction}` (sacrifice is a kind of card destruction).
   - If oracle contains `return` or `draw` or `exile` → `{card_advantage}` (plus `card_draw` if `draw`).
   - If oracle contains `return target` or `shield` or `put ... into your hand` → `{protection}`.
   - If oracle contains `draw a card` or `upkeep` → `{card_draw}`.
   - If oracle contains `counter` or `draw` → `{card_advantage}`.
   - If oracle contains `graveyard` + `battlefield` + `sacrifice` → `{card_destruction, card_advantage}`.
   - Default → `{UNCLASSIFIED}`.
3. Store each role assignment with `evidence` (the matching oracle text quote), `confidence` (deterministic: 0.95 for direct oracle support; 0.7 for structural inference; `null` for unresolved), and `provenance` (source: `cards.json`, rule number if applicable).

### 9.3 Relationship graph (card→card, card→package)

The graph is the heart of the analysis. Edges are typed and carry evidence + confidence + conditions.

| Edge type | Meaning | Detection |
|---|---|---|
| `supports_package` | This card is a member of a named package (e.g., "Boros Energy") | Deck composition + theme matching (keyword/role cluster) |
| `enables_combo` | This card is required for a combo line | Analysis of combo requirements (Step 8) vs deck composition |
| `converts_resource_to_win` | This card turns a resource (mana, card advantage) into a win | Win-condition card + resource supply card detection |
| `protects_a_line` | This card protects a critical line (e.g., the only combo piece) | Combo piece + protection role co-occurrence |
| `shares_resource` | This card shares a resource with another card/package | Resource role co-occurrence (e.g., both produce mana) |
| `overlaps_two_roles` | This card bridges two distinct roles | Role set > 1 with cross-role synergy |
| `is_redundant` | This card is redundant with another under specified conditions | Two cards with identical (or near-identical) roles + oracle text overlap |
| `matchup_specific` | This card matters only against a specific opponent line | Metagame threat matrix (Step 10) + deck analysis |

**Edge schema (per edge):**
```json
{
  "card_a": "Mox Field",
  "card_b": "Laplace the Enigma",
  "type": "supports_package",
  "target_package": "Boros Energy",
  "evidence": "Mox Field: 'Return target creature...' + Laplace: 'synergy' (oracle text)",
  "confidence": 0.9,
  "provenance": "cards.json (oracle text)",
  "conditions": "when opponent plays creatures"
}
```

### 9.4 How edges are derived (deterministic, example)

- `supports_package`: the skill clusters the deck's cards by theme (commission + role cluster). If the cluster has ≥ 3 cards with the same color + a shared resource mechanic, it's tagged as a package; members get `supports_package` edges.
- `enables_combo`: from Step 8's confirmed combo lines, the skill computes the required-piece set. Any deck card in that set gets an `enables_combo` edge to the combo line ID.
- `converts_resource_to_win`: the win condition (e.g., "all creatures die" or "draw 3 cards") is identified. Any card whose role supplies the resource needed for that win gets `converts_resource_to_win` edges to the win condition ID.
- `protects_a_line`: if a card is a combo piece AND a protection card, the skill flags it as `protects_a_line` for that combo line.

### 9.5 UNCLASSIFIED / UNRESOLVED handling

- Cards with no detectable role → `UNCLASSIFIED` with `confidence: null`. NOT omitted. NOT forced into a role.
- Edges with weak or conflicting evidence → `confidence: null` + `UNRESOLVED`. The edge exists, but it's flagged as unresolved.
- These keep the audit honest: an unknown is better than a fabricated classification.

### 9.6 Concrete output example

```json
{
  "roles": [
    {"card": "Mox Field", "roles": ["card_advantage", "card_destruction"], "evidence": "'Return target creature...'"},
    {"card": "Sphinx of Night's Dream", "roles": ["protection", "card_advantage"], "evidence": "shield, return"}
  ],
  "packages": [
    {"package": "Boros Energy", "members": ["Mox Field", "Laughing Breath", "Pyroclasm"], "shared_resource": "mana", "confidence": 0.85}
  ],
  "relationships": [
    {"card_a": "Mox Field", "card_b": "Boros Energy combo", "type": "enables_combo", "target_combo_id": "combo-001", "evidence": "Mox Field returns creatures; combo line requires creature recall", "confidence": 0.9}
  ]
}
```

---
## STEP 10 — External checks (metagame layer + tournament evidence)

**Goal:** build a frozen, date-stamped 6-month metagame layer and query dated tournament usage, so deck analysis is grounded in observed competitive data rather than assertion.

### 10.1 What the metagame layer actually is

Per the design plan, the metagame layer is **a defined snapshot, not an assumption that every source has complete coverage.** It is frozen date-stamped. Its outputs:

| Output | What it establishes |
|---|---|
| **cohorts** | Which lists belong to the same relevant commander/archetype group (e.g., "Boros Energy", "Kraum/Tymna", "5-color") |
| **card prevalence** | How frequently each card appears within the cohort (not proof of necessity) |
| **package prevalence** | Which packages and package combinations appear together |
| **threat matrix** | Which opposing strategies and win conditions are relevant to the target deck |
| **regressions log** | Findings, corrections, repeated failure patterns across audits |

### 10.2 Data sources & tools

| Source | Tool / endpoint | Local artifact |
|---|---|---|
| **TopDeck.gg** | `https://topdeck.gg/api/v2/tournaments` (REST, `Authorization: <TOPDECK_GG_API_KEY>` from `TOPDECK_GG_API_KEY.txt`) | `config/topdeck_all_tournaments.json` (10,124 tournaments, 23.5 MB) + `tournaments/<TID>.json` (8,874 archived) |
| **CEDHStats.org** | `https://cedhstats.org/players` (ranked player data) | `cedhstats/player_rankings.json` (300 players parsed) |
| **CEDHData** | metagame layer (cohorts, prevalence, threat matrix) | `C:\Users\Main\Desktop\project front gate\Projects\Codie\Research\CedhStats\` |

### 10.3 Frozen 6-month window mechanism

The metagame layer is NOT a live query of "all time." It is a **frozen date
window** (extended from 3 months to 6 months to fix the 90-day lapse):

1. **Snapshot definition:** `date_window = "2026-04-24 to 2026-10-24"` (the
   most recent 6 months, frozen at audit time).
2. **Collection:** `topdeck_collect_all.py` fetches tournaments in batches
   (50 TIDs per request), sleeping between batches to avoid 429. Saved to
   `config/topdeck_all_tournaments.json`.
3. **Archiving:** each tournament saved as `tournaments/<TID>.json`.
4. **Query:** the audit script reads `config/topdeck_all_tournaments.json`,
   filters to tournaments in the frozen window, extracts commander entries,
   card inclusions, and package co-occurrences.
5. **Recompute:** the window is recomputed **monthly** (the 1st of each
   month). A stale window (>30 days without a recompute) must be reported as
   `PARTIAL (stale window)`, never silently dropped.

**Rolling refresh protocol (fixes the 90-day lapse):**

### 10.4 What `tournament_usage` returns for a deck

The query asks: "which cards from this deck appear in the frozen-window cohort, and how often?"

```json
{
  "date_window": "2026-07-24 to 2026-10-24",
  "cohort": "BZ (Boros Energy)",
  "card_prevalence": {
    "Mox Field": {"inclusion": 412, "total_decks": 2940, "pct": 14.0, "source": "TopDeck.gg"},
    "Laplace the Enigma": {"inclusion": 356, "total_decks": 2940, "pct": 12.1},
    "Pyroclasm": {"inclusion": 289, "total_decks": 2940, "pct": 9.8}
  },
  "package_prevalence": {
    "Boros Energy": {"pkg": "Boros Energy", "coocurrence": 210, "shared_resource": "mana"}
  },
  "threat_matrix": ["Enemy package Z (Naya)", "Battlefy line (Tokumei)", "Hard counters (Jund)"],
  "data_quality": {"total_decks": 2940, "note": "small biased sample; prevalence ≠ causal"}
}
```

### 10.5 Threat matrix construction

The threat matrix is built by:
1. Analyzing the target deck's color identity + strategy (from Step 9 roles + Step 7 metrics).
2. Querying the frozen-window cohort for the most common opposing strategies (e.g., "Naya streaks", "Battlefy midrange", "Jund midrange").
3. Matching the target deck's weak points (e.g., low protection density → vulnerable to removal) against the opponent's strongest lines.
4. Outputting the threat matrix as a list of "opposing strategy + win condition + relevance to target."

Example output: `[{"opponent": "Naya streak", "win_condition": "kill on gust", "relevance": "high", "evidence": "14% of BZ decks face Naya; target has protection_density 5 vs Naya's 3"}]`.

### 10.6 CEDHStats.org usage

- Player rankings (100 players of 300 parsed) are used as **context** for deck analysis (e.g., "Krau/Tymna is the #1 ranked in the window").
- This is **not** tournament data; it's player rankings (entries, PPG, top cut %, floor, veterans, ceiling).
- Stored in `cedhstats/player_rankings.json` (143 KB). The audit code reads it for context entries only, not as authority.

### 10.7 Failure & degradation

| Failure | Handling |
|---|---|
| TopDeck 429 rate limit | Retry with `TOPDECK_GG_API_KEY.txt`; sleep 10s between batches |
| CEDHStats partial | Use `player_rankings.json` (300 players); mark `PARTIAL` in report |
| Missing tournament window | Report `metagame: PARTIAL (stale window; no local data within the 6-month frozen window)`; fall through to Tier 2 (thinner available local data). Do NOT drop to `UNSUPPORTED`. |
| Small biased sample | Report `data_quality: small biased sample`; separate "common in observed cohort" from "demonstrably improves this deck" |

---
## STEP 11 — Castability simulation (optional)

**Goal:** determine whether the deck can actually cast its key cards, at defined stages, under a frozen baseline. This is NOT a general-purpose simulator; it is a narrowly defined castability experiment tool.

### 11.1 Preserved constraints

Per the design plan, these are non-negotiable:
- **Optimization objective:** castability.
- **Canonical storage:** files.
- **Simulator integration:** browser (Deckcipher).
- **Broader scope:** deferred until decisions made.

### 11.2 Experiment definitions (must not be conflated)

The first experiments distinguish three things:

| Experiment | Question | Rule |
|---|---|---|
| **Cast by turn X** | Can the deck actually pay the costs and cast the target? | Card is castable by turn X under defined rules + mulligan |
| **In hand by turn X** | Has the target entered the player's hand? | Target present in hand at turn X |
| **Seen/accessed by turn X** | Has the target become accessible under a clearly defined rule? | Target is in hand or accessible (e.g., tutor-accessible) by turn X |

**Critical:** a card "seen by turn 2" is NOT "cast by turn 2." A card that is tutor-accessible is NOT necessarily in hand. These must be measured separately.

### 11.3 Deckcipher integration

- Simulator: **Deckcipher** (browser-based).
- Integration point: the audit skill calls Deckcipher via a browser automation (the skill's `browser-sim-controls.md` reference).
- The deck + modifier + experiment parameters are passed to Deckcipher; results returned as structured JSON.

### 11.4 Experiment record schema

Each experiment is recorded with full provenance:

```json
{
  "experiment_id": "cast-001",
  "objective": "cast Mox Field by turn 3",
  "baseline_deck_sha256": "abc123...",
  "modification": "none (frozen baseline)",
  "mulligan_policy": "keep 10-15, 60-card mainboard, 2 commanders",
  "turn_one_draw": "2 cards (default)",
  "opponent_mana": "random (average 5)",
  "sample_size": 5000,
  "random_seed": 12345,
  "results": {
    "cast_by_turn_3": {"pct": 0.34, "count": 1700, "uncertainty": "±0.02"},
    "in_hand_by_turn_3": {"pct": 0.28, "count": 1400},
    "seen_by_turn_2": {"pct": 0.91, "count": 4550}
  },
  "commander_timing": "NOT_MODELED",
  "status": "COMPLETE"
}
```

**Defaults:** Policy mode, 5,000 games, minimum keep of 5 (where supported). Random seed recorded for reproducibility.

### 11.5 What changes the castability numbers

The skill computes how each decision (cut a card vs keep, add a tutor, change mulligan policy) affects castability. The metric `castability_stage` (Step 7) is the baseline; the simulator measures the delta.

**Mutations are staged** (Step 8 of design plan):
1. Select target weakness (e.g., low `castability_stage.cast`).
2. Identify eligible slots + constraints (e.g., "tutor into Mox Field").
3. Generate candidate substitutions.
4. Validate each candidate deck (Step 4 legality).
5. Compare every candidate vs the same frozen baseline (5,000 games each).
6. Run measurements (count castable-by-turn-X).
7. Rank changes by observed effect, uncertainty, opportunity cost.
8. Examine strongest alternatives for package damage or regressions.
9. Present to human review.
10. Save experiment + outcome without auto-changing the canonical deck.

### 11.6 COMMANDER_TIMING: NOT_MODELED

- Commander timing is the hardest part to model (commander can activate only once per turn).
- If Deckcipher/analysis cannot model it, the experiment **must** report `COMMANDER_TIMING: NOT_MODELED`.
- It must NOT silently produce a cast-time (that would be over-claiming). The simulation stops that experiment and reports the limitation.

### 11.7 Failure & degradation

| Failure | Handling |
|---|---|
| Deckcipher not available in browser | Report `SIMULATOR_UNAVAILABLE`; use `deck.stats` stage metrics as proxy; note in report |
| Miscalculated mulligan policy | Record the policy used; do not assume a "standard" policy |
| Seed not supported | Record `random_seed: null`; results are still valid but not bit-reproducible |

---
## STEP 12 — Theory application

**Goal:** route the audit question to the few frameworks that materially improve the analysis (topic routing, not author fame), apply them independently, and preserve disagreements.

### 12.1 Topic routing vs author fame

The older design routed questions by "which theorist is famous/associated." The rebuilt design routes by **what the question actually is**:

| Question type | Framework(s) selected |
|---|---|
| "How do I accelerate / draw faster?" | Card-evaluation + resource-conversion frameworks |
| "Why is this card protective?" | Card-evaluation + role-assignment frameworks |
| "Is this deck too resource-heavy?" | Resource conversion + deck cohesion frameworks |
| "Which commander is over-specialized?" | Commander dependency + stax asymmetry frameworks |
| "How do I improve castability?" | Resource conversion + data-driven cEDH development |

The router selects the few frameworks that **materially improve** the current audit — not every framework.

### 12.2 Claim-level attribution

Each framework's claim is attributed at a level (per `external-tool-review.md`):

| Level | Meaning | Example |
|---|---|---|
| 1. Direct theory | Attributed to the source | "Mox Field is a tutor" (source: Zvi Mowshowitz) |
| 2. Later synthesis | Framework author's synthesis | "Tutors work best at 1–5 CMC" (Marshall Sutcliffe) |
| 3. Jin inference | Derived by Jin from evidence | "This deck has 6 tutors + low conversion → acceleration first" |
| 4. Format translation | Historical Standard/Legacy/Vintage/Limited theory applied to cEDH (requires explicit explanation) | "4-color synergies from Standard don't apply 1:1 to cEDH" |
| 5. Empirical support | Deck observation supports the framework | "This deck's tutor-heavy curve matches framework prediction" |
| 6. Empirical conflict | Deck observation contradicts the framework | "This deck has low tutor density but wins via combo" |
| 7. Unresolved | Insufficient evidence | "Does this card favor the mirror?" |

### 12.3 Independent framework analysis

Before comparing conclusions, each applicable framework evaluates the evidence independently:

1. Framework A analyzes the deck against its theory.
2. Framework B analyzes the deck against its theory.
3. Only then are conclusions compared.

**Rule:** independent analysis before comparison. Frameworks are not allowed to read each other's conclusions first.

### 12.4 Disagreement preservation

Definitional, contextual, empirical, and format-specific disagreements are kept visible. Examples:
- "Jax vs Sparrow" (definitional disagreement about card value).
- "Resource conversion is king" vs "resource conversion is context-dependent" (contextual).
- "Tutors improve win rate" vs "tutors without conversion don't" (empirical).

These are recorded in the packet's `context` array with `attribution` and a `disagreement_type` field.

### 12.5 Format translation gate

Historical Standard/Legacy/Vintage/Limited theory must NOT be applied to cEDH without an **explicit explanation gate**:

- The translation must name *which* historical rules/theory are being applied.
- The translation must state *why* it applies (or doesn't) to cEDH.
- If the translation is uncertain, it's marked `CONTEXT` (not `AUTHORITATIVE_TRUTH`).

Example: "Standard's 4-color synergy patterns from the 'Boros' meta do not transfer 1:1 to cEDH because commander availability and mana base differ. This is a CONTEXT claim, not authoritative."

### 12.6 Theory-to-evidence links

The framework must show which actual deck observations support or contradict the framework:

| Framework claim | Deck observation | Support / Conflict |
|---|---|---|
| "Tutors improve acceleration" | Deck has tutor_density 6 | SUPPORT |
| "Conversion is necessary for tutors to matter" | deck.castability_stage.conversion = 0 | CONFLICT |
| "Protection density prevents curve collapse" | deck.protection_density 5 | SUPPORT (weak) |

This makes the theory audit evidence-based, not assertion-based.

### 12.7 Personal conclusions separated from source authors

The deck's analysis conclusions are stored **separately** from source authors' positions:

```json
{
  "source_claim": "Tutors are strong (Mowshowitz, quoted)",
  "deck_conclusion": "This deck should prioritize acceleration first, because conversion=0 (evidence: castability_stage)",
  "attribution": "deck_conclusion (Jin)",
  "disagreement": "Source claims tutors alone win; deck_conclusion says conversion is the blocker"
}
```

The report generator separates these. The user sees: "Here's the source's claim. Here's what our deck evidence says. Here's the conflict."

### 12.8 Source freshness vs durable strategic principles

- **Source freshness** (dates, current metagame examples) is kept separate from **durable strategic principles**.
- A framework is labeled `FRESH` if its claims depend on the current window (e.g., "Naya streaks matter now").
- A framework is labeled `DURABLE` if its claims persist across windows (e.g., "conversion is necessary for tutors").
- The report marks `FRESH` claims as dated; `DURABLE` claims as timeless.

### 12.9 Retention modes

The theory layer supports four analysis modes:

| Mode | What it does |
|---|---|
| **Automatic analysis** | Router selects frameworks; results aggregated |
| **Explicit framework/lens** | User pins a specific framework (e.g., "analyze with resource conversion") |
| **Topic council** | Multiple frameworks analyze independently; conclusions compared |
| **Debate mode** | Selected frameworks independently analyze; produce a neutral disagreement map |

### 12.10 Concrete theory application example

**Deck:** tutor-heavy, low conversion.
- **Router selects:** Card-evaluation + resource-conversion + data-driven cEDH.
- **Framework 1 (resource conversion):** "Tutors need conversion to win." Observation: `castability_stage.conversion = 0`. → **CONFLICT**.
- **Framework 2 (card evaluation):** "Tutors grant card advantage." Observation: `tutor_density = 6`. → **SUPPORT**.
- **Conclusion:** Tutors are present but conversion is the blocker. Recommendation: prioritize conversion before cutting tutors. (Found via `evidence.against` — counterevidence: "tutors alone don't win".)

---
## CONSOLIDATED OUTPUT SHAPE

All six steps produce, at the end of an `/audit`, one in-memory + persisted evidence object:

```
evidence_packet.json   (Step 6)
metrics.json           (Step 7)
roles_packages.json    (Step 9)
metagame.json          (Step 10)
castability_experiment.json (Step 11, optional)
theory_attribution.json (Step 12)
+ final report (Step 15)
```

Every artifact is file-backed (frozen snapshot + provenance), deterministic (except where flagged UNRESOLVED/NOT_MODELED), and traceable to sources.

---
## FAILURE & DEGRADATION SUMMARY (steps 6–12)

| Step | Failure | Degradation |
|---|---|---|
| 6 | Missing source (e.g., no rules index) | Mark `status: PARTIAL`; continue with available layers |
| 7 | Metric classifier ambiguous | Flag `UNRESOLVED`; use conservative estimate |
| 9 | No role detected | `UNCLASSIFIED` (not omitted); edge confidence `null` |
|| 10 | Full 6-month frozen window missing | `metagame: PARTIAL (stale window; last recomputed <date>)`; continue with the most recent available local data, or fall through to Tier 2. Do NOT silently drop to `UNSUPPORTED`. |
| 11 | Deckcipher unavailable | Use `deck.stats` proxy; note `SIMULATOR_UNAVAILABLE` |
| 12 | No framework materially improves | Router returns `theory: UNSUPPORTED`; report notes it |

---
*Deep dive on Steps 6, 7, 9, 10, 11, 12 — from design plan `NEBULA-DESIGN-PLAN.md`, implemented via codie-audit skill v0.8.0. Nothing is locked until the user chooses.*
