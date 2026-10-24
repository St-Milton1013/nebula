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
