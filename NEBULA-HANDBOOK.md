# NEBULA — Handoff Doc (for a new chat)

**For:** every new chat that continues nebula planning.
**Project:** new codie iteration (`nebula`).
**Workspace:** `/c/Users/Main/Desktop/project frontgate/Projects/nebula/`
**Source of truth (codie):** `C:\Users\Main\Desktop\project frontgate\Projects\Codie\`
**GitHub:** `https://github.com/St-Milton1013/nebula` (public, `main`, brand-new).

---

## 0. Why this doc exists + the master rule

The previous planning pass made mistakes: it locked carry-over decisions into the doc ("Decisions so far"), presented open possibilities as a closed plan, and queued tickets before deciding anything. The user's direction was explicit:

> **single-deck reviews + two-pass critic (Jin), nothing sealed, nothing decided.**

**Master rule for every new chat:** nothing is sealed until the user says so. No "Decisions so far", no DONE marks, no roadmap, no tickets until a decision exists.

---

## 1. How a new chat must work (the flow)

1. **Read this doc.** (Start here.)
2. **Confirm the 2 open directions:** single-deck + two-pass critic (Jin).
3. **Pick ONE open item** from §2 (the list below) and decide impliment OR not.
4. **Lock only that item.** Everything else stays open.
5. **Repeat, one item at a time.** No multi-item decisions before the current one is confirmed.
6. **No code in this session.** Code is written in other chats; this session is planning only.

---

## 2. The list of things from codie that are available to decide on

(Presented as checkboxes — each is a "decide impliment or not" item. None are decided.)

**From Plan A (249-step audit-tool design):**
- [ ] P0 → P3 build order (evidence-first: finish evidence pipeline before expanding Laya)
- [ ] KEEP codie's 70-question Laya framework (decision-support layer)
- [ ] KEEP codie's card-truth + rules-index + deck-validation (data layer)
- [ ] KEEP & refactor codie's meta pipeline (TopDeck, CEDHStats, CEDHData)
- [ ] KEEP file-backed, versioned evidence + provenance (frozen snapshots, fingerprints)
- [ ] DISCARD Goal Engine, Jin, V3 UI, theory node graph, heavy docs, single-deck tooling
- [ ] Report: one per-deck report + cross-deck meta tab (Plan B style)
- [ ] Simulation/castability first (Policy mode, ~5000 games)

**From Plan B (audit report plan, 12 sections):**
- [ ] 12-section audit report structure (per-deck)
- [ ] Cross-deck meta tab
- [ ] Jin's two-pass critic as the review component

**Design constraints (user-endorsed direction, not decided):**
- Modular: parts feed each other but are NOT dependant; each module independently usable; a module failure returns `AVAILABLE`/`PARTIAL`/`UNSUPPORTED` and the report keeps going.
- Meta sources: all free (TopDeck, CEDHStats, CEDHData) — usable as long as used properly.

---

## 3. Open questions (fog) to settle as we pick

- Deck ingestion priority — Moxfield vs Archidekt.
- Base engine — reuse codie-audit v0.7.3 skill, or rebuild?
- Laya question subset vs lean.
- Simulator runner — local Deckcipher via browser, or in-house?
- Report format — single report per deck, or combined with meta?
- Meta source set — confirm all usable (TopDeck, CEDHStats, CEDHData).

---

## 4. Current repo state

- `nebula/NEBULA-CHECKLIST.md` — open menu (nothing sealed).
- `nebula/README.md` — landing page.
- `github.com/St-Milton1013/nebula` — public repo, `main`.
- Codie source of truth at `C:\Users\Main\Desktop\project frontgate\Projects\Codie\`.

---

## 5. Red flags — STOP if you see these

- A "Decisions so far" / "DONE" / "tickets queued" section.
- Presenting a possibility as a plan.
- Locking an item without the user choosing it.
- Mentioning multi-deck as the primary target (single-deck is the confirmed direction).

---

*Handoff driven from codie-audit v0.7.3 + codie vault + St-Milton1013/Codie repo.*
