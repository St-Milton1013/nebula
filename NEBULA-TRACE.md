# NEBULA — SKILL-INVOKING — ULTRA-DETAILED TRACE (step by step, with sites & tools)

**Format:** one row per step — what happens, which site/tool, when, where files are written.
**Goal:** someone reading this can reproduce the exact execution path, tool by tool, site by site.
**Convention:** local paths are Windows-style; MSYS path `C:\Users\Main\Desktop\...` === absolute Windows path.

> Pre-flight state (verified): codie-audit skill v0.8.0, **codieaudit profile** (`C:\Users\Main\AppData\Local\hermes/profiles/codieaudit/skills/codie-audit/`). Active chat repo: `nebula/`. Codie source of truth: `project front gate/Projects/Codie/`. Deck source of truth for card truth: `project front gate/Projects/Codie/nodes/00_CardTruth/cards.json`. Rules index: `project front gate/Projects/Codie/rules/rules_index_academyruins.json`.

---
## Master trigger

User opens the chat and types:

```
/audit https://www.moxfield.com/decks/abc123 (or an Archidekt URL)
```

The slash command is routed to the **codie-audit skill** (active profile = codieaudit v0.8.0). The skill immediately loads five runtime contracts from its reference set:
- `runtime-contract.md` — the /audit execution contract
- `analytical-contract.md` — the analytical phase contract
- `corpus-manifest.md` — which corpus parts are authoritative
- `evidence-packet.md` — the evidence object schema
- `external-tool-review.md` — which external tools (TopDeck/CEDHStats/CEDHData) are in scope

It also parses the argument: `deck_url` (required) + optional `[focus]`.

---
## STEP 1 — Scope resolution

**What happens:** the skill resolves the deck source and the target question.

**Tool / site used:**
- **Moxfield** — `https://www.moxfield.com/decks/<id>`; fetched via `mcp__mtg_unified__moxfield_deck_info` + `mcp__mtg_unified__moxfield_decklist` (bypasses Cloudflare).
- **Archidekt** — `https://archidekt.com/decks/<id>`; fetched via `mcp__mtg_commander__get_archidekt_deck` as the fallback when Moxfield fails.
- The skill itself routes: URL pattern `moxfield.com/decks/` → Moxfield; `archidekt.com/decks/` → Archidekt.

**Input:** the URL + optional `[focus]` (e.g., "evaluate the tutor card" or "is this card a good cut?").

**Output:** `scope = { source: "moxfield", deck_id, commanders: [...], format: "cEDH", focus: null }`.

**Where:** in the skill's runtime context (no file written yet).

---
## STEP 2 — Deck ingestion

**What happens:** the deck is fetched and parsed into a raw decklist.

**Tool / site used:**
1. `mcp__mtg_unified__moxfield_deck_info` (Moxfield) — retrieves deck metadata (name, format, author, dates).
2. `mcp__mtg_unified__moxfield_decklist` (Moxfield) — retrieves the full decklist (mainboard + sideboard + commanders).
3. If Moxfield down: `mcp__mtg_commander__get_archidekt_deck` (Archidekt) — retrieves decklist via `https://archidekt.com/decks/<id>`.

**Input:** the deck URL.

**Output (raw):**
- `mainboard`: array of `{card_name, quantity}`
- `commanders`: array of `{card_name, quantity}`
- `sideboard`: (optional) array
- source URL + timestamp

**Files written:** none yet (in-memory).

**Failure mode:** Cloudflare block on Moxfield → falls back to Archidekt (graceful degradation; the skill logs which source was used).

---
## STEP 3 — Canonical card facts (cards.json)

**What happens:** every card name is resolved to its canonical record. This is where **oracle_id identity** (ADR-001) is enforced — double-faced cards, face-down cards, and paired commanders are resolved correctly.

**Tool / site used:**
- **Scryfall** — bulk card store: `https://api.scryfall.com/bulk-data/cards` (cached locally as `C:\Users\Main\Desktop\project front gate\Projects\Codie\nodes\00_CardTruth\cards.json`).
- The local `cards.json` (59.9 MB) is the canonical card-truth store; the skill looks up each card by name (and `oracle_id` where needed).

