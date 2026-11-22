"""Freeze a deck: canonical form, fingerprint, immutable snapshot.

Contract (NEBULA-CONTRACT-P0.md §2): a result without a fingerprint is not a
nebula result. The fingerprint is computed over a canonical rendering, so the
same deck always produces the same hash regardless of line order or printing.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .importer import Deck

SCHEMA = 1


def canonical(deck: Deck) -> str:
    """Deterministic rendering: one sorted line per entry, zone included."""
    lines = sorted(
        f"{e.zone}\t{e.qty}\t{e.name}" for e in deck.entries
    )
    return "\n".join(lines) + "\n"


def normalised_text(deck: Deck) -> str:
    """The source text as the parser saw it: CRLF collapsed, nothing else changed.

    A byte hash of the file is not stable - git rewrites line endings on
    checkout, so the same deck hashes differently on a different box. Hash what
    the pipeline actually consumed instead, and hash the canonical form
    separately for identity.
    """
    return deck.raw.replace("\r\n", "\n").replace("\r", "\n")


def fingerprint(deck: Deck) -> dict:
    canon = canonical(deck)
    return {
        "deck_sha256": hashlib.sha256(canon.encode("utf-8")).hexdigest(),
        "text_sha256": hashlib.sha256(normalised_text(deck).encode("utf-8")).hexdigest(),
        "total": deck.total,
        "counts": deck.counts(),
        "cards": len(deck.entries),
        "flags": list(deck.flags),
    }


def write_snapshot(deck: Deck, outdir: str | Path, extra: dict | None = None) -> dict:
    """Write the frozen snapshot and return its metadata.

    Idempotent: an existing snapshot with the same deck hash is left untouched.
    """
    meta = fingerprint(deck)
    meta.update({
        "schema": SCHEMA,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": deck.source,
        "canonical": canonical(deck),
        "entries": [{"name": e.name, "qty": e.qty, "zone": e.zone} for e in deck.entries],
    })
    if extra:
        meta.update(extra)

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{meta['deck_sha256'][:16]}.json"
    if not target.exists():
        target.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    meta["path"] = str(target)
    meta["written"] = not target.exists()
    return meta
