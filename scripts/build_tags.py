"""Build nebula's frozen tag store from the Scryfall Tagger bulk file.

    python scripts/build_tags.py --out data/oracle_tags.json.gz

The Tagger hierarchy is the role taxonomy (decision 2026-11-21). Keep the
parent links: a card tagged ``tutor-creature-giant`` is also a ``tutor``, and
that ancestry is what makes the taxonomy useful rather than a flat word list.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BULK_LIST = "https://api.scryfall.com/bulk-data"
UA = "nebula-deck-audit/0.1 (+local, single-deck review)"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=120) as rsp:
        return rsp.read()


def _bulk_uri() -> tuple[str, str]:
    listing = json.loads(_get(BULK_LIST))
    for entry in listing["data"]:
        if entry["type"] == "oracle_tags":
            return entry["jsonl_download_uri"], entry["updated_at"]
    raise SystemExit("oracle_tags bulk entry not found")


def build(out: Path) -> dict:
    uri, updated = _bulk_uri()
    print(f"source: {uri}\nsource updated_at: {updated}")
    raw = _get(uri)
    print(f"downloaded {len(raw)/1e6:.1f} MB")

    tags: dict[str, dict] = {}
    by_oracle: dict[str, list[str]] = {}
    weight_counts: dict[str, int] = {}

    for line in gzip.decompress(raw).decode("utf-8").splitlines():
        if not line.strip():
            continue
        tag = json.loads(line)
        slug = tag["slug"]
        tags[slug] = {
            "label": tag.get("label"),
            "desc": (tag.get("description") or "")[:200],
            "parents": tag.get("parent_ids") or [],
            "children": tag.get("child_ids") or [],
            "id": tag.get("id"),
        }
        for tagging in tag.get("taggings") or []:
            oid = tagging.get("oracle_id")
            if not oid:
                continue
            by_oracle.setdefault(oid, []).append(slug)
            w = tagging.get("weight", "median")
            weight_counts[w] = weight_counts.get(w, 0) + 1

    payload = {
        "schema": 1,
        "meta": {
            "source": "scryfall bulk oracle_tags (Tagger)",
            "source_updated_at": updated,
            "source_uri": uri,
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tags": len(tags),
            "cards": len(by_oracle),
            "weights": weight_counts,
        },
        "tags": tags,
        "by_oracle": by_oracle,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    blob = buf.getvalue()
    out.write_bytes(blob)

    manifest = dict(payload["meta"])
    manifest.update({"path": str(out), "bytes": len(blob),
                     "sha256": hashlib.sha256(blob).hexdigest(), "schema": 1})
    out.with_suffix("").with_suffix(".manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"tags: {len(tags)}  cards tagged: {len(by_oracle)}  file: {len(blob)/1e6:.1f} MB")
    print(f"sha256: {manifest['sha256'][:16]}")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/oracle_tags.json.gz")
    args = ap.parse_args(argv)
    build(Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
