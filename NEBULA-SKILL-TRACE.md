# NEBULA — SKILL-TRACE — Extreme-Depth: What Happens When You Invoke /audit

**Header:** This is the clock-by-clock execution trace for a single `/audit <deck-url>` invocation, running on the codie-audit v0.8.0 (codieaudit profile) engine in `C:\Users\Main\AppData\Local\hermes\profiles\codieaudit\skills\codie-audit\`.
**Direction:** single-deck review. Nothing sealed; nothing decided.
**Style:** each step names the site/API and the tool, exactly when it fires, and where its output lands.

---
## 0. Pre-flight (before you type /audit)

| Field | Value |
|---|---|
| User | Confirms single-deck target (multi-deck = red flag) |
| Deck source | Moxfield (primary) or Archidekt (fallback) |
| Deck format | cEDH (Commander, 100-card mainboard + 2 commanders) |

No tool calls fire here. This is a governance gate: the skill checks the request is a single-deck cEDH audit and records the user's intent in the session's tracking (nebula/`NEBULA-CHECKLIST.md` stays open).

---
## 1. At invocation — `/audit <deck-url> [focus]`

**When:** t = 0 (user sends `<deck-url>` in chat).
**Where:** conversation prompt lands in the codieaudit profile's `/audit` dispatch.

**Action:**
1. The codieaudit profile parses the command. Input = the deck URL + optional focus string.
2. Scope resolution: identifies deck source (Moxfield vs Archidekt), commander(s), and the target question.
3. If the URL is unrecognized or the deck isn't cEDH, the skill reports back exactly what's wrong and asks one clarifying question (governance: one item at a time).

**Tools used:**
- **codie-audit skill** (v0.8.0, codieaudit profile) — the dispatch layer.
- **No external site yet** (URL parsing is in-chat).

---
## 2. Deck ingestion — fetch the deck

**When:** t = 1 (right after scope resolution).
**Where:** skill → MCP server.
**Output lands in:** `deck.snapshot` in memory (and staged to vault shortly).

**Action:**
1. Resolves the deck URL scheme:
   - `moxfield.com/decks/<id>` → primary
   - `archidekt.com/decks/<id>` → fallback
2. Calls the appropriate MCP fetcher:
   - **get_moxfield_deck** (mtg-commander MCP) — fetches decklist + metadata from Moxfield.
   - **get_archidekt_deck** (mtg-commander MCP) — fallback fetcher.
   - Bypasses Cloudflare where the skill's fetch path handles it (there is a skill-internal `get_moxfield_deck` noted as bypassing Cloudflare).
3. Parses the decklist:
   - 98-card mainboard (cEDH standard)
   - both commanders + paired commander relationship
   - color identity (both commanders' identities unioned)
   - canonical `oracle_id` identity per card per ADR-001 (handles face-up/face-down, double-faced)

**Sites/APIs used:**
- `https://www.moxfield.com/decks/<id>` (Moxfield API)
- `https://archidekt.com/decks/<id>` (Archidekt API)

**Tools used:**
- `mcp__mtg_commander__get_moxfield_deck` (primary)
- `mcp__mtg_commander__get_archidekt_deck` (fallback)
- <skill-internal fetch layer> for Cloudflare bypass

**Failure behavior:** if fetch fails (403/404), the skill reports which URL/format failed and does NOT proceed; the decklist is not frozen, so no partial state exists.

---
## 3. Deck validation — construction & legality

**When:** t = 2 (right after ingestion, before anything else).
**Where:** skill → MCP server + local rule lookup.
**Output lands in:** validation result into the evidence packet.

**Action:**
1. Validates construction:
   - deck size (99 cards with commanders in cEDH)
   - singleton rule (no card > 1 copy in mainboard)
   - color identity within both commanders
2. Checks legality (banned/restricted cards in Commander).
3. Validates identities: every card in the deck resolves to a canonical record; unknown cards surface with exact name.

**Sites/APIs used:**
- `mcp__mtg_unified__deck_validate` (validation engine, authoritative)
- `mcp__mtg_unified__bulk_ban_list` (Commander ban list)
- `mcp__mtg_unified__get_card_details` (per-card resolution, fallback)
- `mcp__mtg_unified__bulk_format_legality` (batch legality, optional)

**Output:** VALID / INVALID with actionable error messages; `deck.validated = true/false`.

---
## 4. Freeze input (gazette)

**When:** t = 3 (immediately after validation passes).
**Where:** populates the canonical snapshot.

**Action:**
1. Builds the canonical deck snapshot: decklist + commanders + source URL + timestamp.
2. Resolves every card to its canonical record (from `cards.json`).
3. Computes provenance fingerprint: SHA-256 of the canonical card records + snapshot metadata.
4. Marks the snapshot immutable. From here on, everything traces to this fingerprint.

