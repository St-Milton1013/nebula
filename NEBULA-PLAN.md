# NEBULA — PLAN.md

**Project:** nebula = new codie iteration (the handoff repo)
**Repo:** `github.com/St-Milton1013/nebula` (public, `main`)
**Workspace:** `/c/Users/Main/Desktop/project frontgate/Projects/nebula/`
**Codie source of truth:** `C:\Users\Main\Desktop\project frontgate\Projects\Codie\`
**Audit engine:** codie-audit skill v0.8.0 (codieaudit profile)
**Direction:** single-deck reviews + two-pass critic (Jin); nothing sealed, nothing decided.

> Folder note (verified, no fix needed): the real folder is `project frontgate` — **no** space before "gate". The handbook, checklist, and this file all use that correct spelling.

---
## 1. What was considered — every variation of the codie project

| Variation | Folder / artifact | Role | Nebula uses it as |
|---|---|---|---|
| **C1. Codie repo (codie body of work)** | `project front gate/Projects/Codie/` | Prior codie: 70-q Laya framework, 9-stage audit pipeline, theory corpus, rules index, deck-validation, meta pipeline, 8.8k tournaments, 300 players | **Source of truth for the data layer + framework patterns** — not a running target |
| **C2. Laya knowledge base** | `mtg_laya_project/` | Laya framework (70 questions, 19 parts), node corpus, corpus_pack.json, tournament/player data | **Pattern + question set** — kept as decision-support only, leaned, per handbook |
| **C3. codie-audit skill** | `AppData/Local/hermes/profiles/codieaudit/skills/codie-audit/` (v0.8.0) | Active audit engine (10-stage pipeline, evidence-first) | **Base engine** — reuse, don't rebuild |
| **C4. Codie vault** | `Project Control` + `Codie` repo + `Hidden Gems` | Governance, decisions, ADRs, research, task records | **Reference layer** — read-only for planning |
| **C5. Local fallback data** | `Project\Codie\Research\` (CedhStats, LearnCEDH) + `TOPDECK_GG_API_KEY.txt` | Free meta sources | **Meta pipeline** — all free, usable |

---
## 2. Design constraints (user-endorsed, decided in principle — to be locked per item)

1. **Modular.** Parts feed each other but are NOT dependent. Each module independently usable.
2. **Fault-tolerant.** A module failure returns `AVAILABLE`/`PARTIAL`/`UNSUPPORTED` and the report keeps going.
3. **Meta sources all free.** TopDeck, CEDHStats, CEDHData — usable, as long as used properly.
4. **Single-deck is the primary target.** No multi-deck as a primary use case.

---
## 3. The build order (Plan A — P0 → P3)

Order chosen by the user (evidence-first). Each phase gates the next.

- **P0 — Data & truth layer (already existent; verify/use).**
  - card-truth (`cards.json`) + rules-index — KEEP codie's.
  - deck-validation (`validate_deck`) — KEEP codie's MCP validator.
- **P1 — Evidence pipeline (evidence-first core).**
  - Deck ingestion (Moxfield primary / Archidekt fallback) + evidence packet.
  - File-backed, versioned evidence + provenance (frozen snapshots, fingerprints).
- **P2 — Laya decision-support layer.**
  - Keep codie's 70-question Laya framework, leaned, per user direction.
  - Report: one per-deck report (Plan B structure).
- **P3 — Meta + reviewer.**
  - Refactor codie's meta pipeline (TopDeck, CEDHStats, CEDHData).
  - Jin's two-pass critic as the review component (bounded: reads evidence, returns flags, calls no tools, never rewrites).

---
## 4. Everything the user wants to do (open items — all NOT decided until chosen)

### Deck-review scope
- [ ] **Single-deck review** (confirmed direction — keep as the primary; multi-deck is a red flag, not a goal)

### Analysis approach
- [ ] **Two-pass critic (Jin)** as the adversarial review layer — bounded critic: reads evidence, returns structured flags, calls no tools, never rewrites
- [ ] **Evidence-first pipeline** (codie's 9-stage / 10-stage), with the 70-question Laya in decision-support only

### Evidence & data
- [ ] **Meta: TopDeck + CEDHStats + CEDHData** (all free) — used in the audit
- [ ] **Card truth + rules index** — keep codie's existing
- [ ] **Simulation (castability)** — optional, later (Policy mode, ~5000 games)
- [ ] **Deckcipher / mana calculator** — optional, later

### Report
- [ ] **12-section audit report structure** (per-deck)
- [ ] **Cross-deck meta tab** (Plan B style — once per-deck reports exist)

### Governance (nothing sealed until the user chooses)
- [ ] Nothing locked; nothing "Decisions so far"; no DONE marks; no tickets until a decision exists
- [ ] One item decided at a time

---
## 5. Open questions (fog) to settle as we pick

1. **Deck ingestion priority** — Moxfield vs Archidekt.
2. **Base engine** — reuse codie-audit v0.8.0 (codieaudit profile), or rebuild?
3. **Laya question subset vs lean** — decide when we have an audit.
4. **Simulator runner** — local Deckcipher via browser, or in-house?
5. **Report format** — single report per deck, or combined with meta?
6. **Meta source set** — confirm all usable (TopDeck, CEDHStats, CEDHData).

---
## 6. Red flags — STOP if you see these

- A "Decisions so far" / "DONE" / "tickets queued" section.
- Presenting a possibility as a plan.
- Locking an item without the user choosing it.
- Mentioning multi-deck as the primary target (single-deck is the confirmed direction).

---
## 7. Session rules

- **No code in this session.** Planning only; code is written in other chats.
- This session owns the roadmap and tracking only.
- Each item is locked exactly when the user confirms it, one at a time.

---
*Generated from: NEBULA-HANDBOOK.md (handoff), NEBULA-CHECKLIST.md (open menu), README.md (landing page), codie repo (Projects/Codie), Laya knowledge base (mtg_laya_project), codie-audit skill v0.8.0.*