**Input:** raw card names from Step 2.

**Output (per card):**
- `name` (canonical)
- `mana_cost`, `cmc`, `color_identity`
- `type_line`, `oracle_text`
- `oracle_id` (ADR-001 identity key)
- `colors` (from color identity, resolved to WUBRG)
- `power`, `toughness`
- `edhrec_rank` (for metagame context)
- `collector_number` / `set` (for variant tracking)

**Files written:** none yet.

**Failure mode:** card not in `cards.json` → the skill flags `CARD_NOT_RESOLVED` and uses `mcp__mtg_unified__scryfall_search_cards` (online) to fill the gap, but marks the resolution as `PARTIAL_UNVERIFIED`.

---
## STEP 4 — Deck validation (legal construction)

**What happens:** the deck is checked against Commander construction rules — size, color identity, banned cards, singleton rules.

**Tool / site used (MCP servers):**
1. `mcp__mtg_unified__deck_validate` — Commander format validation (deck size, color identity, banned cards, singleton rules). Input: the frozen mainboard + commanders.
2. `mcp__mtg_unified__bulk_ban_list` — Commander ban list (banned + restricted) for a comprehensive check.
3. `mcp__mtg_commander__validate_deck` — Commander-specific validation as a secondary pass.

**Input:** the canonical snapshot (from Step 2/3).

**Output:**
- `VALID` / `INVALID` with actionable errors (e.g., "too many cards", "color identity mismatch", "banned card X").
- `calculation: { total_cards: 100, commanders: 2, color_identity: "BUG", singletons_ok: true }`

**Files written:** none yet.

**Failure mode:** INVALID deck → the skill **stops** with a clear error. It does not proceed to an audit of an illegal deck (the read-only boundary: "read-only analysis until a human accepts a proposed change").

---
## STEP 5 — Freeze input (gazette)

**What happens:** the deck snapshot is written to the Frontgate vault as a frozen, hashed, timestamped artifact. This is the provenance anchor for everything after.

