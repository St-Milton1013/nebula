# NEBULA — DESIGN.PLANS — First Design Plan

**Project:** nebula = new codie iteration (handoff repo)
**Repo:** `github.com/St-Milton1013/nebula` (public, `main`)
**Workspace:** `/c/Users/Main/Desktop/project frontgate/Projects/nebula/`
**Codie source of truth:** `C:\Users\Main\Desktop\project frontgate\Projects\Codie\`
**Audit engine:** codie-audit skill v0.8.0 (codieaudit profile)
**Direction:** single-deck reviews + two-pass critic (Jin); nothing sealed, nothing decided.

> Folder note (verified): the real folder is `project frontgate` — no space before "gate".

---
## 0. Scope & non-negotiables (handoff + user direction)

- **Primary target:** single-deck review. Multi-deck is a red flag, not a goal.
- **Reviewer:** Jin's two-pass critic — bounded: reads evidence, returns structured flags, calls no tools, never rewrites.
- **Nothing sealed / nothing decided.** No "Decisions so far", no DONE marks, no roadmap, no tickets until a decision is chosen, one item at a time.
- **No code in this session.** Planning only; code is written in other chats.
- **This session owns the roadmap and tracking only.**

---
## 1. Architectural vision (who owns what)

| Layer | Owner | Responsibility |
|---|---|---|
| **Codie** | Codie domain | Canonical card data, rules & legality checks, combo records, normalized tournament evidence, role classifications, relationships, deterministic metrics, snapshots, simulation results, provenance, validation status. Does **not** defer card truth or arithmetic to an LLM. |
| **Jin** | Jin | Interpretation and decision support: explain the deck, challenge assumptions, compare alternatives, evaluate opportunity costs, apply theory, construct counterfactuals, recommend experiments. Uses Codie's evidence to reason — it does not become a database report. |

**Three data objects, kept separate (linked but not merged):**
- **Evidence** — a tournament list contains a card; a rules interaction; an observed phenomenon.
- **Interpretation** — the card appears to support a package; a theory lens fits.
- **Decision** — test replacing card X because the opportunity cost may exceed the benefit.
A later experiment can overturn the interpretation without rewriting the original evidence.

**Guardrails (preserved from codie / revised):**
- Local-first processing for private deck + vault data.
- File-backed canonical storage; frozen inputs + source provenance.
- Deterministic calculations wherever possible.
- Read-only analysis until a human accepts a proposed change.
- No automatic promotion of LLM conclusions into authoritative evidence.
- Explicit uncertainty when a source/model/tool cannot support a claim.

---
## 2. The capability & contract ledger — the first artifact to create

Per the consolidated ideas: before changing code or prompts, create a **capability & contract ledger**. One row per capability with fields:

| Field | Purpose |
|---|---|
| Capability ID | Stable reference for discussion + regression tests |
| Owner | Codie, Jin, audit skill, simulator, or delivery layer |
| Status | Implemented / verified / partial / broken / proposed / deferred / rejected |
| Contract | Required inputs, outputs, invariants, failure behavior |
| Authority | Which source/component may establish the result |
| Dependencies | What must be correct before this capability can run |
| Tests | Unit, integration, regression, independent-validation cases |
| Known defects | Reproducible failures + impact |
| Evidence & provenance | How a result is traced and reproduced |
| Acceptance criteria | What must be demonstrated before complete |
| Decision history | Why accepted, deferred, changed, or rejected |

This ledger becomes the bridge between old discussions and new implementation — and prevents a previously accepted requirement from disappearing.

---
## 3. Behavioral contracts by capability group (P0 → P1)

### 3.1 Data & truth (P0 — codie owns)
```
card_truth      → canonical card records (name, mana_cost, cmc, color_identity,
                  type, oracle text, legality, oracle_id)
rules_index     → verified rules + card evidence for a specific interaction
legality        → Commander legality (color identity, banned cards, singleton)
```
- **Tools:** Scryfall bulk API (`cards.json`); Academy Ruins rules API (rules index);
  `mcp__mtg_unified__deck_validate` (with `bulk_ban_list` + `get_card_details` as fallbacks).
- **Deterministic:** legality, color identity, construction checks, CMC, count/density math.

### 3.2 Deck ingestion (P1 — read-only)
```
deck.import     → frozen snapshot: decklist + commanders + source URL + timestamp
                 + provenance fingerprint (SHA-256 of canonical card records)