**Where output lands:**
- Record written to the Frontgate vault (canonical file store).
- Fingerprint stored alongside the evidence packet for later `evidence.trace`.

**Tools:**
- Local file writes (Frontgate vault path).
- Local SHA-256 computation (stdlib).

---
## 5. Evidence packet build

**When:** t = 4.
**Where:** builds `evidence.packet`.

**Action:**
1. Assembles observations:
   - imported decklist (from step 2)
   - commander identity (from step 2)
   - card facts (from `cards.json`)
   - validation result (from step 3)
2. Assembles measurements (deterministic counts/densities — step 5).
3. Assembles context (theory routing from step 10).
4. Tags each entry:
   - confidence (calibrated)
   - provenance (source URL, section, version, passage)
   - applicable conditions
5. Enforces the evidence hierarchy:
   - **Authoritative truth** (rules, Oracle text, legality)
   - **Observations** (decklist, tournament records)
   - **Reproducible measurements** (counts, densities, simulation)
   - **Context** (primers, theory, user hypotheses)
   - **Decision conclusions** (recommendations, via governed process)

**Tools:**
- `cards.json` (Scryfall bulk API data, local file at `Project\Codie\nodes\00_CardTruth\cards.json`)
- local computation (stdlib)

**Output:** `evidence.packet` object (in-memory + staged to vault).

---
## 6. Deterministic metrics (deck.stats)

**When:** t = 5.
**Where:** builds the metrics record.

**Action:**
1. Computes reproducible counts and densities (local, no LLM):
   - **Tutor Density** — cards that give you the next thing
   - **Protection Density** — cards that protect a line
   - **Combo Density** — cards that enable combo
   - package prevalence
   - mana efficiency
2. Computes **castability stage breakdown**:
   - access → cast → assembly → generation → conversion
3. Reports `COMMANDER_TIMING: NOT_MODELED` if commander timing isn't modeled.

**Tools:**
- Local computation (stdlib)
- `mcp__mtg_unified__deck_validate` (for legality-based density checks)

**Output:** `deck.stats` record (densities, stage breakdown, commander-timing flag).

---
## 7. Combo & commander interaction verification

**When:** t = 6.
**Where:** builds the confirmed-combo record.

**Action:**
1. Returns confirmed combo lines + the cards/pieces required.
2. Returns possible/incomplete lines, clearly marked as **hypotheses**.
3. Verifies commander interactions (both commanders, color identity, shared resources).

**Tools:**
- `mcp__spellbook__spellbook_find_decklist_combos` (confirmed + near combos)
- `mcp__spellbook__spellbook_combo_details` (for any confirmed combo line of interest)
- `mcp__mtg_unified__rules_lookup` (rule verification, fallback)
- `mcp__mtg_unified__rules_interaction` (mechanic interaction, optional)

**Output:** `deck.combos` + `deck.near_combos` + commander-interaction report.

---
## 8. Role & package mapping

**When:** t = 7.
**Where:** builds role + package + relationship records.

**Action:**
1. Assigns roles + supporting evidence (many-to-many, not one-hot).
2. Describes package membership, dependencies, conversion paths.
3. Returns card-to-card and card-to-package relationships.
4. Uses `UNCLASSIFIED`/`UNRESOLVED` where evidence is insufficient (never force a role).

**Tools:**
- `mcp__spellbook__deck_analysis` (role/package context)
- Local computation over `cards.json` + relationships data

**Output:** `deck.roles`, `deck.packages`, `deck.relationships` (each edge carries evidence, confidence, provenance, conditions).

---
## 9. External checks — metagame & tournament evidence

**When:** t = 8.
**Where:** pulls dated, frozen evidence.

**Action:**
1. Builds the frozen 3-month metagame layer:
   - **cohorts** (same commander/archetype group)
   - **card prevalence** (within the cohort)
   - **package prevalence** (which packages appear together)
   - **threat matrix** (opposing strategies / win conditions)
2. Queries dated inclusion + package-prevalence evidence.
3. Integrates Deckcipher + mana calculator for castability baseline.

**Sites/APIs used:**
- **TopDeck.gg REST API** — `POST https://topdeck.gg/api/v2/tournaments` (requires `TOPDECK_GG_API_KEY.txt`; 3-month frozen snapshot)
- **CEDHStats.org** — player rankings (ranked player data)
- **CEDHData** — cEDH meta data
- **Deckcipher** (browser, local) — castability baseline

**Tools:**
- API calls via the skill's API clients (TopDeck requires the key from the local file).
- Deckcipher via **browser_exec** / local browser session (simulator integration).
- `mcp__mtg_unified__tournament_usage` (tournament evidence query, optional)