**Tool / site used:**
- **Frontgate vault** — the canonical, persistent, link-first storage for private deck + vault data. Local-write path: `C:\Users\Main\Desktop\project front gate\Projects\Codie\` (the codie vault).
- The skill's `evidence-packet.md` contract defines the snapshot schema.

**Input:** raw decklist, resolved card facts, source URL, timestamp.

**Output file (frozen snapshot):**
`C:\Users\Main\Desktop\project front gate\Projects\Codie\sessions\audit-<timestamp>-<hash>.json`

Schema (per `evidence-packet.md`):
```json
{
  "snapshot_id": "audit-2026-10-24T01:15:00Z-<sha256>",
  "source": "moxfield|archidekt",
  "deck_url": "https://...",
  "timestamp_utc": "2026-10-24T01:15:00Z",
  "mainboard": [{"card_name": "...", "quantity": 4, "oracle_id": "..."}],
  "commanders": [{"card_name": "...", "quantity": 1, "oracle_id": "..."}],
  "format": "cEDH",
  "color_identity": "BUG",
  "fingerprint_sha256": "abc123...",
  "status": "FROZEN"
}
```

**Files written:** the frozen snapshot JSON.

**Failure mode:** hash collision (practically impossible) → re-fingerprint. Vault write error → logged, then retry once.

---
## STEP 6 — Evidence packet build

**What happens:** the canonical evidence object is assembled from observations + measurements + context.

**Tool / site used:**
- **Local files:** `cards.json` (card truth) + `rules_index_academyruins.json` (rules index, from the Academy Ruins API).
- The skill's `evidence-packet.md` schema defines the packet structure.

**Evidence hierarchy enforced (per `external-tool-review.md`):**
| Layer | What it establishes |
|---|---|
| Authoritative truth | Current rules, Oracle text, legality, scoped authoritative combo/card records |
| Observations | Tournament records, imported decklists, event results |
| Reproducible measurements | Counts, densities, package relationships, simulation results |
| Context | Primers, theory, community discussion, user hypotheses |
| Decision conclusions | Recommendations produced through the governed decision process |

**Output (evidence packet):**
```json
{
  "packet_id": "ep-<snapshot_id>",
  "snapshot_id": "...",
  "observations": [
    {"type": "decklist", "source_url": "...", "cards": [...], "timestamp": "..."},
    {"type": "card_facts", "card": "...", "source": "cards.json"}
  ],
  "measurements": [
    {"type": "count", "key": "tutor_density", "value": 6, "uncertainty": null},
    {"type": "count", "key": "protection_density", "value": 5, "uncertainty": null}
  ],
  "context": [
    {"type": "theory_routing", "laya_question_ids": ["..."]}
  ],
  "provenance": {
    "cards": "cards.json (Scryfall bulk, hashed fingerprint)",
    "rules": "rules_index_academyruins.json (Academy Ruins API)",
    "deck": "snapshot_id (frozen)"
  },
  "status": "AVAILABLE"
}
```

**Files written:** the evidence packet JSON is **kept in memory** (not yet written to disk) — it is the input to Jin's interpretation. It is written to disk at the final report stage.

---
## STEP 7 — Deterministic metrics (deck.stats)

**What happens:** reproducible counts and densities are computed. **No LLM is used for arithmetic.**

**Tool / site used:**
- **Local computation** over the frozen `cards.json` + snapshot + evidence packet.
- The codie-audit skill's own metric pipeline (the 70-question Laya framework is used only for *question routing*, not for these deterministic counts).

**Metrics computed:**
- **Tutor Density** (cards that give you the next thing): count of cards whose oracle text grants card advantage or acceleration.
- **Protection Density** (cards that protect a line): count of cards that return an opponent's removed card / prevent removal.
- **Combo Density** (cards that enable combo): count of cards that enable combo lines.
- **Package prevalence:** which named packages appear and how often.
- **Mana efficiency:** cards-per-mana distribution curve.
- **Castability stage breakdown:** access → cast → assembly → generation → conversion (stage-specific counts, where a card at the "access" stage is NOT counted as "cast").

**Output:**
```json
{
  "metrics": {
    "tutor_density": 6,
    "protection_density": 5,
    "combo_density": 8,
    "mana_curve": {"1": 12, "2": 20, "3": 18, "4": 8, "5+": 4},
    "castability_stage": {"access": 14, "cast": 22, "assembly": 3, "generation": 1, "conversion": 0},
    "commander_timing": "NOT_MODELED"
  },
  "source": "local computation (deterministic)"
}
```

**Files written:** none (computed in-memory, then consumed by the report stage).

**Failure mode:** a card can't be assigned a stage (e.g., commander-timing-specific analysis) → reported as `COMMANDER_TIMING: NOT_MODELED` (no fabricated stage).

---
## STEP 8 — Combo & commander interaction verification

**What happens:** confirmed combo lines + required pieces, and possible/incomplete lines (marked as hypotheses). Commander interactions verified.

**Tool / site used:**
1. `mcp__mtg_unified__spellbook_find_combos` — returns known combos for specific cards (e.g., "Sol Ring").
2. `mcp__mtg_unified__spellbook_find_decklist_combos` — returns combos present in or nearly present in the decklist.

**Input:** the frozen snapshot + canonical card facts (oracle text / keywords like `summon`, `sacrifice`, `exile`, `mill`).

**Output:**
```json
{
  "confirmed_combos": [
    {"line": "Sol Ring → Blink Mox → card X", "required_pieces": ["Sol Ring", "Blink Mox"], "confidence": 0.9, "evidence": "oracle text + rules 702.19"}
  ],
  "hypotheses": [
    {"line": "...", "status": "PARTIAL", "missing": ["card Y"], "note": "incomplete line, needs player ability"}
  ],
  "commander_interactions": [{"type": "teamwork", "cards": ["A", "B"], "note": "both commanders contribute to same effect"}]
}
```

**Files written:** none yet.

---
## STEP 9 — Role & package mapping (deck.roles, deck.packages, deck.relationships)

**What happens:** the many-to-many relationship graph is built. No forced roles; `UNCLASSIFIED`/`UNRESOLVED` is first-class.

**Tool / site used:**
- Local computation over `cards.json` + the evidence packet (the skill's role-graph builder).
- The codie-audit skill's `deck.roles` / `deck.packages` / `deck.relationships` contracts define the output schema.

**Output (per contract):**
```json
{
  "roles": [
    {"card": "...", "role": "card_advantage", "evidence": "returns opponent's card", "confidence": 0.95, "provenance": "oracle text"},
    {"card": "...", "role": "UNCLASSIFIED", "note": "insufficient evidence", "confidence": null}
  ],
  "packages": [
    {"package": "X", "members": ["..."], "dependency": "...", "conversion_path": "..."},
    {"package": "Y", "members": ["..."], "cross_resource": true}
  ],
  "relationships": [
    {"card_a": "...", "card_b": "...", "type": "supports_package", "target_package": "X", "evidence": "...", "confidence": 0.9, "conditions": "when opponent can't return mana"}
  ]
}
```

**Failure mode:** a card has no determinable relationship → `UNCLASSIFIED` (not omitted). An edge's evidence is weak → `confidence: null` + `UNRESOLVED` flag.

---
## STEP 10 — External checks (metagame layer + tournament evidence)

**What happens:** builds the frozen 3-month metagame layer and queries dated tournament usage.

**Tool / site used:**
1. **TopDeck.gg** — API `https://topdeck.gg/api/v2/tournaments` (with `Authorization: <TOPDECK_GG_API_KEY>` from `C:\Users\Main\Desktop\TOPDECK_GG_API_KEY.txt`). Frozen 3-month snapshot: `config/topdeck_all_tournaments.json` (10,124 tournaments) + `tournaments/<TID>.json` (8,874 archived).
2. **CEDHStats.org** — `https://cedhstats.org/players` — player rankings (100 players of 300 parsed into `cedhstats/player_rankings.json`).
3. **CEDHData** — metagame layer (cohorts, card prevalence, package prevalence, threat matrix). Source: `C:\Users\Main\Desktop\project front gate\Projects\Codie\Research\CedhStats\`.
4. **Deckcipher** — browser-based castability simulator (castability simulation, §11).

**Input:** the frozen snapshot + the 3-month frozen metagame snapshot.

**Output:**
```json
{
  "metagame": {
    "cohorts": ["BZ", "Boros Energy", "Kraum/Tymna"],
    "card_prevalence": {"Mox Field": 412, "Laplace the Enigma": 356},
    "package_prevalence": {"Boros Energy": {"Vizier of Alembick": 210}},
    "threat_matrix": ["Enemy package Z", "Battlefy line"],
    "date_window": "2026-07-24 to 2026-10-24"
  },
  "tournament_usage": {
    "Mox Field": {"inclusion": 142, "byes": null, "source": "TopDeck.gg (3-mo frozen)"}
  }
}
```

**Failure mode:** TopDeck rate-limited → retry with `TOPDECK_GG_API_KEY.txt` (36-byte key file) using the slow rate (10s between requests, per `topdeck_integration.py` conventions). CEDHStats partial → use cached `player_rankings.json` (300 players) and mark `PARTIAL`.

---
## STEP 11 — Castability simulation (optional — if requested)

**What happens:** narrowly defined castability experiments against a frozen baseline. This is **not** a general-purpose simulator.

**Tool / site used:**
- **Deckcipher** — browser-based simulator (`https://cedhdata.com/deckcipher` or similar). Canonical storage: files.
- The codie-audit skill's simulator contract defines the experiment scope (Policy mode, 5,000 games, min keep 5, turn-one draw, opponent-mana assumptions, seed, lines).

