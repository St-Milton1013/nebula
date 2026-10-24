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
