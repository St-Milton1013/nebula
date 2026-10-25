#!/usr/bin/env python3
"""
NEBULA — Unified Deck Analyzer
================================

One program that takes a link and spits out all the info.

Usage:
    python nebula.py --link <deck_url_or_card_url>
    python nebula.py --decklist <file.txt>
    python nebula.py --card <card_name>

What it does:
    1. Fetches card info (Scryfall)
    2. Validates deck format (deck_validator)
    3. Gets card tags (tagger)
    4. Gets commander spellbook combos
    5. Gets hypercalculator probabilities (tag-based)
    6. Gets meta context (CEDHStats)
    7. Gets LearnCEDH deck summary
    8. Outputs everything in one report

All adapters are wired through this single entry point.
Comprehensive Documentation: NEBULA-TRANSFER.md
"""

import argparse
import json
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import adapters
from archetype.scryfall import card_info as scryfall_card_info, \
    tags as scryfall_tags
from archetype.deck_validator import num_adapter as deck_validator_adapter
from archetype.learncedh import num_adapter as learncedh_adapter
from archetype.commander_spellbook import num_adapter as commander_spellbook_adapter
from archetype.hypercalculator import num_adapter as hypercalculator_adapter
from archetype.meta_compare import num_adapter as meta_compare_adapter


def load_deck_from_file(filepath):
    """Load a decklist from a text file.
    Supports:
    - 'count card name' format (e.g., '4 Sol Ring' = 4 copies)
    - 'card name' format (e.g., 'Sol Ring' = 1 copy)
    - One card per line
    """
    with open(filepath) as f:
        content = f.read()
    cards = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Try to detect 'count card name' format
        # Split on whitespace, but we need to check if the first token is a number
        parts = line.split(None, 1)
        if len(parts) == 2:
            count_str, name = parts
            if count_str.isdigit():
                # It's a count card name format
                cards.extend([name.strip()] * int(count_str))
            else:
                # Just a card name with spaces - treat as single card
                cards.append(line)
        else:
            cards.append(line)
    return cards


def load_deck_from_link(url):
    """
    Parse a deck link and extract card names.

    Supports:
    - Moxfield deck URLs: https://www.moxfield.com/decks/<id>
    - Archidekt deck URLs: https://archidekt.com/decks/<id>
    - Plain text files: file:// paths or URLs to text files
    """
    # Handle file:// URLs
    if url.startswith('file://'):
        path = url[len('file://'):]
        if os.path.isabs(path):
            filepath = path
        else:
            filepath = os.path.join(PROJECT_ROOT, path)
        return load_deck_from_file(filepath)

    # Handle Moxfield deck URLs
    if '/decks/' in url:
        # Expected: https://www.moxfield.com/decks/<id>
        # For now, return PARTIAL (needs Moxfield API key)
        return None  # Placeholder — implement with Moxfield API

    # Handle Archidekt deck URLs
    if '/decks/' in url:
        # Expected: https://archidekt.com/decks/<id>
        # For now, return PARTIAL (needs Archidekt API)
        return None  # Placeholder — implement with Archidekt API

    # Assume it's a plain text file or a decklink.com URL
    if os.path.exists(url):
        return load_deck_from_file(url)
    elif url.startswith('http'):
        # Remote URL — return PARTIAL (needs network fetch)
        return None
    else:
        # Assume it's a URL to a deck
        return None


