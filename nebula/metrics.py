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
    text = str(type_line or "").split(" // ")[0].split("\u2014")[0]
    for kind in TYPE_ORDER:
        if kind in text:
            return kind
    return (text.strip().split(" ")[0] or "Unknown") if text.strip() else "Unknown"


def _is_land(record: dict | None) -> bool:
    if not record:
        return False
    return "land" in str(record.get("tl") or "").lower()


def composition(deck: Deck, truth: CardTruth) -> dict:
    rows = [e for e in deck.entries if e.zone != "sideboard"]
    lands = nonlands = basics = unresolved = 0
    values: list[float] = []
    curve = Counter()
    types = Counter()

    for entry in rows:
        record = truth.resolve(entry.name)
        if record is None:
            unresolved += entry.qty
            continue
        if _is_land(record):
            lands += entry.qty
            if entry.name.lower() in BASIC_LANDS:
                basics += entry.qty
            continue
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