```
- **Sources/tools:** Moxfield URL (primary), Archidekt URL (fallback).
- **Frozen input:** the deck snapshot is hashed; nothing mutates it after import.

### 3.3 Evidence pipeline (P1)
```
evidence.packet → canonical evidence object (observations + measurements + context,
                  linked to sources, each with confidence, provenance, conditions)
evidence.trace  → trace any conclusion back to sources + calculations
```
- **Tools:** TopDeck.gg API (`tournament_usage`); CEDHStats.org; CEDHData.
- **Outcome:** `AVAILABLE` / `PARTIAL` / `UNSUPPORTED` per module; report keeps going.

### 3.4 Relationship graph (P1)
```
relationships   → many-to-many: card→package, card→combo, card→resource, card→matchup;
                  each edge carries evidence, confidence, provenance, conditions.
roles           → role assignments + supporting evidence (many-to-many, not one-hot)
```
- **Status values:** `REFERENCE`, `DIVERGENT`, `NOVEL`, `UNRESOLVED`, `UNCLASSIFIED`.
- **Guards:** no forced role; `UNCLASSIFIED`/`UNRESOLVED` is first-class.

### 3.5 Deterministic metrics (P0, corrected role model)
```
deck.stats      → reproducible counts & densities (Tutor Density, Protection Density,
                  Combo Density, package prevalence, mana efficiency, castability
                  stage breakdown: access→cast→assembly→generation→conversion)
```
- **Tools:** local computation over frozen `cards.json` + snapshot; no LLM for arithmetic.

---
## 4. Command API surface (proposed operations — contracts, not claims of existing)

Each returns structured, provenance-bearing results (not prose only), so Jin can query and interpret.

| Command | Responsibility |
|---|---|
| `deck.validate` | Validate identities, construction, legality |
| `deck.stats` | Reproducible counts & densities |
| `deck.roles` | Role assignments + supporting evidence |
| `deck.combos` | Confirmed combo lines + required pieces |
| `deck.near_combos` | Possible/incomplete lines, marked as hypotheses |
| `deck.packages` | Package membership, dependencies, conversion paths |
| `deck.relationships` | Query card-to-card / card-to-package relationships |
| `compare_cards` | Compare candidates in a specific deck + slot context |
| `simulate_deck_change` | Test a defined modification against a frozen baseline |
| `tournament_usage` | Dated inclusion + package-prevalence evidence |
| `theory.retrieve` | Attributed theory claims + disagreements |
| `rules.explain` | Verified rules + card evidence for a specific interaction |
| `evidence.trace` | Trace a conclusion to underlying sources + calculations |
| `evidence.against` | Strongest counterevidence to a conclusion |

**Design principle:** commands return structured, provenance-bearing results so Jin can interpret, not a giant undifferentiated dump. Retrieval must expose what it retrieved, omitted, and why.

---
## 5. Audit workflow (/audit — canonical single-deck analysis)

1. **Resolve & scope** — what question is being asked.
2. **Freeze input** — snapshot + SHA-256 fingerprint (gazette).
3. **Validate** — identities, construction, legality (deck.validate).
4. **Evidence packet** — build `evidence.packet` from observations + measurements.
5. **Deterministic metrics** — `deck.stats` (densities, stage breakdown).
6. **Verify combos & commander interactions** — `deck.combos` + `rules.explain`.
7. **Map roles/packages** — `deck.roles` + `deck.packages` + `deck.relationships`.
8. **External checks & experiments** — `tournament_usage`, `simulate_deck_change` (if applicable).
9. **Apply theory** — `theory.retrieve` to relevant frameworks; preserve disagreements.
10. **Card triage & prioritized recommendations** — `evidence.against` for counterevidence.
11. **State confidence, missing evidence, what could change conclusions.**

**Output:** portable Markdown; critical findings immediately visible; evidence organized in readable sections. Keep: Tutor Density, Protection Density, Combo Density, package analysis, theory, card triage, prioritized reconstruction, confidence, provenance. No redundant global curve dump.

**/compare (distinct contract):** audit two configurations independently, then compare:
- Shared structural core
- Differing cards & packages
- Functional consequences
- Mana/resource usage changes
- Combo trees & conversion outlets
- Mulligan & castability behavior
- Matchup implications & opportunity costs
- Evidence for / against each configuration
Each divergent slot faces the same evidence standard.

---
## 6. Metagame layer (frozen, date-stamped, 3-month window)

Structure: cohorts, card prevalence, package prevalence, threat matrix, challenger, regression log.

| Output | What it establishes |
|---|---|
| Cohorts | Which lists belong to same commander/archetype group |
| Card prevalence | Frequency within the cohort (prevalence, not proof of necessity) |
| Package prevalence | Packages + combinations appearing together |
| Threat matrix | Opposing strategies / win conditions relevant to target deck |
| Challenger | Separate review attacking Jin's conclusion (independent) |
| Regression log | Findings, corrections, repeated failure patterns |

**Must-not-do guards:**
- No treating a top-16 commander summary as a full decklist dataset.
- No treating inclusion as proof of necessity.
- No treating prevalence as causal performance evidence.
- No mixing periods without identifying the change.
- No confident archetype-wide claims from small biased samples.

**Tools:** TopDeck.gg API (3-month frozen snapshot); CEDHStats.org; CEDHData.

---
## 7. Adversarial review pipeline (structured challenge, not a second LLM)

```
Codie          → frozen evidence packet
Jin            → initial audit + recommendations
Independent challenger → attack conclusions (same evidence + independently
                       identified counterevidence)