**Failure behavior:** if a source is unavailable/unreachable, that module returns `AVAILABLE`/`PARTIAL`/`UNSUPPORTED`; the report keeps going with the remaining evidence.

---
## 10. Castability simulation (optional — if the focus asks for castability)

**When:** t = 9 (only if the focus explicitly requests castability/simulation).
**Where:** runs in a local browser session.

**Action:**
1. Runs narrowly defined experiments:
   - **Cast by turn X** — can the deck pay the costs and cast the target?
   - **In hand by turn X** — has the target entered the player's hand?
   - **Seen/accessed by turn X** — target accessible under a defined rule?
2. Records for each: baseline, exact modification, mulligan policy, turn-one draw assumption, opponent-mana assumptions, sample size, random seed (when supported), results, uncertainty, representative sample lines.
3. Defaults: **Policy mode, 5,000 games, minimum keep of 5** (where supported).

**Sites/APIs used:**
- **Deckcipher** — browser-based simulator

**Tools:**
- `browser_exec` (browser session, local; or in-house simulator if chosen)
- Local computation over simulation results

**Failure behavior:** `COMMANDER_TIMING: NOT_MODELED` if commander timing is not correctly modeled.

---
## 11. Theory application

**When:** t = 10.
**Where:** retrieves attributed theory claims.

**Action:**
1. Routes the question to the few frameworks that materially improve the audit (topic routing, not author fame).
2. Applies attribution: direct theory, later synthesis, Jin inference, format translation, empirical support, empirical conflict, unresolved claims.
3. Has applicable frameworks evaluate the evidence **independently** before comparing.
4. Preserves disagreements (definitional, contextual, empirical, format-specific).
5. Requires explicit explanation before applying historical Standard/Legacy/Vintage/Limited theory to cEDH.

**Sites/APIs used:**
- **MTG Theory Corpus Compilation v3** (source sourcebook, immutable) — `C:\Users\Main\Desktop\project frontgate\Projects\Codie\corpus\MTG_Theory_Corpus_Compilation_v3.docx` → `corpus_pack.json`

**Tools:**
- `mcp__spellbook__theory.retrieve` (theory retrieval)
- Local corpus processing (`corpus_pack.json`)

---
## 12. Card triage & counterevidence (evidence.against)

**When:** t = 11.
**Where:** builds the triage + recommendation record.

**Action:**
1. Produces card triage + prioritized recommendations.
2. For each recommendation, surfaces the strongest counterevidence:
   - Why this card is recommended.
   - Why it might be wrong for this deck.
   - What competing card/package would occupy the slot.
   - What evidence supports the alternative.
   - What assumptions would make the recommendation fail.
   - What result would reverse the decision.