**Experiment definitions (must not be conflated):**
- **Cast by turn X** — can the deck pay the costs and cast the target?
- **In hand by turn X** — has the target entered the player's hand?
- **Seen/accessed by turn X** — has the target become accessible under a clearly defined rule?

**Metrics recorded (per experiment):**
- baseline (frozen deck)
- exact modification
- mulligan policy
- turn-one draw assumption
- opponent-mana assumptions
- sample size
- random seed (when supported)
- results
- uncertainty
- representative sample lines
- `COMMANDER_TIMING: NOT_MODELED` (if commander timing untimed)

**Failure mode:** commander timing not modeled → the simulator must **not** silently produce a cast-time; it reports `COMMANDER_TIMING: NOT_MODELED` and stops that experiment. This prevents over-claiming.

---
## STEP 12 — Theory application

**What happens:** the question is routed to the few frameworks that materially improve the audit (topic routing, not author fame). Frameworks analyze independently before comparing.

**Tool / site used:**
- **MTG Theory Corpus** — `C:\Users\Main\Desktop\project front gate\Projects\Codie\corpus\MTG_Theory_Corpus_Compilation_v3.docx` (immutable source) + parsed `corpus_pack.json`.
- The codie-audit skill's `theory.retrieve` contract + Laya framework (70 questions, 19 parts) for question routing.

