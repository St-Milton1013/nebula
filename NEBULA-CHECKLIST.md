# NEBULA — Wayfinder Map + Running Checklist

**Project:** Nebula (new codie iteration)
**Workspace:** `/c/Users/Main/Desktop/project frontgate/Projects/nebula/`
**Source of truth (codie):** `C:\Users\Main\Desktop\project frontgate\Projects\Codie\`
**Codie GitHub:** https://github.com/St-Milton1013/Codie
**Design inputs:** `pasted_content_2026-10-23_21-46-12-625_0302b9.txt` (249-step audit-tool design, P0–P3 build order) and `pasted_content_2026-10-23_21-46-28-820_e40f9b.txt` (audit report plan).
**Status:** PLANNING — wayfinder map charted; tickets queued.

---

## Destination

Nebula is "done" when we can **successfully run audits on multiple CEDH decks** and each audit returns **useful** information on:

1. **Cards** — right card for this deck / format? synergy, value, cost, risk.
2. **Deckbuilding** — comma plan, mana, commanders, gaps, packages.
3. **Meta** — is this deck trending, how does it match up, what counters it, where it's heading.

Multi-deck is the design core (repeatable, comparable audits), not one-off review.

---

## Notes

- codie-audit v0.7.3 skill is the existing audit engine (decision-support layer, Laya 70-question framework).
- codie repo is large and "out of control" (codie/ package, Goal Engine, Jin, Phase44–49, docs CHECKPOINT avalanche). Deliberately leaned.
- Design inputs (doc 1) refit codie's plan into an **evidence pipeline** with a clear build order; doc 2 fixes the **report structure**.
- Free/cost priority. Local model is for RAM (64 GB), not primarily privacy — but net-local file storage retained.
- All data sources should be free; warn explicitly if any is paid or account-gated.

---

## Your call — open, nothing locked

Below are the candidates pulled from Plan A and Plan B. Nothing is decided until you approve. Tell me which to tick, and I'll lock them into the roadmap.

| # | Candidate from Plan A / Plan B | Status for you |
|---|--------------------------------|------------------|
| 1 | Adopt Plan A's P0 → P3 build order (evidence-first; finish evidence pipeline before expanding Laya) | your call |
| 2 | KEEP codie's 70-question Laya framework in the decision-support layer | your call |
| 3 | KEEP codie's card-truth + rules-index + deck-validation as the data layer | your call |
| 4 | KEEP & refactor codie's meta pipeline (TopDeck/TopDeck, CEDHStats, CEDHData) for multi-deck | your call |
| 5 | KEEP file-backed, versioned evidence + provenance (frozen snapshots, fingerprints) | your call |
| 6 | DISCARD Goal Engine, Jin, V3 UI, theory node graph, heavy docs, single-deck tooling | your call |
| 7 | Report: one per-deck report + cross-deck meta tab (Plan B style) | your call |
| 8 | Simulation: castability first; Policy mode, 5000 games; browser-bridge for Deckcipher/mana calculator | your call |

---



## Setup & tracking (decided)

- **Repo:** brand-new GitHub repository `nebula` under `St-Milton1013` (this session). No existing repo.
- **Progress tracking:** GitHub issues / commits / PRs — any tool (hermes, her, es, gpt, claude) can read or record state, so tracking is shared, not locked to one agent.
- **Code:** NOT written by this planning pass. Other chats write the M-module code; this pass owns the roadmap + tracking doc only.
- **Meta sources:** all free and used properly — TopDeck/TopDeck (`edhtop16`), CEDHStats, CEDHData. Nothing paid or account-gated.
- **GitHub channel:** hermes is connected via `gh` CLI (authenticated to St-Milton1013, `repo` scope), which is the push/record path for this repo.

---

## Tickets (backlog, in implementation order)

### Tick 0 — Freeze the audit contract (P0)
- Inputs, required outputs, evidence labels, report structure, human-authority boundaries (doc 1 §1, §15, doc 2).
- [ ] Draft contract; freeze report structure (doc 2, 12 sections)

### Tick 1 — Deck importer + snapshot + fingerprint (P0)
- Moxfield primary, Archidekt fallback; parse zones (commanders/main/sideboard/etc.); canonical identities; frozen snapshot + SHA-256 fingerprint (doc 1 §2, steps 9–20).
- [ ] Import Moxfield/Archidekt/pasted/local
- [ ] Resolve commanders, zones, aliases
- [ ] Canonical identities + fingerprint

### Tick 2 — Card-truth store (P0)
- Full Oracle text + faces; legalities; source provenance + freshness; Scryfall + Commander Spellbook for evidence; resolve vs tag (doc 1 §3, steps 21–33).
- [ ] Store canonical card records (Scryfall bulk)
- [ ] Rules index (Academy Ruins) + legality via MCP
- [ ] Provenance + freshness stamps

### Tick 3 — Legality & construction (P0)
- 100-card count; commander config; color identity; singleton; ban list; sideboard separation; explicit PASS/FAIL/PARTIAL statuses (doc 1 §4, steps 34–44).
- [ ] Rule 903.5a + commander eligibility
- [ ] Color identity + singleton + bans

### Tick 4 — Deterministic metrics (P0)
- Versioned role taxonomy; Tutor/Protection/Combo density with denominators; role coverage; mana acceleration; draw/selection; interaction; engine/outlet (doc 1 §5, steps 45–63).
- [ ] Role taxonomy + counting rules
- [ ] Densities with card lists + denominators
- [ ] Mana/castability in context (no global curve)

### Tick 5 — Commander & combo analysis (P1)
- Commander first-class; win lines; conversion outlet; disruption; combo map with Spellbook steps (doc 1 §6 §7, steps 64–88).
- [ ] Commander dependency + recasting
- [ ] Confirmed combo map + disruption

### Tick 6 — Package & relationship analysis (P1)
- Card → relationship → package → deck section → whole deck; enablers, outputs, collisions, orphans, dilution (doc 1 §8, steps 89–105).
- [ ] Package definitions + card mapping
- [ ] Resource collisions / competing uses

### Tick 7 — External structural tools (P1)
- Deckcipher + mana calculator against same snapshot; compare + report discrepancy (doc 1 §9, steps 106–120).
- [ ] Integration layer; same-fingerprint enforcement
- [ ] Comparison + discrepancy logging

### Tick 8 — End-to-end report (P1)
- doc-2 12-section report; explicit UNAVAILABLE/PARTIAL/UNSUPPORTED/HUMAN REVIEW statuses; confidence + provenance (doc 1 §15 §216).
- [ ] Per-deck report format (catches doc-2 structure)
- [ ] Freeze "UNVERIFIED — decision support only" for Laya

### Tick 9 — Simulation bridge (P2)
- Castability first: hypothesis, baseline, variants, mulligan policy, draw assumption, seed, uncertainty, commander modeling separately (doc 1 §11, steps 138–157).
- [ ] Baseline-vs-variant harness
- [ ] Commander modeling disclosed (NOT_MODELED flag)

### Tick 10 — Tournament ingestion & meta (P2)
- Event metadata + full decklists; dedup; inclusion/co-inclusion/lift with denominators; sample-size limits; time window (doc 1 §10, steps 121–137).
- [ ] Multi-deck meta table (deck × card)
- [ ] Declare sample-size/coverage limits per query

### Tick 11 — Theory routing (P2)
- Topic-based routing; attribution; format transfer; preserve disagreement (doc 1 §12, steps 158–172).
- [ ] Theory graph (corpus + attribution)
- [ ] Disagreement-preservation

### Tick 12 — Recommendations & experiments (P3)
- Card triage statuses; matched replacement candidates; valid/invalid pairs; rank by decision importance; recommendations subordinate to evidence (doc 1 §13 §17, steps 173–187, 247).
- [ ] Triage classifier + replacement pairs
- [ ] Recommendation confidence ceiling + what-changes-it

### Tick 13 — Delivery + regression (P3)
- Copy-paste report block; delivery verify; full regression suite; honest-failure reward (doc 1 §15 §16, steps 202–234).
- [ ] Delivery (local file / Discord only if approved)
- [ ] Regression on known defects + reference cases

---

## Not yet specified (fog)

- **Laya subset** for multi-deck (full 19 parts vs a lean subset). Settle during Tick 8.
- **Simulator runner** — local Deckcipher binary via browser vs in-house (doc 1 says "use the browser"). Settle in Tick 9.
- **Deck ingestion priority** — Moxfield vs Archidekt; both needed.
- **Report format** — per-deck report + cross-deck tab, or one combined report. Settle in Tick 8.
- **Base** — reuse codie-audit v0.7.3 skill, or rebuild the engine. Tentative: reuse, since its contract already encodes the evidence-discipline boundaries.
- **Meta source set** — TopDeck/TopDeck (edhtop16), CEDHStats, CEDHData; confirm all free.
- **Sideboard / auxiliary zones** — how much nuance the lean audit needs (doc 1 §4 requires it; decide during Tick 3).

---

## Out of scope

| Item | Why left behind |
|------|-----------------|
| Goal Engine (Phase44–49) | Separate bloated program, not part of a lean audit |
| Jin (two-pass critic) | Not part of a lean multi-deck audit |
| V3 UI handoff | Approved design only, not implemented |
| Theory corpus node graph (~197 nodes) | Bloated; compress/rebuild leanly |
| Heavy consolidated docs (56KB-style) | Replace with lean files |
| Single-deck review tooling | Nebula is multi-deck by design |
| Paid/account-gated meta or card sources | Violates free/cost priority |

---

## Running checklist

Baseline. Status: **planning → in progress**.

### Plan (done)
- [x] Destination confirmed (multi-deck CEDH audit: cards, deckbuilding, meta)
- [x] Wayfinder map charted (this file)
- [x] Design inputs reviewed (Plan A + Plan B)
- [ ] Your call — nothing locked yet; see §2 above
- [ ] Out-of-scope items confirmed with user

### Tick 0 — Frozen contract (in progress)
- [ ] Draft audit contract + report structure

### Tick 1 — Importer + snapshot + fingerprint (next)
- [ ] Deck import (Moxfield/Archidekt/pasted)
- [ ] Zone parsing + canonical identities
- [ ] Fingerprint + version freeze

### Tick 2 — Card-truth store
- [ ] Scryfall bulk store + provenance
- [ ] Rules index + legality sources

### Tick 3 — Legality & construction
- [ ] Rule 903.5a, commander config, color identity, singleton, bans

### Tick 4 — Deterministic metrics
- [ ] Role taxonomy + densities + denominators

### Tick 5 — Commander & combos
- [ ] Commander first-class + combo map

### Tick 6 — Packages & relationships
- [ ] Package map + resource collisions

### Tick 7 — External structural tools
- [ ] Deckcipher + mana calculator comparison

### Tick 8 — End-to-end report
- [ ] Per-deck report format (doc-2 12 sections)

### Tick 9 — Simulation (castability)
- [ ] Baseline-vs-variant harness

### Tick 10 — Tournament + meta
- [ ] Multi-deck meta table

### Tick 11 — Theory routing
- [ ] Topic routing + attribution

### Tick 12 — Recommendations
- [ ] Triage + replacement pairs

### Tick 13 — Delivery + regression
- [ ] Report delivery + regression suite

---

*Template: codie-audit v0.7.3 + codie vault builds + St-Milton1013/Codie repo. Planner: wayfinder; keep-changed doc: NEBULA-CHECKLIST.md.*
