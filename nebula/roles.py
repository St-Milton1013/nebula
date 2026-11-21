"""Role coverage from the Scryfall Tagger hierarchy.

Roles are Tagger parents, not a hand-invented list: every anchor below is a tag
that exists in the Tagger tree, and a card counts for a role if any of its tags
has that anchor among its ancestors.

`ROLE_ANCHORS` is the taxonomy. Changing it changes every coverage number, so it
is versioned with the tag store in the report rather than tuned per deck.
"""

from __future__ import annotations

from .cardtruth import CardTruth
from .importer import Deck
from .metrics import is_land
from .tagger import Tags

# role -> (anchor tag label, what the role is for)
ROLE_ANCHORS: dict[str, tuple[str, str]] = {
    "ramp":        ("ramp", "mana acceleration: rocks, dorks, land ramp"),
    "draw":        ("card advantage", "cards in hand: draw, selection, wheels"),
    "tutor":       ("tutor", "finding a specific card"),
    "removal":     ("removal", "answering a permanent"),
    "counter":     ("counterspell", "answering a spell on the stack"),
    "wipe":        ("sweeper", "answering the board"),
    "protection":  ("protection", "keeping your own things alive"),
    "stax":        ("hate", "taxing or denying opposing resources"),
    "recursion":   ("recursion", "getting cards back from the graveyard"),
}

# A land may hold these roles (decision 2026-11-21: lands can be ramp).
# Other role hits on lands are recorded as `land_roles_excluded` so a fetchland
# reading as a tutor is visible rather than quietly dropped or quietly counted.
LAND_ROLES = {"ramp"}


class RoleClassifier:
    def __init__(self, tags: Tags, truth: CardTruth):
        self.tags = tags
        self.truth = truth
        self.anchors: dict[str, str] = {}
        missing = []
        for role, (label, _) in ROLE_ANCHORS.items():
            slug = tags.slug_for(label)
            if slug is None:
                missing.append((role, label))
            else:
                self.anchors[role] = slug
        self.missing_anchors = missing

    @property
    def version(self) -> str:
        return f"tags:{self.tags.version}"

    def roles_for(self, card_name: str) -> tuple[list[str], str]:
        """Return (roles, state): CLASSIFIED / LAND / UNTAGGED / UNRESOLVED."""
        roles, state, _ = self._classify_card(card_name)
        return roles, state

    def _classify_card(self, card_name: str) -> tuple[list[str], str, list[str]]:
        """Roles, state, and role hits withheld by the land rule."""
        record = self.truth.resolve(card_name)
        if record is None:
            return [], "UNRESOLVED", []
        card_tags = self.tags.tags_for(record.get("oid"))
        land = is_land(record)
        if not card_tags:
            return [], ("LAND" if land else "UNTAGGED"), []

        hit = [role for role, anchor in self.anchors.items()
               if any(anchor in self.tags.ancestors(slug) for slug in card_tags)]
        if not land:
            return hit, ("CLASSIFIED" if hit else "UNTAGGED"), []

        allowed = [r for r in hit if r in LAND_ROLES]
        withheld = [r for r in hit if r not in LAND_ROLES]
        return allowed, ("CLASSIFIED" if allowed else "LAND"), withheld

    def classify(self, deck: Deck) -> dict:
        per_card = []
        for entry in deck.entries:
            if entry.zone == "sideboard":
                continue
            record = self.truth.resolve(entry.name)
            roles, state, withheld = self._classify_card(entry.name)
            per_card.append({
                "name": entry.name,
                "qty": entry.qty,
                "zone": entry.zone,
                "land": is_land(record),
                "roles": roles,
                "state": state,
                "land_roles_excluded": withheld,
            })

        counts = {role: 0 for role in ROLE_ANCHORS}
        for card in per_card:
            for role in card["roles"]:
                counts[role] += card["qty"]

        # D7: a card may hold several roles. Counts are per role and do not sum
        # to the deck; the multi-role cards are listed so the overlap is visible.
        multi = [
            {"name": c["name"], "qty": c["qty"], "roles": c["roles"]}
            for c in per_card if len(c["roles"]) > 1
        ]
        distinct_in_any_role = sum(1 for c in per_card if c["roles"])

        untagged = [f"{c['name']} x{c['qty']}" for c in per_card if c["state"] == "UNTAGGED"]
        unresolved = [c["name"] for c in per_card if c["state"] == "UNRESOLVED"]
        nonland = [c for c in per_card if not c["land"]]
        land_cards = [c for c in per_card if c["land"]]

        # lands may only hold LAND_ROLES; show the split so ramp reads honestly
        land_ramp = sum(c["qty"] for c in land_cards if "ramp" in c["roles"])
        spell_ramp = sum(c["qty"] for c in nonland if "ramp" in c["roles"])
        excluded = [
            {"name": c["name"], "qty": c["qty"], "roles": c["land_roles_excluded"]}
            for c in land_cards if c["land_roles_excluded"]
        ]
        classified = sum(1 for c in nonland if c["state"] == "CLASSIFIED")

        return {
            "version": {"roles": self.version, "anchors": self.anchors},
            "counts": counts,
            "ramp_split": {"land": land_ramp, "spells": spell_ramp},
            "coverage": {
                "cards": len(per_card),
                "nonland": len(nonland),
                "lands": len(land_cards),
                "classified": classified,
                "untagged": len(untagged),
                "unresolved": len(unresolved),
                # denominator is nonland cards: a land has no role to cover
                "classified_pct": round(100 * classified / max(len(nonland), 1), 1),
            },
            "untagged": untagged,
            "unresolved": unresolved,
            "land_roles_excluded": excluded,
            "multi_role": multi,
            "distinct_in_any_role": distinct_in_any_role,
            "role_slots": sum(counts.values()),
            "per_card": per_card,
            "status": "AVAILABLE" if not unresolved and not untagged and not self.missing_anchors else "PARTIAL",
        }
