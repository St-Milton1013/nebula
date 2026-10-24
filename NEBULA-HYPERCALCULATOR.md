# NEBULA — HYPERCALCULATOR ADAPTER

**Capability ID:** `archetype.hypercalculator`
**Owner:** Codie (calculation) + Jin (interpretation)
**Date:** 2026-10-24
**Status:** DESIGN REFERENCE — not implemented

---

## 1. Package contents

The **Hypercalculator** adapter computes probability/chance metrics for cards
in a deck, answering the question: *"What are the chances of drawing or
finding specific cards in my deck?"*

### What it calculates

All probabilities are **tag-based** — not card-specific. The calculator groups
cards by their tags (from the Tagger adapter) and computes:

| Metric | Description |
|---|---|
| **Tag draw probability** | Chance of drawing at least one card with a specific tag |
| **Opening hand tag distribution** | How many cards with each tag are in the opening hand |
| **Combo tag probability** | Chance of drawing all required tags for a specific combo |
| **Mana curve odds** | Distribution of card types (land, creature, spell) in the opening hand |

### Example: "Chance of finding a card with the 'ramp' tag"

Given a mainboard of **N cards** (99 for standard, more for partner/companion decks)
with **K cards tagged** `ramp`:
- Opening hand (7 cards): ~47% chance of drawing at least 1 ramp card

Probability uses the hypergeometric distribution:
```
P(X >= 1) = 1 - P(X = 0)
P(X = 0) = (N - K) / N * (N - K - 1) / (N - 1) * ... (n terms)
```

For example, with **N = 100** (100-card mainboard including a partner):
- K = 8 ramp cards, n = 7 draws
- P(X = 0) = (92/100) * (91/99) * (90/98) * (89/97) * (88/96) * (87/95) * (86/94) ≈ 0.52
- P(X >= 1) = 1 - 0.52 = 0.48 (48%)

### Underlying math

All probabilities use the **multivariate hypergeometric distribution**:

```
P(X >= k) = probability of drawing at least k cards with a given tag
```

Given:
- `N` = deck size (actual mainboard count, not hardcoded)
- `K` = number of cards with the tag
- `n` = number of cards drawn (7 for opening hand)
- `k` = target count (1 for at least one)

This is exact — not Monte Carlo estimation.

### Inputs

| Field | Type | Required | Notes |
|---|---|---|---|
| `decklist` | array | yes | Mainboard card list (non-commander, non-partner, non-companion) |
| `deck_size` | integer | yes | Actual mainboard card count (from deck validator, not hardcoded 99) |
| `tags` | object | yes | Tag-to-card mapping (from Tagger adapter) |
| `draws` | integer | no | Number of draws (default: 7 for opening hand) |
| `targets` | object | no | Per-tag target counts |

**Important:** `deck_size` is **not hardcoded**. The `deck_validator` adapter
detects partners/companions and returns the actual mainboard count. The
hypercalculator uses that count, not a fixed 99.

### Outputs

| Field | Type | Notes |
|---|---|---|
| `tag_draw_probability` | object | For each tag: card count, opening hand probability |
| `opening_hand_distribution` | object | Lands, creatures, spells, and tag counts in opening hand |
| `combo_tag_chances` | object | Probability of drawing all tags for key combos |
| `mana_curve` | object | Distribution by card type (land/creature/spell) |

### Caveats

- Assumes a well-shuffled deck (uniform random distribution)
- Does not account for mulligan, draw spells, or card effects that change the deck
- Probabilities are theoretical, not empirical
- The `urn` library provides exact hypergeometric calculations (no Monte Carlo approximation)

---

## 2. Integration with other components

| Source | Data | Package use |
|---|---|---|
| **LearnCEDH** | Deck summary, performance metrics | What the deck is (narrative) |
| **Commander Spellbook** | Combo data | What the deck can do (gameplan) |
| **Tagger** | Card tags (mechanical/behavioural) | What the cards do (behavioural) — **key input** |
| **Scryfall** | Card info | What the cards are (structural) |
| **Hypercalculator** | Probability metrics | Chances of drawing cards with specific tags |