3. Preserves conflicts (e.g., primer's explanation vs current card text) rather than silently preferring one.

**Tools:**
- `mcp__spellbook__evidence.against` (counterevidence search)
- `mcp__spellbook__evidence.trace` (trace a conclusion to sources)

**Output:** `deck.triage` + prioritized recommendations + counterevidence record.

---
## 13. Jin's two-pass critic (bounded review — Plan B)

**When:** t = 12.
**Where:** two independent agent passes.

**Action:**
**Pass 1 — Jin produces the initial audit:**
1. Jin reads the frozen evidence packet.
2. Produces the initial audit + recommendations.
3. Jin does **not** rewrite Codie's evidence packet.

**Independent challenger attacks the conclusions:**
1. Challenger identifies a claim, objection, supporting evidence, alternative explanation, verdict, confidence.
2. Challenger must use independent evidence — cannot certify its own claims (no circular references).

**Jin adjudication:**
1. Resolve objections against authoritative evidence + measurements.
2. Distinguish factual error, missing evidence, methodological disagreement, strategic preference.

**Final audit records:**
- accepted
- rejected
- downgraded
- unresolved

**Tools:**
- Two independent LLM agents (local model Qwen3.6-35B-A3B-UD-Q4_K_M via llamacpp) — one for Pass 1 (Jin), one for the challenger.
- Codie's authoritative evidence store (frozen snapshot).

---
## 14. Final audit report (delivered)

**When:** t = 13 (end of pipeline).
**Where:** delivered to the user as portable Markdown.

**Report contents:**
1. Critical findings immediately visible.
2. Detailed evidence in readable sections.
3. Provenance: frozen snapshot, hashes, sources, timestamps.
4. Calibrated confidence per claim.
5. Missing evidence + what could change conclusions.
6. Explicit uncertainty where a source/model can't support a claim.

**Guardrails enforced in the report:**
- No overall single deck score (separate dimensions, evidence, uncertainty).
- No LLM-decided truth (authoritative sources or explicit uncertainty).
- Prevalence ≠ causal performance.
- No automatic cut of weak cards (package, matchup, opportunity-cost analysis required).
- Theory stays interpretive, preserves conflicts, does not overrule measurements.
- Human approval required before any recommended change is promoted to canonical deck.

---
## 15. What the user sees

```
/AUDIT result: <deck-url>
──────────────────────────────────────────────
Finding: Tutor Density OK · Protection Density WEAK · Combo Density OK
Package: "X" supports Y (evidence: E1 · conf: 0.72 · provenance: source@sec§3)
Recommendation: replace card Z with W (opportunity cost > benefit)
Why not: counterevidence E2 (inclusion rate 12%/30d · matching deck 0.82)
Confidence: 0.72 · Missing evidence: tournament cohort size 48 (30d)
Status: AVAILABLE (report continues; metagame pending)
──────────────────────────────────────────────
Provenance: SHA-256 <fingerprint> · frozen 2026-10-24T01:15:00Z
```

---
## 16. Reliability & regression discipline (end of invocation)

| Discipline | Mechanism |
|---|---|
| Behavioral contracts | Codie/Jin/tool borders defined per capability |
| Independent validation | Challenger agent is independent of Pass-1 Jin |
| Failure states | `AVAILABLE`/`PARTIAL`/`UNSUPPORTED`; report keeps going |
| Regression log | Repeated failure patterns → future tests |
| Provenance | SHA-256 snapshot + source references |

---
## Summary table — every site/API + tool, when, and where

| Step | Site/API | Tool (name) | When | Output destination |
|---|---|---|---|---|
| 1 | — | codie-audit v0.8.0 (codieaudit profile) | t=0 | Session tracking (nebula/NEBULA-CHECKLIST.md) |
| 2 | Moxfield / Archidekt API | `get_moxfield_deck` / `get_archidekt_deck` (mtg-commander) | t=1 | deck.snapshot (memory) |
| 3 | MTG rule / ban data | `deck_validate`, `bulk_ban_list`, `get_card_details` (mtg-unified) | t=2 | validation result (evidence) |
| 4 | Local file | SHA-256, vault write | t=3 | Frontgate vault (frozen snapshot) |
| 5 | cards.json (Scryfall bulk) | local computation | t=4 | evidence.packet |
| 6 | — | local computation | t=5 | deck.stats |
| 7 | — | `spellbook_find_decklist_combos`, `spellbook_combo_details` | t=6 | deck.combos + commander report |
| 8 | TopDeck.gg, CEDHStats.org, CEDHData | API clients + local parsers | t=8 | metagame layer + tournament evidence |
| 9 | Deckcipher (browser) | `browser_exec` | t=9 | castability baseline (if requested) |
| 10 | MTG Theory Corpus v3 | `spellbook_/theory.retrieve` + local corpus | t=10 | `theory.retrieve` results |
| 11 | — | `evidence.against`, `evidence.trace` | t=11 | tray + recommendations |
| 12 | Local LLM (Qwen3.6-35B via llamacpp) | Jin agent + challenger agent | t=12 | accepted/rejected/downgraded/unresolved |
| 13 | — | Report assembly | t=13 | user (portable Markdown) |

---
## Key source files (where data lives on disk)

| Resource | Path | Role |
|---|---|---|
| Codie-audit skill (active) | `C:\Users\Main\AppData\Local\hermes\profiles\codieaudit\skills\codie-audit\` | Audit engine (v0.8.0) |
| Card truth store | `C:\Users\Main\Desktop\project frontgate\Projects\Codie\nodes\00_CardTruth\cards.json` | Canonical card records (Scryfall bulk) |
| Rules index | `C:\Users\Main\Desktop\project frontgate\Projects\Codie\rules\rules_index_academyruins.json` | Verified rules (Academy Ruins API) |
| Theory corpus | `C:\Users\Main\Desktop\project frontgate\Projects\Codie\corpus\MTG_Theory_Corpus_Compilation_v3.docx` → `corpus_pack.json` | Theory corpus |
| TopDeck API key | `C:\Users\Main\Desktop\TOPDECK_GG_API_KEY.txt` | TopDeck.gg auth |
| Codie repo (source of truth) | `C:\Users\Main\Desktop\project frontgate\Projects\Codie\` | Vault + codie body of work |
| Laya KB | `C:\Users\Main\Desktop\mtg_laya_project\` | 70-question Laya framework (decision-support only) |
| Git tracking | `github.com/St-Milton1013/nebula` (public, main) | Handoff repo |

---
*Extreme-depth trace of `/audit` invocation, as planned in `NEBULA-DESIGN-PLAN.md` and `NEBULA-INVOKING.md`. Nothing is locked until the user chooses; this is the intended execution path.*
