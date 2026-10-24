# IDEA — TopDeck.gg Top-16 Meta Comparison

**Idea ID:** `ideas.topdeck_meta`
**Status:** PROPOSED — confirmed as a viable option, NOT implemented
**Owner:** nebula design (user)
**Date:** 2026-10-24

---
## Confirmation of feasibility

We verified locally that the TopDeck data is available in the Codie repo config:
- **400 top-16 decks** across **25 CEDH tournaments** (16 finishers each)
- Data is in `mtg_laya_project/config/topdeck_tournament_top16.json` (raw text decklists) + `topdeck_events.json` (tournament metadata)
- Format field = `EDH` for all 25; `cedh_eligibility` = `CANDIDATE_UNCONFIRMED` for all

So: **yes, it is an option we can note as a potential idea**. No implementation, no data collection, no live API calls.

---
## What this would do

Compare a deck's archetype stance (turbo/stax/control/storm) against the CEDH
meta as derived from TopDeck Top-16 decks:

```
User deck (audit) ──► archetype.scores
                        │
                        ▼
        TopDeck meta reference (400 top-16 decks)
                        │
                        ▼
   Meta distribution: where do top-16 decks concentrate?
                        │
                        ▼
   User deck position + similarity to nearest archetype cluster
```

### Pipeline
1. **Parse** 400 text decklists → canonical card lists (using `cards.json`).
2. **Compute** archetype scores per deck with the same deterministic pipeline (steps 7–9).
3. **Build** meta distribution — deck counts per quadrant, top-quartile "extreme" reference.
4. **Compare** — overlay user's deck position, nearest top-16 archetype cluster, axis-sigma deviations.

### Output format
```
META REFERENCE (TopDeck Top-16, 25 CEDH tournaments / 400 decks)
  Quadrants: Turbulent 42 · Saxic 98 · Control 121 · Storm 139
  Your deck: TURBO-STORM (turbo=62·stax=38·control=31·storm=69)
  Comparator: closest cluster = "Storm-Combo" (n=87)
  Caveat: 400 decks = Top-16 only; eligibility = CANDIDATE_UNCONFIRMED
```

---
## Guardrails

- Meta comparison is a **reference context**, not a judgment. Top-16 decks are
  the most competitive tier; matching a top-16 archetype is not "good" or "bad" —
  it's a reflection of the format's extreme end.
- `cedh_eligibility = CANDIDATE_UNCONFIRMED` must be cited.
- Compute all meta decks locally (no cloud upload). Use local `cards.json` + existing metric pipeline.
- No live TopDeck API calls during the audit — use the cached snapshot.

---
## Caveats to state in any report

- **400 decks is a top-16 sample, not the full CEDH meta** — it's the most competitive
  tier, which is exactly what "more extreme decks" means, but it's not the whole format.
- **`cedh_eligibility = CANDIDATE_UNCONFIRMED`** for all 1275 tournaments —
  flag it clearly rather than over-claiming confirmed cEDH status.
- Data is static (as of `retrieved_at`), not live.

---
## Reference location

- Full design/plan: `NEBULA-DESIGN-PLAN.md` (main repo)
- This idea: `NEBULA-IDEAS/` folder
- See also: `NEBULA-ARCHETYPE-CLASSIFICATION.md`, `NEBULA-META-COMPARE.md`
