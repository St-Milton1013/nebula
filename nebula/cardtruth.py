"""Card truth: frozen Scryfall record lookup.

Built by ``scripts/build_card_truth.py`` from the Scryfall bulk oracle-cards
file. Full Oracle text, both faces and per-format legality are kept, because
legality, colour identity and role classification all depend on them.

Name resolution order: exact -> case-insensitive -> apostrophe-normalised ->
front face of a two-faced card. A miss is a miss; nothing is guessed.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

_APOSTROPHES = {"\u2019": "'", "\u2018": "'", "\u02bc": "'"}


def _norm(name: str) -> str:
    out = name.strip().lower()
    for src, dst in _APOSTROPHES.items():
        out = out.replace(src, dst)
    return out


class CardTruth:
    """Read-only card index. Never mutates, never fetches at call time."""

    def __init__(self, index: dict, meta: dict | None = None):
        self._index = index
        self.meta = meta or {}
        self._aliases = {}
        for key, rec in index.items():
            full = rec.get("n", key)
            if " // " in full:
                front = full.split(" // ")[0]
                self._aliases.setdefault(_norm(front), key)

    # ---------------------------------------------------------------- loading
    @classmethod
    def load(cls, path: str | Path) -> "CardTruth":
        p = Path(path)
        opener = gzip.open if p.suffix == ".gz" else open
        with opener(p, "rt", encoding="utf-8") as fh:
            payload = json.load(fh)
        meta = dict(payload.get("meta", {}))
        if "sha256" not in meta:
            import hashlib
            meta["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        meta.setdefault("path", str(p))
        return cls(payload.get("cards", payload), meta)

    @classmethod
    def from_records(cls, records: list[dict]) -> "CardTruth":
        index = {}
        for rec in records:
            index[_norm(rec["name"])] = {
                "n": rec["name"],
                "mc": rec.get("mana_cost", ""),
                "cmc": rec.get("cmc", 0.0),
                "ci": rec.get("color_identity", []),
                "tl": rec.get("type_line", ""),
                "ot": rec.get("oracle_text", ""),
                "p": rec.get("power"),
                "t": rec.get("toughness"),
                "kw": rec.get("keywords", []),
                "legal": rec.get("legalities", {}),
                "edhrec": rec.get("edhrec_rank"),
                "faces": rec.get("card_faces", []),
                "oid": rec.get("oracle_id"),
            }
        return cls(index, {"count": len(index)})

    # ---------------------------------------------------------------- lookup
    def __len__(self) -> int:
        return len(self._index)

    @property
    def version(self) -> str:
        return self.meta.get("sha256", "unversioned")[:12]

    def resolve(self, name: str) -> dict | None:
        key = _norm(name)
        rec = self._index.get(key)
        if rec is not None:
            return rec
        alias = self._aliases.get(key)
        if alias is not None:
            return self._index[alias]
        return None

    def color_identity(self, name: str) -> list[str] | None:
        rec = self.resolve(name)
        return None if rec is None else list(rec.get("ci", []))

    def legality(self, name: str, fmt: str = "commander") -> str | None:
        rec = self.resolve(name)
        if rec is None:
            return None
        return (rec.get("legal") or {}).get(fmt)
