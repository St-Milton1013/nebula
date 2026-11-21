"""Build nebula's frozen card-truth store from Scryfall bulk data.

    python scripts/build_card_truth.py --out data/card_truth.json.gz

Writes the index plus a manifest (sha256, source timestamp, counts) so every
downstream result can name the exact card-truth version it used.

Kept deliberately dumb: stream the JSONL, project the fields the pipeline needs,
write once. No incremental logic, no cache invalidation bugs.
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
KEEP_LEGAL = ("commander", "duel", "legacy", "vintage")
UA = "nebula-deck-audit/0.1 (+local, single-deck review)"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json;q=0.9,*/*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=120) as rsp:
        return rsp.read()


def _bulk_uri() -> tuple[str, str]:
    listing = json.loads(_get(BULK_LIST))
    for entry in listing["data"]:
        if entry["type"] == "oracle_cards":
            return entry["jsonl_download_uri"], entry["updated_at"]
    raise SystemExit("oracle_cards bulk entry not found")


def _project(card: dict) -> dict:
    return {
        "n": card["name"],
        "mc": card.get("mana_cost", ""),
        "cmc": card.get("cmc", 0.0),
        "ci": card.get("color_identity", []),
        "tl": card.get("type_line", ""),
        "ot": card.get("oracle_text", ""),
        "p": card.get("power"),
        "t": card.get("toughness"),
        "kw": card.get("keywords", []),
        "legal": {k: v for k, v in (card.get("legalities") or {}).items() if k in KEEP_LEGAL},
        "edhrec": card.get("edhrec_rank"),
        "faces": [
            {
                "name": f.get("name", ""),
                "mc": f.get("mana_cost", ""),
                "tl": f.get("type_line", ""),
                "ot": f.get("oracle_text", ""),
                "p": f.get("power"),
                "t": f.get("toughness"),
            }
            for f in card.get("card_faces") or []
        ],
        "oid": card.get("oracle_id"),
    }


def build(out: Path) -> dict:
    uri, updated = _bulk_uri()
    print(f"source: {uri}\nsource updated_at: {updated}")
    raw = _get(uri)
    print(f"downloaded {len(raw)/1e6:.1f} MB")

    text = gzip.decompress(raw).decode("utf-8")
    index: dict[str, dict] = {}
    skipped = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        card = json.loads(line)
        if card.get("lang") != "en":
            skipped += 1
            continue
        rec = _project(card)
        index[rec["n"].lower()] = rec

    payload = {
        "schema": 1,
        "source": "scryfall bulk oracle_cards",
        "meta": {
            "source_updated_at": updated,
            "source_uri": uri,
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "count": len(index),
            "skipped_non_english": skipped,
        },
        "cards": index,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(json.dumps(payload, ensure_ascii=False, sort_keys=False).encode("utf-8"))
    blob = buf.getvalue()
    out.write_bytes(blob)

    manifest = dict(payload["meta"])
    manifest.update({
        "path": str(out),
        "bytes": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "schema": 1,
    })
    manifest_path = out.with_suffix("").with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"cards: {len(index)}  file: {len(blob)/1e6:.1f} MB  sha256: {manifest['sha256'][:16]}")
    print(f"manifest: {manifest_path}")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/card_truth.json.gz")
    args = ap.parse_args(argv)
    build(Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
