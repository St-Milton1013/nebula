# NEBULA — SKILL-INVOKING — Step-by-Step: What Happens When You Invoke /audit

**Audience:** the human + a new chat that inherits the handoff.
**Format:** portable Markdown; critical findings first, evidence after.
**Direction:** single-deck reviews + two-pass critic (Jin); nothing sealed, nothing decided.

---
## 0. Pre-flight (before you even type /audit)

- Confirm the **single-deck** target (multi-deck is a red flag, not a goal).
- Have a deck URL ready: **Moxfield** (primary) or **Archidekt** (fallback).
- Confirm the deck is a **cEDH** deck (Commander format, 100-card mainboard + 2 commanders).
- Nothing is locked; if the request is ambiguous, one clarifying question only.

---
## 1. Trigger & scope resolution

**You:** `/audit <deck-url> [focus]`

**What the skill does:**
1. Resolves the deck source (Moxfield → primary; Archidekt → fallback).
2. Identifies the commander(s) and the target question/scope (e.g., "is the protection spell a good cut?").
3. If scope is ambiguous, asks **one** clarifying question (governance: one item at a time, no locking).

**Tools:** Moxfield/Archidekt fetchers (skill-internal); the deck URL is the only user input consumed.

---
## 2. Deck ingestion

**What the skill does:**
1. Fetch the deck (bypassing Cloudflare where needed).
2. Extract:
   - 98-card mainboard (canonical card identities via `oracle_id` per ADR-001)
   - both commanders + paired commander relationship
   - color identity, format (cEDH), card count
3. Resolve any face-up face-down or double-faced cards to their canonical identity.

**Tools:** Moxfield/Archidekt fetch (skill-internal); `mcp__mtg_unified__deck_validate` for construction/legality.

---
## 3. Freeze input (gazette)

**What the skill does:**
1. Build the canonical snapshot: decklist + commanders + source URL + timestamp.
2. Compute a provenance fingerprint (SHA-256 of canonical card records).
3. Record the snapshot as **immutable** — nothing below this line mutates it.

**Why:** frozen inputs + provenance are non-negotiable; every downstream result traces to this fingerprint.

---
## 4. Evidence packet build (step 4)

**What the skill does:**
1. Assemble the evidence packet from **observations** (imported decklist, commander identity, card facts) + **measurements** (deterministic counts/densities) + **context** (theory corpus routing, dated tournament evidence if any).
2. Tag every entry with:
   - confidence (calibrated)
   - provenance (source URL, section, version, passage)
   - applicable conditions
3. Distinguish evidence hierarchy:
   - **Authoritative truth** (rules, Oracle text, legality)
   - **Observations** (tournament records, imported decklists)
   - **Reproducible measurements** (counts, densities, simulation results)
   - **Context** (primers, theory, user hypotheses)
   - **Decision conclusions** (recommendations, produced via governed process)

**Tools:** static card facts (`cards.json` via Scryfall bulk); decision not based on LLM confidence.

---
## 5. Deterministic metrics (deck.stats)

**What the skill does:**
1. Compute reproducible counts and densities (local, no LLM):
   - **Tutor Density** (cards that give you the next thing)
   - **Protection Density** (cards that protect a line)
   - **Combo Density** (cards that enable combo)
   - package prevalence, mana efficiency
2. Compute the **castability stage breakdown**:
   - access → cast → assembly → generation → conversion
   - A deck can excel at one stage and fail at another.
3. Report `COMMANDER_TIMING: NOT_MODELED` if commander timing isn't modeled.

**Tools:** local computation over frozen `cards.json` + snapshot; `mcp__mtg_unified__deck_validate` for legality.

---
## 6. Combo & commander interaction verification (deck.combos, rules.explain)

**What the skill does:**
1. Return confirmed combo lines + the cards/pieces required.
2. Return possible/incomplete lines, clearly marked as **hypotheses**.
3. Verify commander interactions (both commanders, color identity, any shared resource).

**Tools:** `deck.combos`, `deck.near_combos` (hypotheses), `rules.explain` for specific interactions.

---
## 7. Role & package mapping (deck.roles, deck.packages, deck.relationships)

**What the skill does:**
1. Assign roles + supporting evidence (many-to-many, not one-hot).
2. Describe package membership, dependencies, conversion paths.
3. Return card-to-card and card-to-package relationships.
4. Use `UNCLASSIFIED`/`UNRESOLVED` where evidence is insufficient — never force a role.

**Tools:** `deck.roles`, `deck.packages`, `deck.relationships`; edge carries evidence, confidence, provenance, conditions.

---
## 8. External checks (tournament_usage, metagame layer)

**What the skill does:**
1. Build the frozen 3-month metagame layer:
   - **cohorts** (same commander/archetype group)
   - **card prevalence** (within the cohort)
   - **package prevalence** (which packages appear together)
   - **threat matrix** (opposing strategies / win conditions)
2. Query dated inclusion + package-prevalence evidence.
3. Integrate **Deckcipher + mana calculator** for castability baseline.

