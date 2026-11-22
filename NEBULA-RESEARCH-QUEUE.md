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

1. **Population, widest usable first.** A specificity ladder, because a niche pair cannot
   support pair-level co-occurrence:

   | Level | Population | Use when |
   |---|---|---|
   | `pair` | exact commander pair | the pair has `min_population_lists` lists |
   | `identity` | every deck of the same colour identity | the pair is too thin and pooling is allowed |

   Publish at the **most specific level that passes stability**, always label the level, and
   never compare a `pair` package with an `identity` package as though they were the same
   object. The population is a parameter of the answer, not a footnote: "the TyKraum Breach
   package" means nothing outside the population it was measured in.
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

**On the staple blob — corrected.** Fixing the population to a commander pair *is* the
fix, and leverage finishes it: a card that appears in 98% of the population's lists has an
expected co-occurrence just as high, so its leverage is ~0 and it forms no edge. The
mandatory forty dissolve into the baseline rather than clustering into a fake package.

What survives instead is **trivial** clusters — the mana base, the interaction suite every
list of that identity runs. Three filters handle those rather than one:

- lands are excluded from package membership (they have their own diagnostic),
- a cluster must contain an **anchor** (combo piece or declared win condition) to be named,
- a cluster that is merely the top-inclusion cards of the population is flagged as
  `STAPLE_SUITE`, not presented as a package.

**The remaining risk is thin samples**, which the ladder addresses rather than hides: a
pooled `identity` package is real but less specific, and the level label is what keeps a
reader from mistaking one for the other.

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

## R5 — Recommendation engine at cEDH sample sizes

**Why.** D14 defers cuts and adds until packages exist, and the thing that makes a
recommendation credible is related-card evidence: what else the population plays, what the
slot still needs, what the candidate completes. This is the largest unbuilt piece.

**Prior art already in Codie.** `codie/recommendations/` has nine modules whose docstrings
are explicit that they hold *statistics primitives and do not generate candidates*. What
they do fix is the shape:

```
score =  commander_lift + inclusion_rate + confidence + similarity
       + package_completion + combo_completion + tournament_performance
       + simulation_delta
       - generic_staple_penalty - low_sample_penalty
```

candidate types: `commander_specific`, `source_label_specific`, `package_specific`,
`combo_completion`, `generic_staple`, `meta_tech`. The `low_sample_penalty` term means the
volume problem was anticipated, not discovered.

**What transfers at cEDH scale, and what doesn't.** The eight positive terms split cleanly:

| Term | At small N | Note |
|---|---|---|
| `package_completion` | works | volume-free; needs D17 packages |
| `combo_completion` | works now | volume-free; Spellbook's `almostIncluded` buckets are a ready signal — 74 on the 100-card fixture |
| `tournament_performance` | works, with discipline | needs top-cut vs field **within the same population**, never raw win rate |
| `commander_lift`, `inclusion_rate` | noisy | below ~100 lists per pair the CI is wider than the effect; floor it and label it |
| `similarity` | weak | Jaccard between 100-card lists is dominated by staples |
| `confidence` | keep | it is the label on the others, not a signal itself |
| `simulation_delta` | permanently 0 | D3 parks the simulator; the term exists and can never fire |

So the recommendation order at cEDH scale inverts the EDHREC one: **structure first,
outcomes second, co-occurrence last.** EDHREC can lead with co-occurrence because it has
millions of lists; we have hundreds per pair and should lead with what the deck is missing.

**The volume substitute.** EDHREC does not know who won. TopDeck does. That is the trade:
small N, but every list carries a result — which is why `tournament_performance` is worth
more here than `inclusion_rate`, provided the population and the cut are stated.

**Recommander (recommander.cards), inspected 2026-11-22**

Product, not a reference design. Its aggregate is *all* Commander decks, not cEDH: 4,953
Kraum // Tymna decks indexed, against 595 complete events in our own cache. Two
consequences follow.

*What it is.* A deck-corpus recommender. Public API, no key:
`POST https://api.recommander.cards/public-release/api/decks/recommend/top`, returns up to
200 ranked cards in ~0.4s. A test against the frozen Ishai/Rograkh fixture returned 0 cards
already in the deck, 0 outside the commanders' colour identity, 0 unresolved — and a mix of
cEDH-playable (Red Elemental Blast, Pyroblast, Grim Monolith, Wheel of Fortune, Dispel,
Dizzy Spell) and clearly casual picks (The Queen of Dale, Samut, Steal Enchantment). That is
what an all-Commander model produces on a cEDH list: legal, sensibly filtered, wrong at the
margins that matter.

*What that means for us.* Their co-occurrence volume comes from deck lists, not results, and
we are unlikely ever to match it from tournament data alone. So the goal is not to rebuild
Recommander. It is to use it as a **candidate generator** and re-rank with cEDH evidence:

| API feature | What it does for us |
|---|---|
| `candidate_step: explicit` | rank only cards that appear in our tournament population — their model inside our candidate space |
| `candidate_step: set` | new-set candidates for meta-tech, scoped to colour identity |
| `weighted_deck` (-10..10) | the declared plan (D12) expressed as weights — combo pieces up, ramp down, and the recommendations follow the intent |
| card page `Replaced By` / `Same Job` | replacement coverage, the thing a cut analysis needs and we have no data for |

*Caveats.* `score` is comparable only within one response and has no fixed range. Their docs
say the public release may serve a model trained on a subset of their data. Terms: personal,
non-commercial, attribution, and explicitly no scraping — the API is the sanctioned path.
Sending a decklist there is a new egress, the same class as Spellbook (D15) and needing the
same explicit yes.

**Open**

- Extend D15 to cover Recommander as an approved egress?
- Candidate generation as its own slice, feeding the re-ranker, or fold it into R5 proper?
- Gate the volume terms (show nothing below the floor) or show them with wide intervals?
  Recommendation: gate. A number whose interval spans the decision is not evidence.

**Gates.** D14's cuts and adds; depends on §6 (populations) and D17 (packages).

---

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
