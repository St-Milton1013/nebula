"""P0 command line: import a deck, freeze it, check legality.

    python -m nebula.cli --deck tests/fixtures/ishai_rograkh.deck
    python -m nebula.cli --deck my.deck --json

No network, no writes outside the snapshot directory. Every run prints the
deck fingerprint so a result can always be tied to the exact deck it came from.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import legality
from .cardtruth import CardTruth
from .freeze import write_snapshot
from .importer import load_deck

DEFAULT_TRUTH = Path("data/card_truth.json.gz")
DEFAULT_SNAPSHOTS = Path("data/snapshots")


def run(deck_path: Path, truth_path: Path, snapshot_dir: Path | None, as_json: bool) -> int:
    deck = load_deck(deck_path)

    if not truth_path.exists():
        print(f"card truth missing: {truth_path}\n"
              f"build it with: python scripts/build_card_truth.py", file=sys.stderr)
        return 2
    truth = CardTruth.load(truth_path)

    meta = write_snapshot(deck, snapshot_dir or DEFAULT_SNAPSHOTS,
                          extra={"card_truth": truth.version})
    result = legality.check(deck, truth)

    payload = {
        "deck": {
            "source": deck.source,
            "sha256": meta["deck_sha256"],
            "raw_sha256": meta["raw_sha256"],
            "total": meta["total"],
            "counts": meta["counts"],
            "flags": meta["flags"],
            "snapshot": meta["path"],
        },
        "card_truth": {
            "version": truth.version,
            "cards": len(truth),
            "source_updated_at": truth.meta.get("source_updated_at"),
        },
        "legality": result,
    }

    if as_json:
        print(json.dumps(payload, indent=2))
        return 0

    d = payload["deck"]
    print(f"deck      {Path(deck_path).name}")
    print(f"sha256    {d['sha256']}")
    print(f"cards     {d['total']}  ({d['counts']})")
    print(f"truth     {payload['card_truth']['cards']} cards, version {payload['card_truth']['version']}")
    print(f"snapshot  {d['snapshot']}")
    print()
    print(f"legality  {result['status']}")
    for f in result["findings"]:
        mark = {"VERIFIED": "ok  ", "FAIL": "FAIL", "PARTIAL": "part", "UNSUPPORTED": "n/a "}[f["status"]]
        print(f"  [{mark}] {f['code']:<18} {f['detail']}")
        for c in f["cards"][:8]:
            print(f"          - {c}")
        if len(f["cards"]) > 8:
            print(f"          ... +{len(f['cards']) - 8} more")
    if d["flags"]:
        print()
        print("import flags:", ", ".join(d["flags"]))
    return 0 if result["status"] == "AVAILABLE" else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="P0: import, freeze, validate one deck")
    ap.add_argument("--deck", required=True, type=Path)
    ap.add_argument("--truth", type=Path, default=DEFAULT_TRUTH)
    ap.add_argument("--snapshots", type=Path, default=DEFAULT_SNAPSHOTS)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    return run(args.deck, args.truth, args.snapshots, args.json)


if __name__ == "__main__":
    sys.exit(main())
