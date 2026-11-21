"""Deterministic measurements: composition and curve.

Everything here is arithmetic over the frozen deck plus card truth. No model,
no tags, no judgement - the numbers a reader can recompute by hand from the
decklist. Role coverage lives in roles.py because it depends on a taxonomy;
these do not.
"""

from __future__ import annotations

import statistics
from collections import Counter

from .cardtruth import CardTruth
from .importer import BASIC_LANDS, Deck

CURVE_BUCKETS = ["0", "1", "2", "3", "4", "5", "6+"]
TYPE_ORDER = ("Creature", "Planeswalker", "Instant", "Sorcery", "Artifact",
              "Enchantment", "Battle", "Land")


def primary_type(type_line: str | None) -> str:
    """One word per card: Creature, Instant, Artifact, ... First match wins."""
    text = front_type_line(type_line).split("\u2014")[0]
    for kind in TYPE_ORDER:
        if kind in text:
            return kind
    return (text.strip().split(" ")[0] or "Unknown") if text.strip() else "Unknown"


def front_type_line(type_line: str | None) -> str:
    """The front face only: a modal DFC 'Instant // Land' is an Instant."""
    return str(type_line or "").split(" // ")[0]


def is_land(record: dict | None) -> bool:
    """Front face is a land: this card is played as a land drop."""
    if not record:
        return False
    return "land" in front_type_line(record.get("tl")).lower()


def has_land_face(record: dict | None) -> bool:
    """Any face is a land, including the back of a modal DFC."""
    if not record:
        return False
    return any("land" in part.lower()
               for part in str(record.get("tl") or "").split(" // "))


def composition(deck: Deck, truth: CardTruth) -> dict:
    rows = [e for e in deck.entries if e.zone != "sideboard"]
    lands = nonlands = basics = unresolved = 0
    modal_lands: list[dict] = []
    values: list[float] = []
    curve = Counter()
    types = Counter()

    for entry in rows:
        record = truth.resolve(entry.name)
        if record is None:
            unresolved += entry.qty
            continue
        if is_land(record):
            lands += entry.qty
            if entry.name.lower() in BASIC_LANDS:
                basics += entry.qty
            continue
        if has_land_face(record):
            # A modal DFC played as a spell is still a land when you need a land
            # drop. Counted in both places, and named so the double count is
            # visible rather than silent (decision 2026-11-21).
            modal_lands.append({"name": entry.name, "qty": entry.qty})
        nonlands += entry.qty
        cmc = float(record.get("cmc") or 0.0)
        values.extend([cmc] * entry.qty)
        bucket = "6+" if cmc >= 6 else str(int(cmc))
        curve[bucket] += entry.qty
        types[primary_type(record.get("tl"))] += entry.qty

    return {
        "total": deck.total,
        "lands": lands,
        "nonlands": nonlands,
        "basic_lands": basics,
        "nonbasic_lands": lands - basics,
        "modal_lands": modal_lands,
        "modal_land_count": sum(m["qty"] for m in modal_lands),
        "land_sources": lands + sum(m["qty"] for m in modal_lands),
        "unresolved": unresolved,
        "average_mana_value": round(statistics.fmean(values), 2) if values else None,
        "median_mana_value": statistics.median(values) if values else None,
        "mana_value_total": int(sum(values)),
        "curve": {bucket: curve.get(bucket, 0) for bucket in CURVE_BUCKETS},
        "curve_pct": {
            bucket: round(100 * curve.get(bucket, 0) / nonlands, 1) if nonlands else 0.0
            for bucket in CURVE_BUCKETS
        },
        "types": dict(sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def build(deck: Deck, truth: CardTruth, roles: dict | None = None) -> dict:
    out = {"composition": composition(deck, truth)}
    if roles is not None:
        out["roles"] = {k: v for k, v in roles.items() if k != "per_card"}
    return out