**Attribution levels (per `external-tool-review.md`):**
1. Direct theory (attributed to source)
2. Later synthesis (framework author)
3. Jin inference
4. Format translation (requires explicit explanation before applying to cEDH)
5. Empirical support (deck observation supports framework)
6. Empirical conflict (deck observation contradicts framework)
7. Unresolved (insufficient evidence)

**Failure mode:** a theory claim conflicts with current card text → the conflict is **flagged** (not silently preferring either). Format translation (e.g., Standard theory to cEDH) requires an explicit explanation gate.

---
## STEP 13 — Card triage & prioritized recommendations (evidence.against)

**What happens:** the skill produces card triage + prioritized recommendations, and for each recommendation surfaces the **strongest counterevidence**.

**Tool / site used:**
- `mcp__mtg_unified__spellbook__evaluate_upgrade` (shadow) — evaluates whether a card is worth adding to the deck.
- The skill's own `evidence.against` contract (counterevidence search) — local computation over the evidence packet + metagame + theory.

**Per-recommendation output:**
```json
{
  "card": "X",
  "recommendation": "keep in maindeck (replacement for Y)",
  "reason": "...",
  "opportunity_cost": "replace Z with W (P<0.35 in metagame cohort)",
  "counterevidence": [
    {"source": "tournament_usage", "claim": "X appears in 22% of BZ decks", "strength": 0.7},
    {"source": "theory", "claim": "Lords-of-Complexity favors Y", "strength": 0.4}
  ],
  "reverse_condition": "if opponent passes with 3+ land, drop the card"
}
```

**Guardrails enforced:**
- No overall single deck score (separate dimensions).
- No LLM-decided truth — authoritative sources or explicit uncertainty.
- Prevalence ≠ causal performance.
- No automatic cut of weak-looking cards (package, matchup, opportunity-cost analysis required).

---
## STEP 14 — Jin's two-pass critic (bounded)

**What happens:** the review is a **structured challenge process**, not a second LLM generating another essay.

**Phase 14a — Pass 1: Jin produces the initial audit**
1. Jin reads the frozen evidence packet (Step 6) in full.
2. Jin produces the initial audit + recommendations (the output above).
3. Jin does **not** rewrite Codie's evidence packet. It only interprets.

**Phase 14b — Independent challenger attacks the conclusions**
1. A **separate, independent agent** (not the same as Pass 1) reads the frozen evidence packet + the initial audit.
2. The challenger must identify:
   - a claim
   - an objection
   - supporting evidence (independent of the initial audit)
   - alternative explanation
   - verdict (rejected / downgraded / unresolved)
   - confidence
3. The challenger cannot certify its own claims (no circular references to the initial audit).

