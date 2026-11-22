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

**Questions to settle**

- What is the minimum package record? Candidate: `{name, cards[], enabler[], output,
  requires[]}`, with every membership carrying a one-line reason (never a bare list).
- How are packages identified for a new deck: declared by the pilot, derived from combo
  variants, matched against a template library, or a mix? D12 says declared for the plan;
  packages are finer-grained than the plan and may be derivable.
- What does "missing conversion step" mean operationally — an output with no consumer?
  An engine with no payoff? This needs a definition that a test can check.
- How does a cut get proposed without the audit pretending to know the pilot's intent?

**Inputs already owned.** The Codie recommender data plan (role/relationship weighting,
slot-donor comparison) is prior art for this and should be read before designing fresh.

**Gates.** D14's cuts and adds; §8; the whole triage layer.

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
