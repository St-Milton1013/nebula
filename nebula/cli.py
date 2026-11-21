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
from .decklink import load_link
from .freeze import write_snapshot
from .importer import Deck, load_deck
from .metrics import composition
from .roles import RoleClassifier
from .tagger import Tags

DEFAULT_TRUTH = Path("data/card_truth.json.gz")
DEFAULT_TAGS = Path("data/oracle_tags.json.gz")
DEFAULT_SNAPSHOTS = Path("data/snapshots")


def _load(deck_path: Path | None, link: str | None) -> Deck:
    if link:
        return load_link(link)
    return load_deck(deck_path)


def run(deck: Deck, truth_path: Path, snapshot_dir: Path | None, as_json: bool,
        tags_path: Path | None = None) -> int:
    if not truth_path.exists():
        print(f"card truth missing: {truth_path}\n"
              f"build it with: python scripts/build_card_truth.py", file=sys.stderr)
        return 2
    truth = CardTruth.load(truth_path)

    meta = write_snapshot(deck, snapshot_dir or DEFAULT_SNAPSHOTS,
                          extra={"card_truth": truth.version})
    result = legality.check(deck, truth)

    comp = composition(deck, truth)

    roles = None
    if tags_path is not None:
        if not tags_path.exists():
            print(f"tag store missing: {tags_path}\n"
                  f"build it with: python scripts/build_tags.py", file=sys.stderr)
            return 2
        classifier = RoleClassifier(Tags.load(tags_path), truth)
        roles = classifier.classify(deck)

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
        "composition": comp,
    }
    if roles is not None:
        payload["roles"] = {k: v for k, v in roles.items() if k != "per_card"}
        payload["roles"]["per_card"] = roles["per_card"]

    if as_json:
        print(json.dumps(payload, indent=2))
        return 0

    d = payload["deck"]
    print(f"deck      {deck.source}")
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
    print()
    print(f"deck shape  {comp['total']} cards  |  {comp['lands']} lands "
          f"({comp['basic_lands']} basic, {comp['nonbasic_lands']} nonbasic)  |  "
          f"{comp['nonlands']} nonland")
    if comp["average_mana_value"] is not None:
        print(f"  mana value  avg {comp['average_mana_value']}  median {comp['median_mana_value']}  "
              f"total {comp['mana_value_total']}")
    curve_bits = "  ".join(f"{k}:{v}" for k, v in comp["curve"].items())
    print(f"  curve       {curve_bits}")
    type_bits = "  ".join(f"{k} {v}" for k, v in list(comp["types"].items())[:6])
    print(f"  types       {type_bits}")

    if roles is not None:
        cov = roles["coverage"]
        print()
        print(f"roles     {roles['status']}  ({cov['classified']}/{cov['nonland']} nonland cards classified, "
              f"{cov['untagged']} untagged, {cov['lands']} lands)")
        split = roles["ramp_split"]
        for role, count in roles["counts"].items():
            note = ""
            if role == "ramp" and count:
                note = f"  ({split['spells']} spells + {split['land']} land)"
            print(f"  {role:<11} {count:>3}  {'#' * min(count, 40)}{note}")
        print(f"  overlap     {len(roles['multi_role'])} card(s) in 2+ roles, "
              f"{roles['distinct_in_any_role']} distinct cards, {roles['role_slots']} role slots")
        for card in roles["multi_role"][:6]:
            print(f"    {card['name'][:34]:<34} {'+'.join(card['roles'])}")
        if roles["land_roles_excluded"]:
            shown = ", ".join(f"{c['name']} ({'+'.join(c['roles'])})"
                              for c in roles["land_roles_excluded"][:5])
            print(f"  lands not counted as: {shown}",
                  "..." if len(roles["land_roles_excluded"]) > 5 else "")
        if roles["untagged"]:
            print("  untagged:", ", ".join(roles["untagged"][:8]),
                  "..." if len(roles["untagged"]) > 8 else "")

    if d["flags"]:
        print()
        print("import flags:", ", ".join(d["flags"]))
    return 0 if result["status"] == "AVAILABLE" else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="P0: import, freeze, validate one deck")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--deck", type=Path, help="path to a text decklist")
    group.add_argument("--link", help="Moxfield or Archidekt deck URL")
    ap.add_argument("--truth", type=Path, default=DEFAULT_TRUTH)
    ap.add_argument("--tags", type=Path, default=None,
                    help="add role coverage from the Tagger store (default when --roles)")
    ap.add_argument("--roles", action="store_true", help="report role coverage")
    ap.add_argument("--snapshots", type=Path, default=DEFAULT_SNAPSHOTS)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    tags_path = args.tags if args.tags is not None else (DEFAULT_TAGS if args.roles else None)
    deck = _load(args.deck, args.link)
    return run(deck, args.truth, args.snapshots, args.json, tags_path)


if __name__ == "__main__":
    sys.exit(main())
