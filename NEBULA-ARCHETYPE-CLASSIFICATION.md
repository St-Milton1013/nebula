# NEBULA — CAPABILITY — ARCHETYPE BAND (turbo/stax/control/storm)

**Capability ID:** `archetype.classify` (proposed)
**Owner:** Codie (measurement) + Jin (interpretation)
**Type:** Report enhancement — a bar/quadrant classification of a deck's archetype stance.
**Status:** PROPOSED (not implemented; no code written; no data collected for it yet).
**Prereqs:** Steps 7 (metrics), 9 (roles/packages) already produce the raw signal. No new data source.

---
## 1. Intent

Classify each audited deck on two axes, so the report shows where it sits relative to the format's more extreme archetypes:

- **Axis A — Speed/tempo:** `turbo` (fast, combo/tempo, low loadout) ↔ `stax` (slow, anti-fly, economic, heavy, hard to read).
- **Axis B — Card-advantage intensity:** `control` (steady, removal-based, steady) ↔ `storm` (maximum draw, mass, endgame card advantage).

A deck plots on a 2×2 grid (two polarities, not a single "bar"). The simplest deliverable is a 2×2 quadrant result + two polar bar tick-marks (one per axis), e.g.:

```
          STORM (high draw / mass)
             ▲
             │   Storm-Stax   │  Storm-Control
             │                │
Turbo (fast) │  Turbo-Storm   │  Turbo-Control
             │                │
             ▼
          STAX (slow / economic)
             ──────────────────► TSX (slow / steady)
```

Each axis is scored 0–100; the quadrant is the nearest bucket; the report prints the axis ticks as a "bar."

---
## 2. Signals — what data drives the classification

All signals come from **already-computed** pipeline outputs (no new sources):

| Signal | Source (Step) | What it measures |
|---|---|---|
| `castability_stage.cast` | 7 | Fast-cast pieces reachable early |
| `castability_stage.assembly` | 7 | Slow-play / assembly pieces (late + grinding) |
| `combo_density` | 7 | Combo-force / tempo pieces |
| `mana_curve` | 7 | Fast curve (low CMC) = turbo; heavy curve = stax |
| `tutor_density` | 7 | Card draw / acceleration (more = storm-leaning) |
| `protection_density` | 7 | Removal / defense (more = control-leaning) |
| `combo_density` + `protection_density` ratio | 7 | Storm (draw+both) vs control (protection) |
| `roles.cards` | 9 | Resource generation, card draw, destruction, protection |
| `roles.resource_generation` count | 9 | Mana/resource production |
| `tournament_usage.card_prevalence` | 10 | Popular in the frozen cohort |
| `deck_size` | 7 | Heavy loadout = stax-leaning; light = turbo |

The role graph (Step 9) is the most informative: a deck with many `resource_generation` + `card_draw` roles → storm; many `protection` roles → control; many `card_advantage` + `combo_density` → turbo; many `protection` + heavy curve + high `assembly` → stax.

### 2.x Scoring (draft)

Each axis gets a 0–100 score using a deterministic, transparent formula over the normalized metrics. Example (to be finalized with the user):

```
turbo_score = 0.35 * norm(combo_density, 0, 10)
            + 0.25 * norm(castability_stage.cast, 0, max_cast)
            + 0.20 * (1 - norm(mana_curve_center, 0, 5))   // fast = low center CMC
            + 0.20 * norm(tutor_density, 0, 12)

stax_score  = 0.35 * norm(mana_curve_center, 0, 5)         // heavy = high center CMC
            + 0.25 * norm(mana_curve_tail, 0, 3)           // 4-5 cards
            + 0.20 * norm(protection_density, 0, 12)
            + 0.20 * norm(castability_stage.assembly, 0, max_assembly)

control_score = 0.40 * norm(protection_density, 0, 12)
              + 0.30 * norm(resource_generation, 0, 10)    // steady mana
              + 0.30 * norm(tutor_density, 0, 12)          // card advantage (without mass)

storm_score = 0.40 * norm(tutor_density, 0, 12)            // draw = storm
            + 0.30 * norm(combo_density, 0, 10)
            + 0.20 * norm(resource_generation, 0, 10)
            + 0.10 * norm(castability_stage.cast, 0, max_cast)
```

(All `norm(x, 0, max)` = min-max normalization across the audit population, or against a fixed reference set — decision pending.)

Quadrant = argmax over the four combos. Axis ticks printed as `[turbo 30 ────── 70 stax]`.

---
## 3. Where it plugs into the pipeline

```
Step 7 (metrics) ──► archetype.scores (turbo/stax/control/storm)
Step 9 (roles/packages) ──► archetype.roles (role profile)
Step 10 (metagame) ──► archetype.popularity (cohort prevalence)
Step 15 (report) ──► archetype bar + quadrant + descriptors
```

It is a **derived classification**, not a new evidence source. The report prints it as a caption under the deck facts, not as a verdict.

---
## 4. What the report shows

```
ARCHETYPE STANCE
  Axis 1 (speed):   [====TURBO=====──] 55 / 45
  Axis 2 (draw):    [──CONTROL──]───── 30 / 70  STORM

  Quadrant: TURBO-STORM
  Descriptor: "Combo-timed, fast curve, light loadout; draw on the low side."
  Evidence: combo_density=8 (top-quartile), castability.cast=22, mana_center=2.4,
            tutor_density=6, protection_density=5, roles: card_advantage=4, resource_gen=1.
  Caveat: classification is heuristic; compare to cohort prevalence (metagame.json).
```

---
## 5. Guardrails (from the design plan)

- **Heuristic, not authoritative.** The classification is a measurement, not a verdict. State it as "stands here," not "this is the truth."
- **No single overall score.** The two axes are separate dimensions (like Step 6/7 guardrails).
- **Caveat in the report.** Always cite the evidence and the cohort prevalence; note when the sample is small/biased.
- **Not a ranking.** `storm` is not "better" than `control`; it's a different stance. The metagame layer separates "common" from "improving."
- **No automatic promotion.** The classification does not change the deck; it's a readout.

---
## 6. Risks & unknowns

1. `norm()` reference set — normalize against the current audit population (each report) or a fixed curated set? Decision pending.
2. Quadrant granularity — nearest bucket is coarse; a continuous "where on the bar" is more useful. Diddle.
3. Label semantics — "turbo/stax/control/storm" have cEDH-specific meanings; verify with the user's definition before locking labels.
4. Coupling — scores depend on Steps 7/9/10 outputs; if those change, archetype scores must be recomputed. Confirm dependency direction.

---
## 7. Next steps (if the user picks this)

1. Lock the axis definitions (turbo/stax/control/storm).
2. Freeze the scoring formula (or choose continuous vs discrete).
3. Add `archetype.scores` to Step 7's output schema.
4. Wire Steps 9/10 columns into the score.
5. Render the bar + quadrant in the report (Step 15).
6. Run a pilot on 5–10 known extreme decks to sanity-check the labels.

---
*Capability concept for the tool — part of the nebula design plan. Not implemented; nothing committed.*
