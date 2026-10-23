# NEBULA — Open (nothing decided, nothing sealed)

**Status:** OPEN — no decisions made, nothing sealed so far.
**Workspace:** `/c/Users/Main/Desktop/project frontgate/Projects/nebula/`
**Source of truth (codie):** `C:\Users\Main\Desktop\project frontgate\Projects\Codie\`
**Codie GitHub:** https://github.com/St-Milton1013/Codie
**GitHub repo (new):** https://github.com/St-Milton1013/nebula

---

## Direction you've given (open — not sealed)

1. **Single-deck** reviews, not multi-deck.
2. **Two-pass critic (Jin):** a bounded second pass over an evidence packet — it reads the evidence, returns structured adversarial flags, calls no tools, and never rewrites. Keep as a review component.

---

## What we start from (fixed facts)

- `codie-audit` v0.7.3 skill (existing audit engine, decision-support layer).
- codie vault + GitHub codie repo (as the prior codie body of work).
- Two design inputs:
  - `pasted_content_2026-10-23_21-46-12-625_0302b9.txt` — the 249-step audit-tool design (evidence pipeline + P0–P3 build order).
  - `pasted_content_2026-10-23_21-46-28-820_e40f9b.txt` — the audit report plan (12 sections).

---

## Open areas — choose, piece by piece

(Each is a possibility, all OPEN / NOT DECIDED until you say otherwise.)

### Deck-review scope
- [ ] Single-deck review (your direction — to confirm)

### Analysis approach
- [ ] Two-pass critic (Jin) as the adversarial review layer
- [ ] Evidence-first pipeline (codie's 9-stage), with the 70-question Laya in decision-support only

### Evidence & data
- [ ] Meta: TopDeck/TopDeck, CEDHStats, CEDHData (all free) — used in the audit
- [ ] Card truth + rules index — keep codie's, or rebuild
- [ ] Simulation (castability) — optional, later
- [ ] Deckcipher / mana calculator — optional, later

### Report
- Open once we have an audit; then decide format.

### Governance
- Nothing sealed until you choose.

---

## Forward

None queued. Items become tickets only when you choose them, one at a time.

---

## Not yet specified (fog)

Open questions to settle as we pick:
- Deck ingestion priority — Moxfield vs Archidekt.
- Base engine — reuse codie-audit v0.7.3 skill, or rebuild?
- Laya question subset vs lean — decide when we have an audit.
- Simulator runner — local Deckcipher via browser, or in-house?
- Report format — single report per deck, or combined with meta?
- Meta source set — confirm all usable (TopDeck, CEDHStats, CEDHData).

---

## Status

**Open.** This document is a menu of possibilities, not a plan, and not a roadmap. No item is locked, no ticket is queued, nothing is sealed.

---

*Template: codie-audit v0.7.3 + codie vault + St-Milton1013/Codie repo. Notebook: `NEBULA-CHECKLIST.md`.*