Jin adjudication → resolve objections against authoritative evidence + measurements
Final audit    → record accepted / rejected / downgraded / unresolved claims
Correction & regression → material failures → future tests
```

**Safeguards:**
- Challenger cannot rewrite Codie's evidence packet.
- Challenger must identify: a claim, objection, supporting evidence, alternative explanation, verdict, confidence.
- Agreement between models is not proof; disagreement triggers adjudication.
- Distinguish factual error, missing evidence, methodological disagreement, strategic preference.
- Major recommendations + repeated failures get more scrutiny.
- Challenger must not certify its own claims (no circular references).

**Tools:** two independent LLM agents (or the codieaudit profile + a separate challenger agent) + Codie's authoritative evidence store.

---
## 8. Simulator & mutation testing (castability-first)

**Recorded planning constraints (preserved):**
- Optimization objective: **castability**.
- Canonical storage: **files**.
- Simulator integration: **browser** (Deckcipher).
- Broader scope: deferred until decisions made.

**Narrowly defined experiments (first):**
- **Cast by turn X** — can the deck pay the costs and cast the target?
- **In hand by turn X** — has the target entered the player's hand?
- **Seen/accessed by turn X** — target accessible under a defined rule?

Metrics must **not** be conflated. A card seen by turn 2 is not necessarily castable by turn 2. If commander timing is not modeled, report `COMMANDER_TIMING: NOT_MODELED`.

Each experiment records: baseline, exact modification, mulligan policy, turn-one draw, opponent-mana assumptions, sample size, random seed (when supported), results, uncertainty, representative sample lines.

**Defaults:** Policy mode, 5,000 games, minimum keep of 5 (where supported).

**Mutation testing (after baseline is trustworthy):**
1. Select target weakness / optimization objective.
2. Identify eligible slots + constraints.
3. Generate candidate substitutions.
4. Validate each candidate deck.
5. Compare every candidate against the same frozen baseline.
6. Run relevant measurements.
7. Rank by observed effect, uncertainty, opportunity cost.
8. Examine strongest alternatives for package damage or regressions.
9. Present to human review.
10. Save experiment + outcome without auto-changing canonical deck.

**Tools:** Deckcipher (browser) for simulation; local computation for metrics; Laya + mtg-unified MCP for complementary validation.

---
## 9. Theory corpus + primer/video ingestion (shared service, distinct authority)

**Theory corpus** (shared service for Jin's analysis + learning):
- Topic routing (not author fame).
- Claim-level attribution (direct theory, later synthesis, Jin inference, format translation, empirical support, empirical conflict, unresolved).
- Independent framework analysis before comparing.
- Disagreement preservation (definitional, contextual, empirical, format-specific).
- Format translation (explicit explanation before applying historical theory to cEDH).
- Theory-to-evidence links (which deck observations support/contradict).
- Source freshness separated from durable strategic principles.

**Primer ingestion (versioned, immutable source):**
- Package membership + intended function; combo outputs + prerequisites;
  sequencing + decision points; failure states; protection + recovery lines;
  alternate conversion outlets; anti-decking / edge cases; exact source section, version, passages.
- Flag conflicts with current card text rather than silently preferring primer.

**Video transcripts (separate extension):**
- Transcript-first: acquire transcript, timestamps, metadata, speaker attribution, source version.
- Claim extraction → validation (card facts/rules vs authoritative data) → conflict analysis.
- Optional deep stage: targeted visual inspection (OCR / card recognition) where needed.
- **Modes:** Fast / Standard / Deep (Deep is adaptive).
- Preserves attribution; both distinct from verified card truth.

**Tools:** web_search / web_extract for source ingestion; local parsers + rules API for validation.

---
## 10. Final design plan — build order (P0 → P3)

### P0 — Contracts & foundation
Inventory current capability/known defects/intended behavior.
- Codie/Jin boundaries + evidence classes (5-layer model).
- Freeze deck snapshot + provenance schema.
- Audit output contract.
- Corrected role model + deterministic metrics.
- Canonical verification + regression ledgers.
- Create the capability & contract ledger (first artifact).
**Tools:** local inventory over codie repo + vault + Laya; Scryfall bulk.

### P1 — Evidence pipeline reliability
- Validate identities, construction, legality.
- Verify commander + combo paths.
- Build many-to-many relationship graph + role assignments.
- Establish `evidence.trace` + counterevidence retrieval.
- Generate complete report with honest `AVAILABLE/PARTIAL/UNSUPPORTED` statuses.
- Independently validate the end-to-end workflow.
**Tools:** `mcp__mtg_unified__deck_validate`, Scryfall, Academy Ruins rules API, Laya.

### P2 — Competitive + experimental evidence
- Frozen 3-month metagame layer (TopDeck/CEDHStats/CEDHData).
- Deckcipher + mana calculator integration.
- Castability simulator against a known baseline.
- Structured adversarial review pipeline.
- Correction + regression log.
**Tools:** Deckcipher (browser), TopDeck.gg, CEDHStats.org, CEDHData.

### P3 — Strategic intelligence
- Theory graph + primer ingestion.
- Counterfactual deck changes + mutation testing.
- Richer tournament comparisons + matchup studies.
- Transcript-first video ingestion.
- UI, puzzle benchmark, research integrations.
**Tools:** web_search/extract, Deckcipher, video transcript tools, local parsers.

---
## 11. Governance & session rules

- **Master rule:** nothing sealed until the user says so. No "Decisions so far", no DONE marks, no roadmap items become tickets, no multi-deck as the primary target.
- **One item decided at a time.** All items stay open until the user chooses.
- **Code is written in other chats.** This session is planning + roadmap + tracking only.
- **Tool discipline:** integrate tools only where their output answers a defined question; never dump a hidden undifferentiated data set.
- **Human approval required** before any proposed change is promoted to canonical deck.

---
## 12. File inventory (this session)

| File | Purpose |
|---|---|
| `nebula/NEBULA-HANDBOOK.md` | Handoff doc (master rule + codie items to decide on) |
| `nebula/NEBULA-CHECKLIST.md` | Open decision menu (nothing locked) |
| `nebula/README.md` | Landing page |
| `nebula/NEBULA-PLAN.md` | (lighter summary already written) |
| **`nebula/NEBULA-DESIGN-PLAN.md`** | **This document — the detailed first design plan** |

---
*Generated from: NEBULA-HANDBOOK.md, NEBULA-CHECKLIST.md, README.md, codie repo (Projects/Codie), Laya knowledge base (mtg_laya_project), codie-audit skill v0.8.0, and the consolidated codie-ideas document.*