**Phase 14c — Jin adjudication**
1. Jin resolves the objection against authoritative evidence + measurements (rules, oracle text, deterministic metrics).
2. Jin distinguishes:
   - factual error → fixed in the evidence packet
   - missing evidence → flagged, reported in "missing evidence"
   - methodological disagreement → resolved by re-reading the contract
   - strategic preference → noted as a preference, not a verdict

**Phase 14d — Final audit records**
- accepted
- rejected
- downgraded
- unresolved

**Failure mode:** the challenger and Jin agree → agreement is **NOT** proof; the audit still records the claim as accepted (with the agreement noted).
**Success mode:** the challenger and Jin disagree → adjudication by the authoritative evidence store; the challenger does NOT auto-accept.

**Tools:** two independent LLM agents (codieaudit profile v0.8.0 + a separate challenger agent) + Codie's authoritative evidence store.

---
## STEP 15 — Final audit report (delivered)

**What the report contains:**
1. **Critical findings immediately visible** (top of the report).
2. **Detailed evidence** organized in readable sections (densities, combos, roles, packages, metagame, castability).
3. **Provenance:** frozen snapshot + SHA-256 fingerprint + source URLs + timestamps.
4. **Confidence** per claim (calibrated) + what calibrated it.
5. **Missing evidence** (what could change conclusions).
6. **Explicit uncertainty** where a source/model can't support a claim (e.g., `COMMANDER_TIMING: NOT_MODELED`).

**Report structure (per the consolidated ideas):**
```
CRITICAL FINDINGS
  - Protection Density WEAK (5, below cohort median of 8)
  - Combo Density OK (8, within baseline)

EVIDENCE
  - Densities (time series, cohort comparison)
  - Combos: confirmed / hypothesis / rejected
  - Roles & packages (many-to-many graph)
  - Metagame: cohorts, prevalence, threat matrix

RECOMMENDATIONS
  - Card triage + prioritized recommendations (with counterevidence)

CONFIDENCE & MISSING EVIDENCE
  - Calibrated confidence per claim
  - What would change conclusions

PROVENANCE
  - Frozen snapshot + SHA-256 fingerprint
  - Source URLs + timestamps
```

**Tool / site used:**
- The codie-audit skill's report generator (per `analytical-contract.md`).
- Output: portable Markdown, delivered to the user's chat.

**Files written:**
- Final report: `C:\Users\Main\Desktop\project front gate\Projects\Codie\decks\audit-<date>-<sha256>.md`

---
## STEP 16 — Delivery & storage

**What happens:** the report is delivered and archived.

**Tool / site used:**
- **Chat delivery** — the report is posted to the user's chat.
- **Discord audit channel** — optional; the skill notes `DISCORD DELIVERY: ❌ no webhook/mcp tool currently` (per `CODIE_MASTER_CHECKLIST.md`). This is a known gap; not blocking.
- **Raindrop trace** — `http://localhost:5899/runs/<trace-id>` (optional, for auditing the session).

**Output file (archived):**
- `C:\Users\Main\Desktop\project front gate\Projects\Codie\decks\audit-<date>-<sha256>.md` (final report)
- `C:\Users\Main\Desktop\project front gate\Projects\Codie\sessions\audit-<timestamp>-<hash>.json` (frozen snapshot)

**Failure mode:** Discord channel not configured → reported as `DISCORD_DELIVERY: UNAVAILABLE` (does not block chat delivery).

---
## MASTER TOOL/SITE INDEX (by site)

