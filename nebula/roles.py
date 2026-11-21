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

# Roles that overlap functionally. Reported so a card is never counted twice
# without saying so.
OVERLAPS = [("counter", "removal"), ("wipe", "removal"), ("stax", "protection")]


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
        record = self.truth.resolve(card_name)
        if record is None:
            return [], "UNRESOLVED"
        if "land" in str(record.get("tl") or "").lower():
            return [], "LAND"
        oracle_id = record.get("oid")
        card_tags = self.tags.tags_for(oracle_id)
        if not card_tags:
            return [], "UNTAGGED"
        hit = []
        for role, anchor in self.anchors.items():
            if any(anchor in self.tags.ancestors(slug) for slug in card_tags):
                hit.append(role)
        return hit, "CLASSIFIED" if hit else "UNTAGGED"

    def classify(self, deck: Deck) -> dict:
        per_card = []
        for entry in deck.entries:
            if entry.zone == "sideboard":
                continue
            roles, state = self.roles_for(entry.name)
            per_card.append({
                "name": entry.name,
                "qty": entry.qty,
                "zone": entry.zone,
                "roles": roles,
                "state": state,
            })

        counts = {role: 0 for role in ROLE_ANCHORS}
        for card in per_card:
            for role in card["roles"]:
                counts[role] += card["qty"]

        untagged = [f"{c['name']} x{c['qty']}" for c in per_card if c["state"] == "UNTAGGED"]
        unresolved = [c["name"] for c in per_card if c["state"] == "UNRESOLVED"]
        lands = [c["name"] for c in per_card if c["state"] == "LAND"]
        nonland = [c for c in per_card if c["state"] != "LAND"]
        classified = sum(1 for c in nonland if c["state"] == "CLASSIFIED")

        return {
            "version": {"roles": self.version, "anchors": self.anchors},
            "counts": counts,
            "coverage": {
                "cards": len(per_card),
                "nonland": len(nonland),
                "lands": len(lands),
                "classified": classified,
                "untagged": len(untagged),
                "unresolved": len(unresolved),
                # denominator is nonland cards: a land has no role to cover
                "classified_pct": round(100 * classified / max(len(nonland), 1), 1),
            },
            "untagged": untagged,
            "unresolved": unresolved,
            "per_card": per_card,
            "status": "AVAILABLE" if not unresolved and not untagged and not self.missing_anchors else "PARTIAL",
        }
