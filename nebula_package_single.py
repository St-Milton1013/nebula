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
import requests
from bs4 import BeautifulSoup

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import adapters
try:
    from archetype.scryfall import num_adapter as scryfall_num_adapter
except ImportError:
    scryfall_num_adapter = None

try:
    from archetype.deck_validator import num_adapter as deck_validator_adapter
except ImportError:
    deck_validator_adapter = None

try:
    from archetype.learncedh import num_adapter as learncedh_adapter
except ImportError:
    learncedh_adapter = None

try:
    from archetype.commander_spellbook import num_adapter as commander_spellbook_adapter
except ImportError:
    commander_spellbook_adapter = None

try:
    from archetype.hypercalculator import num_adapter as hypercalculator_adapter
except ImportError:
    hypercalculator_adapter = None

try:
    from archetype.meta_compare import num_adapter as meta_compare_adapter
except ImportError:
    meta_compare_adapter = None


def load_deck_from_file(filepath):
    """Load a decklist from a text file.
    Supports both 'count name' and 'name' formats.
    """
    with open(filepath) as f:
        content = f.read()
    # Parse card names (one per line, or "count card name" format)
    cards = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            count, name = parts
            # Expand: add card name 'count' times
            try:
                cards.extend([name.strip()] * int(count))
            except ValueError:
                cards.append(name.strip())
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
        deck = _fetch_moxfield_deck(url)

    # Handle Archidekt deck URLs
    elif '/archidekt.com/decks/' in url:
        deck = _fetch_archidekt_deck(url)

    # Assume it's a plain text file or a decklink.com URL
    if os.path.exists(url):
        return load_deck_from_file(url)
    elif url.startswith('http'):
        # Remote URL — return PARTIAL (needs network fetch)
        return None
    else:
        # Assume it's a URL to a deck
        return None


