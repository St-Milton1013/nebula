---
id: nebula-research-queue
project: nebula
type: queue
status: ACTIVE
created: '2026-11-21'
updated: '2026-11-21'
---

# NEBULA — Research Queue

Items here are research, not tickets. Each one states the question, the evidence that
would answer it, and the build it gates. An item leaves this file when it produces a
decision, not when it produces a document.

---

## R1 — How should the tool *recommend* a primary plan?

**Why.** D12 has the pilot declare the plan; R1 asks whether Nebula can propose one to
accept or edit. A stax list and a consult list with the same commander pair need different
plans, so the recommendation cannot come from the commander alone.

**Candidate evidence, cheapest first**

1. What plans do *winning lists of this commander pair* run? Computable from TopDeck
   standings once §6 exists — the decklist is the plan, in aggregate.
2. Spellbook variant presence: a list with 3 Breach variants and 0 Ad Nauseam variants is
   a Breach deck, if the variants are complete.
3. Tagger role mix (ramp/draw/tutor/interaction densities) as a weak prior only.
4. Commander tags, for archetype hints — weakest of the four; a commander does not fix a
   plan.

**Shape of the answer.** Not a deterministic module. A short ranked list of candidate
plans with the evidence line behind each, handed to Laya/Jin for the wording. The pilot
still confirms.

**Gates.** §8 package analysis for decks the pilot cannot classify confidently; the
recommendation half of triage. Does **not** gate v1.

---

## R2 — The package model

**Why.** D14 keeps cuts and adds out of v1 precisely because this does not exist. Steps
89–105 of the design are the specification, and they are demanding: packages, enablers,
outputs, dependencies, missing conversion steps, resource collisions, orphaned cards.

**Prior art, reviewed 2026-11-22.** Codie holds an approved-deferred plan —
`Projects/Codie/Plans/APPROVED TBD - Relationship and Package Intelligence.md`
(`APPROVED_TBD / NOT ACTIVE`, Phase40K core externally accepted). It is reference for
Nebula, not authority: it activates nothing here (D1, D2).

What that plan fixes as vocabulary, worth adopting as-is:

| Constraint | Meaning for us |
|---|---|
| 7 relationship families | card↔card, card↔package, card↔commander, package↔package, card↔combo, card↔meta, package↔strategy |
| 4 basis kinds | rules/function, observed tournament evidence, source-authored strategic claim, derived analysis — every relationship names one |
| confidence only for interpretive links | a rules fact is not "80% confident" |
| no graph database as canonical storage | graph views are rebuildable indexes over file-backed records |
| replacement coverage in any removal/addition analysis | a cut must account for what the slot still needs |
| metric lineage | every derived number reproducible from snapshot + version |

**The gap that matters.** `codie/analytics/relationship_metrics.py` and
`relationship_population.py` already implement the arithmetic — support, directional
confidence, dependence delta, lift, leverage, Jaccard, PMI over typed endpoints that
include `package` and `commander_pair`, with population manifests and observation
statuses. **The arithmetic exists; the packages do not.** The plan's own dependency list
says so: *attributed package definitions*. The theory node for package design
(`nodes/01_Topics/30-package-design.md`) is an empty scaffold — "content pending
extraction" — so the corpus cannot supply definitions either.

So R2 splits:

### R2a — Deriving packages from relationships (D17)

Packages are **computed, not authored**. The question is how to compute them so the answer
is stable, reproducible, and named — not how to write them down.

**Mechanism under consideration**

1. **Population.** Exact commander pair, events at or above the floor (D10), rolling
   window, minimum N lists. The population is a parameter of the answer, not a footnote:
   "the TyKraum Breach package" is only meaningful inside a stated population.
2. **Edges.** Card↔card weight from the relationship metrics that already exist in
   `codie/analytics` (leverage, lift, PMI, Jaccard). Prefer **leverage** — observed minus
   expected co-occurrence — because PMI and lift explode on rare pairs.
3. **Support floor.** A pair must appear in a minimum share of the population's lists or it
   is not an edge. Without this, a pair seen once carries an enormous lift and every
   package is noise. This is the single most important parameter.
4. **Clustering.** Community detection over that graph, with a minimum community size and
   a resolution parameter.
5. **Naming.** A community that contains a Spellbook combo piece or a declared win
   condition takes **that** name. Communities without an anchor stay unnamed: reported by
   dominant Tagger role and card count, flagged as `UNNAMED_CLUSTER`. Naming is the one
   step that cannot be made objective, so the design defers to an anchor rather than to
   whoever writes the report.
6. **Stability.** Bootstrap-resample the population's lists; publish a package only if the
   cluster recurs in most resamples. Unstable clusters are dropped, not labelled.

**What this buys, honestly.** No stale list, no authoring labour, and every package
carries its population, metric version and stability score — so "why is this a package?"
has an answer that isn't "because someone said so." The failure mode moves from *stale* to
*unstable*, and step 6 is what covers it.

**The two ways this fails**

- **Thin samples.** A commander pair with 40 lists cannot support pair-level co-occurrence;
  a support floor that protects the numbers may also leave no packages at all. Expect
  popular pairs to produce packages and niche pairs to produce none, and say so rather
  than lowering the floor.
- **The staple blob.** High-inclusion cards connect to everything. If the weight is not
  support-aware, the first "package" discovered is always *the deck*.

**Gating.** Needs §6 tournament ingestion before anything can be computed. That puts D14's
cuts and adds behind §6, which is a scheduling change worth knowing now rather than later.

### R2b — Relationship metrics (adapting prior art)

- Codie's metric families are sufficient for "how often do these two cards appear
  together in winning lists of this pair."
- Nebula must decide what to take as a *design* (metric definitions, packet shape,
  population manifest) while writing its own code (D1: no `codie.*` imports).
- Open: whether to compute these at all in v1, given D14 and the fact that tournament
  ingestion (§6) is not built.
- Gates: the evidence behind any future cut/add proposal.

## R3 — Tagger coverage at scale

**Why.** Role coverage came out 90% on two decks, and the misses clustered on cEDH
interaction (Deflecting Swat, Misdirection, Commandeer, Brain Freeze). If the untagged rate
is 30% and concentrated in protection, the coverage table understates interaction on every
list.

**Method.** 200 real tournament lists, run the existing classifier, report: untagged rate,
the untagged cards ranked by frequency, and whether misses cluster by role.

**Gates.** Whether role coverage ships as a headline feature or as a caveated section.

---

## R4 — Does the 30-player floor hold?

**Why.** D10 sets 30 and makes it adjustable. Nobody has checked what that admits.

**Method.** Apply 30 / 32 / 64 to the 2025–2026 TopDeck events: how many events qualify,
what share of standings rows, and whether the composition of commanders changes at each
threshold. If 30 admits 4-round local events that 64 excludes, that is a data-quality
decision the pilot should make knowingly.

**Gates.** Nothing structural — it either validates the default or moves it.

---

## Parked behind v1.1

- **Theory source ledger** — underlying work, location, authoring method, rights status,
  quotation vs paraphrase per passage. Required before §9 appears in a shared report
  (D9 currently keeps reports private, so this waits).
- **Jin critic contract** — the flag schema does not exist; authoring it is design, then
  the adherence/determinism test the research report asked for.
- **Simulator coverage** — 0/10 win-condition packages have action support. Revisit only
  if the action catalog changes.