The Hypercalculator provides the **probabilistic context** to the deck analysis,
complementing the structural, behavioural, and gameplan data.

---

## 3. Open questions (resolved)

### 3.1 Target population

**Decision:** Calculate probabilities for tags, not individual cards. The
adapter groups cards by tag and computes the chance of drawing at least one
card with each tag.

### 3.2 Draw context

**Decision:** Support opening hand (7 cards) and arbitrary draw counts.
The adapter also computes the probability of drawing specific tags at
different stages of the game (turn 1, turn 5, etc.).

### 3.3 Deck composition

**Decision:** The adapter works from the decklist (99 cards for Commander).
The Tagger adapter provides the tag-to-card mapping. The hypercalculator
aggregates tags and computes probabilities.

---

## 4. Implementation note

### Files to create

| File | Purpose |
|---|---|
| `NEBULA-HYPERCALCULATOR.md` | **This document** — the hypercalculator adapter blueprint. |
| `archetype/hypercalculator.py` | New module: `num_adapter(mode="hypercalculator", decklist, tags, options)` — computes probabilities. |

### Library dependencies

| Dependency | Purpose |
|---|---|
| `urn` | Multivariate hypergeometric distribution |
| `statistics` | Statistical calculations |

### Constraints

- Read-only computation (no data submission)
- Caching allowed locally for audit speed
- No live API calls needed (pure computation)

---

## 5. Reference — Tymna Thrasios example

### Deck composition (estimated)

| Card type | Count |
|---|---|
| Lands | 20 |
| Creatures | 25 |
| Spells | 40 |
| Total mainboard | 85 (standard Commander) |

*Note: decks with partners/companions will have a larger mainboard (e.g., 100+ for a 100-card mainboard with a partner). The hypercalculator uses the actual mainboard count from the deck validator.*

### Tag aggregation (from Tagger)

| Tag | Cards with tag |
|---|---|
| `ramp` | 8 |
| `draw engine` | 5 |
| `mana sink` | 5 |
| `card advantage` | 12 |
| `board wipes` | 6 |

### Hypercalculator outputs

| Tag | Cards | Opening hand prob (≥1) |
|---|---|---|
| `ramp` | 8 | ~47% |
| `draw engine` | 5 | ~33% |
| `mana sink` | 5 | ~33% |
| `card advantage` | 12 | ~60% |
| `board wipes` | 6 | ~39% |

*Probabilities are calculated using N = 85 (actual mainboard count), not hardcoded 99.*

### Example results

**Opening hand (7 cards) — chance of drawing at least 1 ramp card:**

```
P(X >= 1) = 1 - P(X = 0)
P(X = 0) = (91/99) * (90/98) * (89/97) * (88/96) * (87/95) * (86/94) * (85/93)
P(X = 0) ≈ 0.52
P(X >= 1) = 1 - 0.52 = 0.48 (48%)
```

**Opening hand (7 cards) — chance of drawing at least 1 card with 'card advantage' tag:**

```
P(X >= 1) = 1 - P(X = 0)
P(X = 0) = (87/99) * (86/98) * (85/97) * (84/96) * (83/95) * (82/94) * (81/93)
P(X = 0) ≈ 0.38
P(X >= 1) = 1 - 0.38 = 0.62 (62%)
```

### Combo tag chances

For the combo "Seedborn Muse + Thrasios, Triton Hero":

| Tag | Cards |
|---|---|
| `card advantage` | 12 |
| `ramp` | 8 |
| `mana sink` | 5 |

Probability of drawing all three tags in opening hand:

```
P(card advantage ∩ ramp ∩ mana sink) ≈ 0.15
```

---

*This completes the hypercalculator adapter design. It provides probability metrics for tag draws and combo chances, complementing the structural, behavioural, and gameplan data from the other adapters.*