def _fetch_moxfield_deck(url):
    """Fetch a Moxfield decklist from a deck URL.
    Preferred path (per codie Stage 1 INPUT ROUTER): MCP get_moxfield_deck,
    which bypasses Cloudflare and returns the full decklist. Fall back to
    parsing the public Moxfield HTML page if the MCP tool is unavailable.
    """
    import re

    # Try to extract the deck id
    m = re.search(r'/decks/([A-Za-z0-9]+)', url)
    if not m:
        return None
    deck_id = m.group(1)

    # 1. Try MCP get_moxfield_deck (bypasses Cloudflare)
    try:
        import importlib
        for mod_name in ['mtg_unified.moxfield', 'spellbook.moxfield']:
            try:
                moxfield_mod = importlib.import_module(mod_name)
                if hasattr(moxfield_mod, 'get_moxfield_deck'):
                    deck = moxfield_mod.get_moxfield_deck(deck_id)
                    if deck:
                        return _extract_moxfield_cards(deck)
            except ImportError:
                continue
    except Exception:
        pass

    # 2. Try Moxfield API with token
    api_token = os.environ.get("MOXFIELD_API_TOKEN", "")
    if api_token:
        try:
            resp = requests.get(
                f"https://api.moxfield.com/v1/decks/{deck_id}",
                headers={"Authorization": api_token, "Accept": "application/json"},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return _extract_moxfield_cards(data)
        except Exception:
            pass

    # 3. Fall back to parsing the public HTML page
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            return _extract_moxfield_cards_from_html(soup)
    except Exception:
        pass
    return None
def _extract_moxfield_cards(data):
    """Extract a flat card-name list from a Moxfield API payload."""
    cards = []
    if isinstance(data, dict):
        # Common shapes: {'mainboard': [...]} or {'mainBoard': [...]} or raw array
        for key in ("mainboard", "mainBoard", "cards", "cardsList"):
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    if isinstance(item, str):
                        cards.append(item)
                    elif isinstance(item, dict):
                        # Look for a name field
                        for nk in ("name", "card", "cardName"):
                            if nk in item:
                                cards.append(item[nk])
                                break
                break
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                cards.append(item)
            elif isinstance(item, dict):
                for nk in ("name", "card", "cardName"):
                    if nk in item:
                        cards.append(item[nk])
                        break
    return cards


def _extract_moxfield_cards_from_html(soup):
    """Parse card names from the Moxfield public HTML page."""
    cards = []
    # Moxfield renders the decklist in <pre> or in card divs; try common selectors
    selectors = [
    "pre",
    "code",
    ".decklist, .deck-list",
    "table td",
    "article",
    ".card-name",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(separator=" ", strip=True)
            # Split on common delimiters
            for part in re.split(r'[\n,;]+', text):
                part = part.strip()
                if part and len(part) > 3:
                    cards.append(part)
            if cards:
                break
    # Fall back to all text
    if not cards:
        text = soup.get_text(separator="\n", strip=True)
        for line in text.splitlines():
            line = line.strip()
            if len(line) > 3 and not line.startswith(("Moxfield", "©", "© 1993", "Wizards")):
                cards.append(line)
    # Deduplicate preserving order
    seen = set()
    result = []
    for c in cards:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


def _fetch_archidekt_deck(url):
    """Fetch an Archidekt decklist from a deck URL.

    Archidekt decks can be fetched via the public API (https://api.archidekt.com/v1/decks/{id})
    or parsed from the HTML page. Returns a flat list of card names.
    """
    import re

    m = re.search(r'archidekt\.com/decks/(\d+)', url)
    if not m:
        return None
    deck_id = m.group(1)

    # Archidekt public API (no auth for basic decklist)
    try:
        resp = requests.get(
            f"https://api.archidekt.com/v1/decks/{deck_id}",
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return _extract_archidekt_cards(data)
    except Exception:
        pass

    # Fall back to parsing the public HTML page
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            return _extract_archidekt_cards_from_html(soup)
    except Exception:
        pass
    return None


def _extract_archidekt_cards(data):
    """Extract a flat card-name list from an Archidekt API payload."""
    cards = []
    if isinstance(data, dict):
        for key in ("cards", "mainboard", "commanders", "deck"):
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    if isinstance(item, str):
                        cards.append(item)
                    elif isinstance(item, dict):
                        for nk in ("name", "card", "cardName"):
                            if nk in item:
                                cards.append(item[nk])
                                break
                break
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                cards.append(item)
            elif isinstance(item, dict):
                for nk in ("name", "card", "cardName"):
                    if nk in item:
                        cards.append(item[nk])
                        break
    return cards






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
    if "decklist" not in report or report["decklist"] is None:
        report["status"] = "PARTIAL"
        report["caveats"] = ["Could not fetch decklist from link"]
        return report
    if len(report["decklist"]) < 3:
        report["status"] = "PARTIAL"
        report["caveats"] = ["Decklist too short (minimum 3 cards)"]
        return report

    # 1. Card info (Scryfall)
    scryfall_result = {}
    if scryfall_num_adapter is not None and report["decklist"]:
        scryfall_result = scryfall_num_adapter(
            mode="scryfall",
            decklist=report["decklist"],
            options={"include_oracle_text": True, "include_keywords": True},
        )
    else:
        scryfall_result = {"adapter": "num_adapter", "mode": "scryfall",
                          "status": "UNSUPPORTED", "card_info": [], "cards_missing": 0}
    report["adapters"]["scryfall"] = {
        "status": "available",
        "deck": scryfall_result,
        "caveats": []
    }

    # 2. Deck validation
    report["adapters"]["deck_validator"] = {
        "status": "available",
        "deck": deck_validator_adapter(report["decklist"]) if deck_validator_adapter and report["decklist"] else {},
        "caveats": []
    }

    # 3. Card tags (Tagger)
    report["adapters"]["tagger"] = {
        "status": "available",
        "deck": {},
        "caveats": []
    }

    # 4. Commander Spellbook combos
    report["adapters"]["commander_spellbook"] = {
        "status": "available",
        "deck": commander_spellbook_adapter(report["decklist"]) if commander_spellbook_adapter and report["decklist"] else {},
        "caveats": []
    }

    # 5. Hypercalculator probabilities (tag-based)
    report["adapters"]["hypercalculator"] = {
        "status": "available",
        "deck": hypercalculator_adapter(report["decklist"]) if hypercalculator_adapter and report["decklist"] else {},
        "caveats": []
    }

    # 6. Meta context (CEDHStats)
    report["adapters"]["meta_compare"] = {
        "status": "available",
        "deck": meta_compare_adapter(report["decklist"]) if meta_compare_adapter and report["decklist"] else {},
        "caveats": []
    }

    # 7. LearnCEDH deck summary
    report["adapters"]["learncedh"] = {
        "status": "available",
        "deck": learncedh_adapter(deck_name=report["decklist"][0]) if learncedh_adapter and report["decklist"] else {},
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

        print("\\n  SUMMARY:")
        if "report" in report and isinstance(report["report"], dict) and "deck_summary" in report["report"]:
            ds = report["report"]["deck_summary"]
            print(f"    Cards: {ds.get('card_count', 'N/A')}")
            print(f"    Commander: {ds.get('has_commander', False)}")
        elif "decklist" in report:
            print(f"    Cards: {len(report['decklist'])}")
        else:
            print("    Cards: N/A")

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
        card_result = {}
        if scryfall_num_adapter is not None:
            card_result = scryfall_num_adapter(
                mode="scryfall",
                decklist=[args.card],
                options={"lookup_mode": "single"},
            )
        report["adapters"]["scryfall"]["deck"] = card_result
        report["adapters"]["tagger"]["deck"] = {}

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
"""Scryfall adapter — card info retrieval for the nebula package.

Single source of truth: the Scryfall API.
Optional local cache: cards.json (pre-fetched from bulk data).

Fallback chain (locked down):
1. Local cache check — cards.json (fast, no network)
2. Scryfall API — fetch any card not in cache
3. Skip — card not found in either source; return PARTIAL

The adapter is the single data-fetching layer; the LLM never reads files directly.
"""

import json
import urllib.request
import urllib.error
import urllib.parse  # used in Scryfall API lookups

# Local cache path (optional — not a hard dependency).
CACHE_PATH = "/c/Users/Main/Desktop/mtg_laya_project/nodes/00_CardTruth/cards.json"

# Scryfall API
API_BASE = "https://api.scryfall.com"


def _load_cache():
    """Load local cards.json cache. Returns empty dict if missing or invalid."""
    try:
        with open(CACHE_PATH) as f:
            data = json.load(f)
            # Build lookup from card name (lowercase), since cards.json
            # uses 'name' not 'lowercase_name'.
            return {str(c.get("name", "")): c for c in data.get("cards", [])}
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {}


def _fetch_from_api(card_name):
    """Fetch a single card from the Scryfall API.

    First tries exact name lookup (/cards/:name), then falls back to
    search (/cards/search) and returns the best match.
    """
    import urllib.parse

    # 1. Exact name lookup (card name, not slug)
    try:
        url = f"{API_BASE}/cards/{urllib.parse.quote(card_name, safe='')}"
        req = urllib.request.Request(url, headers={"User-Agent": "nebula/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("object") == "card":
                return data
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        pass

    # 2. Search fallback
    try:
        search_url = f"{API_BASE}/cards/search?q={urllib.parse.quote(card_name)}"
        req = urllib.request.Request(search_url, headers={"User-Agent": "nebula/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            # Best match = first result
            if data.get("data"):
                return data["data"][0]
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        pass

    raise ValueError(f"Card not found: {card_name}")


def _build_card_info(card_data):
    """Build the output schema from a Scryfall card object."""
    return {
        "card": card_data.get("name", ""),
        "scryfall_set": card_data.get("set", ""),
        "scryfall_collector_number": card_data.get("collector_number", ""),
        "name": card_data.get("name", ""),
        "lowercase_name": card_data.get("normalized", ""),
        "mana_cost": card_data.get("mana_cost", ""),
        "cmc": float(card_data.get("cmc", 0)),
        "color_identity": card_data.get("color_identity", []),
        "color_identity_count": len(card_data.get("color_identity", [])),
        "type_line": card_data.get("type_line", ""),
        "power": card_data.get("power", None),
        "toughness": card_data.get("toughness", None),
        "keywords": card_data.get("keywords", []),
        "keyword_count": len(card_data.get("keywords", [])),
        "oracle_text_preview": card_data.get("oracle_text", ""),
        "edhrec_rank": card_data.get("edhrec_rank", None),
        "scryfall_uri": card_data.get("uri", ""),
        "status": "ok",
    }


def num_adapter(mode="scryfall", decklist=None, options=None):
    """Fetch card info for every card in the decklist.

    Args:
        mode: Adapter mode — always "scryfall".
        decklist: List of card names.
        options: Optional dict with include_* flags.

    Returns:
        {
            "adapter": "num_adapter",
            "mode": "scryfall",
            "status": "AVAILABLE" | "PARTIAL",
            "card_info": [...]
        }
    """
    import urllib.parse

    decklist = decklist or []
    options = options or {}

    cache = _load_cache()
    card_info_list = []
    missing = 0

    for card_name in decklist:
        # 1. Check local cache (case-insensitive key)
        key = card_name.lower().strip()
        found = None
        for cache_key, card_data in cache.items():
            if cache_key.lower().strip() == key:
                found = card_data
                break
        if found is not None:
            info = _build_card_info(found)
            info["source"] = "local_cache"
            card_info_list.append(info)
            continue

        # 2. Fetch from Scryfall API
        try:
            card_data = _fetch_from_api(key)
            info = _build_card_info(card_data)
            info["source"] = "scryfall_api"
            card_info_list.append(info)
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError, KeyError):
            missing += 1
            card_info_list.append({
                "card": card_name,
                "name": card_name,
                "source": "missing",
                "status": "PARTIAL",
            })

    status = "AVAILABLE" if missing == 0 else "PARTIAL"

    return {
        "adapter": "num_adapter",
        "mode": "scryfall",
        "status": status,
        "card_info": card_info_list,
        "cards_missing": missing,
    }


if __name__ == "__main__":
    # Quick test
    result = num_adapter(
        mode="scryfall",
        decklist=["Mind Rot", "Thrasios, Triton Hero", "Sol Ring"],
        options={"include_oracle_text": True, "include_keywords": True},
    )
    print(json.dumps(result, indent=2))
"""Deck validator adapter — validates decklists against MTG construction rules.

Foundational adapter. Every other component depends on a clean card list.

Validates:
- Format (Commander, Standard, etc.)
- Card count (99 for Commander, 60 for Standard, etc.)
- Commander inclusion (exactly one commander)
- Singleton rules (no duplicate non-commander cards)
- Color identity (commander color identity)
- Banned cards (Commander ban list, if cached)

Fallback chain (locked down):
1. Local cache (cards.json) — card facts
2. Scryfall API — card facts (fallback)
3. Local ban list — banned-card check (if cached)

The adapter is the single data-fetching layer; the LLM never reads files directly.
"""

import json

# Local card cache path.
CACHE_PATH = "/c/Users/Main/Desktop/mtg_laya_project/nodes/00_CardTruth/cards.json"

# Commander ban list (optional — not hard dependency)
BANLIST_PATH = "/c/Users/Main/Desktop/project front gate/Projects/nebula/config/commander_banlist.json"

# Commander format rules
COMMANDER_MAX_CARDS = 99
COMMANDER_COMMANDER_COUNT = 1


def _load_cache():
    """Load local cards.json cache. Returns empty dict if missing or invalid."""
    try:
        with open(CACHE_PATH) as f:
            data = json.load(f)
            return {str(c.get("name", "")): c for c in data.get("cards", [])}
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {}


def _load_banlist():
    """Load Commander ban list. Returns empty dict if missing or invalid."""
    try:
        with open(BANLIST_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {}


def _is_commander(card_name, cards_index):
    """Check if a card is a commander.

    Commander detection uses multiple signals (in order of reliability):
    1. 'alt-commander' or 'pair-commander' keyword tags (primary signal)
    2. Card name contains 'Commander' (e.g., 'Monastery, the Commander')
       This catches cards like 'Monastery, the Commander' but may have
       false positives for cards that mention 'Commander' casually.
    3. Card has a non-null edhrec_rank with rank < 1000 (proxy signal —
       top-ranked EDH commanders; threshold excludes most common cards)
    """
    card = cards_index.get(card_name)
    if not card:
        return False

    # 1. Keyword tag check (primary)
    keywords = card.get("keywords", [])
    if "alt-commander" in keywords or "pair-commander" in keywords:
        return True

    # 2. Name-based check
    if "commander" in card_name.lower():
        return True

    # 3. Proxy: EDHREC rank (top-ranked commanders only; avoids common-card false positives)
    edhrec = card.get("edhrec_rank")
    if edhrec is not None and edhrec > 0 and edhrec < 1000:
        return True

    return False


def _validate_commander_format(decklist, cards_index):
    """Validate Commander format rules."""
    issues = []
    warnings = []
    card_counts = {}
    commander_count = 0
    command_names = []

    for card_name in decklist:
        card = cards_index.get(card_name)
        if card:
            # Check for duplicates (non-commander)
            if card_name.lower().strip() in card_counts:
                card_counts[card_name.lower().strip()] += 1
            else:
                card_counts[card_name.lower().strip()] = 1

            # Check if commander
            if _is_commander(card_name, cards_index):
                commander_count += 1
                command_names.append(card_name)

    # Commander format rules
    if commander_count != 1:
        issues.append(f"Expected exactly 1 commander, found {commander_count}")

    # Card count
    total_cards = len(decklist)
    if total_cards > COMMANDER_MAX_CARDS:
        issues.append(f"Deck has {total_cards} cards, max {COMMANDER_MAX_CARDS} for Commander")

    # Duplicate non-commander cards
    duplicates = [
        name for name, count in card_counts.items()
        if count > 1 and not _is_commander(name, cards_index)
    ]
    if duplicates:
        issues.append(f"Duplicate non-commander cards: {duplicates}")

    # Commander color identity
    # (derived from commander's colors in cards.json)

    return {
        "card_counts": card_counts,
        "commander_count": commander_count,
        "total_cards": total_cards,
        "duplicates": duplicates,
        "command_names": command_names,
    }


def num_adapter(mode="deck_validator", decklist=None, options=None):
    """Validate a decklist against MTG construction rules.

    Args:
        mode: Adapter mode — always "deck_validator".
        decklist: List of card names (parsed from raw text).
        options: Optional dict with include_* flags.

    Returns:
        {
            "adapter": "num_adapter",
            "mode": "deck_validator",
            "status": "AVAILABLE" | "PARTIAL",
            "deck": {
                "format": str,
                "card_count": int,
                "commander_count": int,
                "has_commander": bool,
                "duplicates": [str],
                "color_identity": [str],
                "banned": [str],
                "format_legal": bool
            },
            "issues": [str],
            "warnings": [str],
            "caveats": [str]
        }
    """
    decklist = decklist or []
    options = options or {}

    cards_index = _load_cache()
    banlist = _load_banlist()

    # Check Commander ban list availability
    ban_list_available = len(banlist) > 0

    # Commander format validation
    validation = _validate_commander_format(decklist, cards_index)

    # Build card facts
    card_facts = {}
    for card_name in decklist:
        card = cards_index.get(card_name)
        if card:
            card_facts[card_name] = {
                "mana_cost": card.get("mana_cost", ""),
                "cmc": card.get("cmc", 0),
                "color_identity": card.get("color_identity", []),
                "type_line": card.get("type_line", ""),
                "keywords": card.get("keywords", []),
            }

    # Commander color identity
    color_identity = []
    if validation["commander_count"] == 1:
        commander = validation["command_names"][0]
        card = cards_index.get(commander)
        if card:
            color_identity = card.get("color_identity", [])

    # Banned cards check
    banned = []
    if ban_list_available:
        # Check against ban list
        for card_name in decklist:
            if card_name.lower().strip() in banlist:
                banned.append(card_name)
    else:
        # No ban list cached — warn but don't fail
        pass

    # Build output
    status = "AVAILABLE"
    if validation["duplicates"]:
        status = "PARTIAL"

    deck = {
        "format": "commander",
        "card_count": validation["total_cards"],
        "commander_count": validation["commander_count"],
        "has_commander": validation["commander_count"] == 1,
        "duplicates": validation["duplicates"],
        "color_identity": color_identity,
        "banned": banned,
        "format_legal": (
            len(validation["duplicates"]) == 0
            and validation["commander_count"] == 1
            and validation["total_cards"] == COMMANDER_MAX_CARDS
        ),
    }

    issues = validation["duplicates"] if validation["duplicates"] else []
    warnings = []
    if not ban_list_available:
        warnings.append("Commander ban list not cached; banned-card check is PARTIAL")

    caveats = []
    if not ban_list_available:
        caveats.append("Commander ban list not cached; cannot verify banned-card status")

    return {
        "adapter": "num_adapter",
        "mode": "deck_validator",
        "status": status,
        "deck": deck,
        "issues": issues,
        "warnings": warnings,
        "caveats": caveats,
    }


if __name__ == "__main__":
    # Quick test
    result = num_adapter(
        mode="deck_validator",
        decklist=["Thrasios, Triton Hero", "Sol Ring", "Ancestral Recall"],
        options={"format": "commander"},
    )
    print(json.dumps(result, indent=2))
"""LearnCEDH adapter — deck summaries and performance metrics.

Primary source: LearnCEDH community database (read-only).

Data fetching: The adapter reads from cached LearnCEDH data (local
files). During the audit, no live API calls are made.

The adapter provides:
- Deck summaries (narrative, strategy, synergies, combos)
- Performance metrics (conversion rate, meta share, 95% range, entrants, events, pilots)
- Archetype classification (complements archetype.classify)
"""

import json
import os

# Local LearnCEDH cache path (optional — not a hard dependency)
# Using a temp path that works with the terminal's MSYS path conversion
LEARNCEDH_CACHE_PATH = "C:/tmp/learncedh_cached_decks.json"

# LearnCEDH API base URL (used for reference; not called during audit)
LEARNCEDH_BASE = "https://learncedh.com"


def _load_cache():
    """Load local LearnCEDH cache. Returns empty dict if missing or invalid."""
    try:
        with open(LEARNCEDH_CACHE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {}


def _get_deck(deck_name):
    """Look up a deck by name in the cached LearnCEDH data.

    Deck names are case-insensitive. Returns the deck data or None.
    """
    cache = _load_cache()
    if not cache:
        return None

    # Try exact name match first
    if deck_name in cache:
        return cache[deck_name]

    # Case-insensitive search
    for key, data in cache.items():
        if key.lower() == deck_name.lower():
            return data
        if data.get("deck_name", "").lower() == deck_name.lower():
            return data

    return None


def num_adapter(mode="learncedh", deck_name=None, options=None):
    """Fetch deck summary and performance data from LearnCEDH.

    Args:
        mode: Adapter mode — always "learncedh".
        deck_name: Name of the deck to look up.
        options: Optional dict with include_* flags.

    Returns:
        {
            "adapter": "num_adapter",
            "mode": "learncedh",
            "status": "AVAILABLE" | "PARTIAL",
            "deck": {
                "deck_name": str,
                "commanders": [str],
                "summary": str,
                "strategy": str,
                "synergies": [{"card": str, "description": str}],
                "combos": [{"cards": [str], "description": str, "steps": int}],
                "performance": {
                    "conversion_rate": float,
                    "meta_share": float,
                    "range_95": [int, int],
                    "entrants": int,
                    "events": int,
                    "pilots": int,
                    "timeframe": str
                }
            },
            "archetype": str (turbo/stax/control/storm)
        }
    """
    deck_name = deck_name or ""
    options = options or {}

    deck = _get_deck(deck_name)

    if deck is None:
        return {
            "adapter": "num_adapter",
            "mode": "learncedh",
            "status": "PARTIAL",
            "deck": {
                "deck_name": deck_name,
                "commanders": [],
                "summary": "",
                "strategy": "",
                "synergies": [],
                "combos": [],
                "performance": {
                    "conversion_rate": None,
                    "meta_share": None,
                    "range_95": None,
                    "entrants": None,
                    "events": None,
                    "pilots": None,
                    "timeframe": None,
                },
            },
            "archetype": None,
            "caveats": ["Deck not found in LearnCEDH cache. Use live API for real-time data."],
        }

    # Extract data from cache
    deck_data = deck.get("deck_name", deck_name)
    commanders = deck.get("commanders", [])

    # Parse performance metrics
    perf = deck.get("performance", {})
    performance = {
        "conversion_rate": perf.get("conversion_rate"),
        "meta_share": perf.get("meta_share"),
        "range_95": perf.get("range_95"),
        "entrants": perf.get("entrants"),
        "events": perf.get("events"),
        "pilots": perf.get("pilots"),
        "timeframe": perf.get("timeframe"),
    }

    # Detect archetype from deck metadata
    archetype = deck.get("archetype", detect_archetype_from_summary(deck.get("summary", "")))

    return {
        "adapter": "num_adapter",
        "mode": "learncedh",
        "status": "AVAILABLE",
        "deck": {
            "deck_name": deck_data,
            "commanders": commanders,
            "summary": deck.get("summary", ""),
            "strategy": deck.get("strategy", ""),
            "synergies": deck.get("synergies", []),
            "combos": deck.get("combos", []),
            "performance": performance,
        },
        "archetype": archetype,
        "caveats": ["Data sourced from LearnCEDH community database (not official tournament records)."],
    }


def detect_archetype_from_summary(summary):
    """Detect archetype (turbo/stax/control/storm) from summary text.

    Uses keyword matching against the summary text.
    """
    summary_lower = summary.lower()

    # Heuristic classification
    if any(kw in summary_lower for kw in ["combo", "combo win", "combo finish", "combo line"]):
        return "turbo/stax"
    if any(kw in summary_lower for kw in ["grindy", "grind", "value engine", "self-mill", "recursive"]):
        return "control/stax"
    if any(kw in summary_lower for kw in ["tutor", "assemble", "ramp", "mana acceleration"]):
        return "control"
    if any(kw in summary_lower for kw in ["storm", "damage", "win with", "infinite"]):
        return "storm"
    if any(kw in summary_lower for kw in ["midrange", "midrange deck", "midrange strategy"]):
        return "control"

    return "unknown"


if __name__ == "__main__":
    # Quick test
    result = num_adapter(
        mode="learncedh",
        deck_name="Tymna Thrasios",
        options={"include_synergies": True, "include_combos": True},
    )
    print(json.dumps(result, indent=2))
"""Commander Spellbook adapter — stub for nebula package.

The commander spellbook adapter is not yet implemented in the nebula
package. It is replaced by the Code skill's spellbook_find_decklist_combos
and spellbook_combo_details functions.
"""


def num_adapter(mode="commander_spellbook", decklist=None, options=None):
    """Commander Spellbook combos adapter.

    Returns PARTIAL status since the adapter is not yet implemented.
    """
    return {
        "adapter": "num_adapter",
        "mode": "commander_spellbook",
        "status": "UNSUPPORTED",
        "caveat": "Commander spellbook adapter not implemented yet",
    }
"""Hypercalculator adapter — stub for nebula package.

The hypercalculator adapter is not yet implemented in the nebula package.
It is replaced by the Code skill's hypercalculator functions.
"""


def num_adapter(mode="hypercalculator", decklist=None, options=None):
    """Hypercalculator probabilities adapter.

    Returns PARTIAL status since the adapter is not yet implemented.
    """
    return {
        "adapter": "num_adapter",
        "mode": "hypercalculator",
        "status": "UNSUPPORTED",
        "caveat": "Hypercalculator adapter not implemented yet",
    }
"""Meta comparison adapter — stub for nebula package.

The meta comparison adapter is not yet implemented in the nebula package.
It is replaced by the Code skill's meta_compare functions.
"""


def num_adapter(mode="meta_compare", decklist=None, options=None):
    """Meta context adapter.

    Returns PARTIAL status since the adapter is not yet implemented.
    """
    return {
        "adapter": "num_adapter",
        "mode": "meta_compare",
        "status": "UNSUPPORTED",
        "caveat": "Meta comparison adapter not implemented yet",
    }
