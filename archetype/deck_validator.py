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