**Tools:** TopDeck.gg API (3-month frozen snapshot); CEDHStats.org; CEDHData; Deckcipher (browser).

---
## 9. Castability simulation (optional — if requested)

**What the skill does:**
1. Runs narrowly defined experiments:
   - **Cast by turn X** — can the deck pay the costs and cast the target?
   - **In hand by turn X** — has the target entered the player's hand?
   - **Seen/accessed by turn X** — target accessible under a defined rule?
2. Records: baseline, exact modification, mulligan policy, turn-one draw assumption, opponent-mana assumptions, sample size, random seed, results, uncertainty, representative sample lines.
3. Defaults: **Policy mode, 5,000 games, minimum keep of 5** (where supported).

**Tools:** Deckcipher (browser); local computation for stage metrics.

---
## 10. Theory application (theory.retrieve)

**What the skill does:**
1. Route the question to the few frameworks that materially improve the audit (topic routing, not author fame).
2. Apply attribution: direct theory, later synthesis, Jin inference, format translation, empirical support, empirical conflict, unresolved claims.
3. Have applicable frameworks evaluate the evidence **independently** before comparing conclusions.
4. Preserve disagreements (definitional, contextual, empirical, format-specific).
5. Require explicit explanation before applying historical Standard/Legacy/Vintage/Limited theory to cEDH.

**Tools:** `theory.retrieve`; `mtg-commander`/`mtg-unified` for card/rule facts.

---
## 11. Card triage & prioritized recommendations (evidence.against)

**What the skill does:**
1. Produce card triage + prioritized recommendations.
2. For each recommendation, surface the **strongest counterevidence**:
   - Why this card is recommended.
   - Why it might be wrong for this deck.
   - What competing card/package would occupy the slot.
   - What evidence supports the alternative.
   - What assumptions would make the recommendation fail.
   - What result would reverse the decision.
3. Preserve conflicts (e.g., primer's explanation vs current card text) rather than silently preferring one.

**Tools:** `evidence.against` (counterevidence search); `evidence.trace` (trace a conclusion to sources).

---
## 12. Jin's two-pass critic (bounded — Plan B)

**Pass 1 — Jin produces the initial audit:**
1. Jin reads the frozen evidence packet.
2. Produces the initial audit + recommendations.
3. Jin does **not** rewrite Codie's evidence packet.

**Independent challenger attacks the conclusions:**
1. Challenger identifies a claim, objection, supporting evidence, alternative explanation, verdict, confidence.
2. Challenger must use independent evidence — it cannot certify its own claims (no circular references).

**Jin adjudication:**
1. Resolve objections against authoritative evidence + measurements.
2. Distinguish factual error, missing evidence, methodological disagreement, strategic preference.

**Final audit records:**
- accepted
- rejected
- downgraded
- unresolved

Material failures → correction and regression log (→ future tests).

**Tools:** two independent LLM agents (codieaudit profile v0.8.0 + a separate challenger agent); Codie's authoritative evidence store.

---
## 13. Final audit report (delivered)

**What the report contains:**
1. Critical findings immediately visible.
2. Detailed evidence organized into readable sections.
3. Provenance: frozen snapshot, hashes, sources, timestamps.
4. Confidence (per claim, calibrated) + state that it is calibrated.
5. Missing evidence + what could change conclusions.
6. Explicit uncertainty where a source/model can't support a claim.

**Guardrails enforced in the report:**
- No overall single deck score (separate dimensions, evidence, uncertainty).
- No LLM-decided truth — authoritative sources or explicit uncertainty.
- Prevalence ≠ causal performance.
- No automatic cut of weak-looking cards (package, matchup, opportunity-cost analysis required).
- Theory stays interpretive, preserves conflicts, does not overrule measurements.
- Human approval required before any recommended change is promoted to canonical deck.

---
## 14. What the user sees

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
## 15. Reliability & regression discipline

- Every capability has a **behavioral contract** (inputs, outputs, invariants, failure states, authority boundaries) — codified in the capability & contract ledger.
- The implementer **cannot** certify their own fix; independent check verifies tests cover intended behavior.
- Known defects are tied to a **reproducible test case + expected result**.
- A **regression log** records findings, corrections, repeated failure patterns across audits.
- Failure states return `AVAILABLE`/`PARTIAL`/`UNSUPPORTED`; the report keeps going.

---
## 16. Files produced during an audit

| Artifact | Where | Purpose |
|---|---|---|
| deck snapshot + SHA-256 | Frontgate vault / `nebula/` | Frozen provenance |
| evidence packet | `project frontgate/Projects/Codie/` | Canonical evidence object |
| deck.stats metrics | evidence packet | Deterministic counts/densities |
| castability baseline | simulator (file-backed) | Castability stage breakdown |
| metagame layer | `config/` (3-month frozen) | Tournament evidence |
| final audit report | delivered to user | Portable Markdown, critical findings first |

---
*Step-by-step of the `codie-audit` `/audit` skill, as planned in `NEBULA-DESIGN-PLAN.md`. Nothing is locked until the user chooses; this is the intended execution path.*
