"""Scryfall Tagger tag store: slug ancestry and per-card tags.

The Tagger hierarchy is community-built and community-checked, which is why it
is the role taxonomy's source (decision 2026-11-21). A card tagged
``tutor-creature-giant`` inherits ``tutor``; that inheritance is computed once
at load time, not per card.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path


class Tags:
    def __init__(self, tags: dict, by_oracle: dict, meta: dict | None = None):
        self.tags = tags
        self.by_oracle = by_oracle
        self.meta = meta or {}
        self._by_id = {t.get("id"): slug for slug, t in tags.items() if t.get("id")}
        self._by_label = {str(t.get("label") or "").lower(): slug for slug, t in tags.items()}
        self._closure: dict[str, frozenset[str]] = {}

    # ---------------------------------------------------------------- loading
    @classmethod
    def load(cls, path: str | Path) -> "Tags":
        p = Path(path)
        opener = gzip.open if p.suffix == ".gz" else open
        with opener(p, "rt", encoding="utf-8") as fh:
            payload = json.load(fh)
        meta = dict(payload.get("meta", {}))
        if "sha256" not in meta:
            meta["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        return cls(payload.get("tags", {}), payload.get("by_oracle", {}), meta)

    # ---------------------------------------------------------------- lookups
    @property
    def version(self) -> str:
        return str(self.meta.get("sha256", "unversioned"))[:12]

    def __len__(self) -> int:
        return len(self.tags)

    def slug_for(self, label: str) -> str | None:
        """Resolve a human tag label ('card advantage') to its slug."""
        return self._by_label.get(label.strip().lower())

    def ancestors(self, slug: str) -> frozenset[str]:
        """The slug plus every parent tag, transitively."""
        cached = self._closure.get(slug)
        if cached is not None:
            return cached
        seen: set[str] = set()
        stack = [slug]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            node = self.tags.get(current)
            if not node:
                continue
            for parent_id in node.get("parents") or []:
                parent = self._by_id.get(parent_id)
                if parent:
                    stack.append(parent)
        result = frozenset(seen)
        self._closure[slug] = result
        return result

    def tags_for(self, oracle_id: str | None) -> list[str]:
        if not oracle_id:
            return []
        return self.by_oracle.get(oracle_id, [])

    def has(self, oracle_id: str | None, anchor_slug: str) -> bool:
        for slug in self.tags_for(oracle_id):
            if anchor_slug in self.ancestors(slug):
                return True
        return False