def build_report(link=None, decklist=None):
    """Build the unified report from all adapters."""

    report = {
        "report_title": "NEBULA Unified Deck Analysis",
        "generated": "2026-10-24T00:00:00Z",
        "source": "unknown",
        "adapters": {
            "scryfall": {"status": "catalog", "deck": {}},
            "deck_validator": {"status": "catalog", "deck": {}},
            "tagger": {"status": "catalog", "deck": {}},
            "commander_spellbook": {"status": "catalog", "deck": {}},
            "hypercalculator": {"status": "catalog", "deck": {}},
            "meta_compare": {"status": "catalog", "deck": {}},
            "learncedh": {"status": "catalog", "deck": {}},
        },
        "report": {}
    }

    # Parse input
    if link:
        report["source"] = f"link: {link}"
        deck_cards = load_deck_from_link(link)
        if deck_cards is None:
            report["status"] = "PARTIAL"
            report["caveats"] = [
                "Could not fetch decklist from link; provide decklist or ensure link is supported"
            ]
        else:
            report["decklist"] = deck_cards
            report["source"] = f"link: {link}"
    elif decklist:
        report["source"] = f"file: {decklist}"
        deck_cards = load_deck_from_file(decklist)
        report["decklist"] = deck_cards
    else:
        report["status"] = "UNSUPPORTED"
        report["caveats"] = ["No input provided — use --link or --decklist"]
        return report

    # Check minimum card count
    if len(report["decklist"]) < 3:
        report["status"] = "PARTIAL"
        report["caveats"] = ["Decklist too short (minimum 3 cards)"]
        return report

    # 1. Card info (Scryfall)
    report["adapters"]["scryfall"] = {
        "status": "available",
        "deck": scryfall_card_info(report["decklist"]) if report["decklist"] else {},
        "caveats": []
    }

    # 2. Deck validation
    report["adapters"]["deck_validator"] = {
        "status": "available",
        "deck": deck_validator_adapter(report["decklist"]) if report["decklist"] else {},
        "caveats": []
    }

    # 3. Card tags (Tagger)
    report["adapters"]["tagger"] = {
        "status": "available",
        "deck": scryfall_tags(report["decklist"]) if report["decklist"] else {},
        "caveats": []
    }

    # 4. Commander Spellbook combos
    report["adapters"]["commander_spellbook"] = {
        "status": "available",
        "deck": commander_spellbook_adapter(report["decklist"]) if report["decklist"] else {},
        "caveats": []
    }

    # 5. Hypercalculator probabilities (tag-based)
    report["adapters"]["hypercalculator"] = {
        "status": "available",
        "deck": hypercalculator_adapter(report["decklist"]) if report["decklist"] else {},
        "caveats": []
    }

    # 6. Meta context (CEDHStats)
    report["adapters"]["meta_compare"] = {
        "status": "available",
        "deck": meta_compare_adapter(report["decklist"]) if report["decklist"] else {},
        "caveats": []
    }

    # 7. LearnCEDH deck summary
    report["adapters"]["learncedh"] = {
        "status": "available",
        "deck": learncedh_adapter(report["decklist"]) if report["decklist"] else {},
        "caveats": []
    }

    # Check for any PARTIAL statuses
    statuses = [a["status"] for a in report["adapters"].values()]
    if "PARTIAL" in statuses:
        report["status"] = "PARTIAL"
    elif "UNSUPPORTED" in statuses:
        report["status"] = "UNSUPPORTED"
    else:
        report["status"] = "AVAILABLE"

    # Build the report body (simplified view)
    report["report"] = {
        "status": report["status"],
        "source": report["source"],
        "deck_summary": {
            "card_count": len(report["decklist"]),
            "has_commander": any("commander" in c.lower() for c in report["decklist"]),
            "total_cards": len(report["decklist"]),
        },
        "adapters_summary": {
            name: {
                "status": a["status"],
                "key_data": {k: v for k, v in a["deck"].items() if k != "adapter"}
            }
            for name, a in report["adapters"].items()
        }
    }

    return report


def print_report(report, output_format="text"):
    """Print the report in the specified format."""
    if output_format == "json":
        print(json.dumps(report, indent=2, default=str))
    else:
        # Text output
        print("=" * 60)
        print(f"  NEBULA Unified Deck Analysis")
        print(f"  Source: {report['source']}")
        print(f"  Status: {report['status']}")
        print("=" * 60)

        if "decklist" in report:
            print(f"\n  Decklist: {len(report['decklist'])} cards")

        print("\n  ADAPTERS:")
        for name, adap in report["adapters"].items():
            status = adap.get("status", "unknown")
            print(f"    [{status.upper()}] {name}")

        print("\n  SUMMARY:")
        if "report" in report and "deck_summary" in report["report"]:
            print(f"    Cards: {report['report']['deck_summary']['card_count']}")
            print(f"    Commander: {report['report']['deck_summary'].get('has_commander', False)}")

        if report.get("caveats"):
            print("\n  CAVEATS:")
            for c in report["caveats"]:
                print(f"    - {c}")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="NEBULA Unified Deck Analyzer — one program, all the info"
    )
    parser.add_argument(
        "--link", "-l",
        help="Deck link (Moxfield, Archidekt, URL) or path to decklist file"
    )
    parser.add_argument(
        "--decklist", "-d",
        help="Path to decklist file (one card per line, or 'count card name')"
    )
    parser.add_argument(
        "--card", "-c",
        help="Single card name to look up card info"
    )
    parser.add_argument(
        "--format", "-f",
        default="text",
        choices=["text", "json"],
        help="Output format (default: text)"
    )
    args = parser.parse_args()

    # Validate input
    if not args.link and not args.decklist and not args.card:
        parser.error("No input provided. Use --link, --decklist, or --card.")

    # Build report
    if args.card:
        # Single card lookup
        report = {
            "report_title": "NEBULA Card Lookup",
            "generated": "2026-10-24T00:00:00Z",
            "source": f"card: {args.card}",
            "adapters": {
                "scryfall": {"status": "available", "deck": {}},
                "deck_validator": {"status": "not_applicable", "deck": {}},
                "tagger": {"status": "available", "deck": {}},
                "commander_spellbook": {"status": "not_applicable", "deck": {}},
                "hypercalculator": {"status": "not_applicable", "deck": {}},
                "meta_compare": {"status": "not_applicable", "deck": {}},
                "learncedh": {"status": "not_applicable", "deck": {}},
            },
            "report": {}
        }
        card_result = scryfall_card_info([args.card], lookup_mode="single")
        report["adapters"]["scryfall"]["deck"] = card_result
        card_tags = scryfall_tags([args.card])
        report["adapters"]["tagger"]["deck"] = card_tags

        print_report(report, args.format)
    else:
        # Deck analysis
        report = build_report(link=args.link, decklist=args.decklist)
        print_report(report, args.format)

        # Save report to file
        if args.format == "json":
            output_file = report["source"].split("://")[-1].replace("/", "_")[:50]
            output_file = output_file or "unk"
            output_file = f"report_{output_file}.json"
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n  Report saved to: {output_file}")


if __name__ == "__main__":
    main()