| Site | Tool / endpoint | Used in step(s) | Purpose |
|---|---|---|---|
| **Moxfield** (`moxfield.com/decks/<id>`) | `moxfield_deck_info`, `moxfield_decklist` (MCP) | 2 | Deck ingestion (primary) |
| **Archidekt** (`archidekt.com/decks/<id>`) | `get_archidekt_deck` (MCP) | 2 | Deck ingestion (fallback) |
| **Scryfall** (`api.scryfall.com`) | bulk-data `cards`, `scryfall_search_cards` | 3, 13 | Canonical card facts + online resolution |
| **Palm to Deck / Academy Ruins** (`academyruins.com`) | rules index API | 3, 6, 12 | Rules text index |
| **TopDeck.gg** (`topdeck.gg/api/v2/...`) | REST API + `topdeck_recent_cedh_events` (MCP) | 10 | Tournament usage + 3-month frozen metagame |
| **CEDHStats.org** (`cedhstats.org`) | player rankings → `cedhstats/player_rankings.json` | 10 | Player rankings + context |
| **CEDHData** (`cedhdata.com`) | metagame layer (cohorts, prevalence, threat matrix) | 10 | Competitive positioning |
| **Deckcipher** (`cedhdata.com/deckcipher`) | browser-based sim | 11 | Castability simulation |
| **Frontgate vault** (`C:\Users\Main\Desktop\project front gate\Projects\Codie\`) | local JSON ledger | 5, 16 | Frozen snapshots, provenance, archived reports |
| **Codie vault** (`C:\Users\Main\Desktop\project front gate\Projects\Codie\`) | static files + MDT corpus | 6, 12 | Card truth, rules index, theory corpus |
| **Local computation** (Python) | local scripts (`cards.json` lookups, metric pipeline) | 7, 9, 13 | Deterministic metrics, relationship graph, counterevidence |

---
## MASTER INPUT/OUTPUT FILES (by step)

| Step | Input file(s) | Output file(s) |
|---|---|---|
| 2 | user URL | (in-memory) |
| 3 | `cards.json` (59.9 MB) | (in-memory) |
| 4 | frozen snapshot (JSON) | (in-memory validation result) |
| 5 | frozen snapshot (JSON) | `sessions/audit-<ts>-<hash>.json` (FROZEN) |
| 6 | `cards.json`, `rules_index_academyruins.json`, snapshot | evidence packet (in-memory) |
| 7 | evidence packet + `cards.json` | metrics (in-memory) |
| 8 | evidence packet + `cards.json` | combos (in-memory) |
| 9 | evidence packet + `rules_index_academyruins.json` | roles/packages/relationships (in-memory) |
| 10 | frozen metagame snapshot (TopDeck/CEDHStats/CEDHData) | metagame output (in-memory) |
| 11 | frozen baseline + Deckcipher (browser) | castability results (in-memory + file) |
| 12 | theory corpus + Laya framework | theory attribution (in-memory) |
| 13 | evidence packet + metagame + theory | triage + recommendations (in-memory) |
| 14 | frozen evidence packet + initial audit + challenger | final audit (in-memory) |
| 15 | everything above | final report MD (delivered to chat + archived) |

---
## FAILURE & DEGRADATION MATRIX

| Failure | Where it occurs | Degradation |
|---|---|---|
| Moxfield Cloudflare block | Step 2 | Fall back to Archidekt |
| Card not in `cards.json` | Step 3 | Fill online via Scryfall; mark `PARTIAL_UNVERIFIED` |
| Deck INVALID (illegal) | Step 4 | Stop with clear error; no audit |
| TopDeck 429 rate limit | Step 10 | Retry with `TOPDECK_GG_API_KEY.txt`; slow rate (10s/request) |
| CEDHStats partial | Step 10 | Use `player_rankings.json` (300 players); mark `PARTIAL` |
| Commander timing untimed | Step 7/11 | Report `COMMANDER_TIMING: NOT_MODELED`; stop that experiment |
| Discord webhook unavailable | Step 16 | `DISCORD_DELIVERY: UNAVAILABLE`; chat delivery still works |

---
## ONE-LINE SUMMARY

`/audit` → fetch deck (Moxfield/Archidekt) → canonicalize cards (Scryfall `cards.json`) → validate (deck_validate/bulk_ban_list) → freeze snapshot (SHA-256, Frontgate vault) → build evidence packet → deterministic metrics → combos → roles/packages/relationships → metagame (TopDeck/CEDHStats/CEDHData) → theory → triage → **two-pass critic (Jin pass 1, independent challenger, Jin adjudication)** → portable Markdown report (critical findings first, provenance last).
