"""Deck links: Moxfield and Archidekt public APIs.

The page itself is behind Cloudflare, the JSON API is not - which is how the
earlier iteration solved this. Fetch the deck object, map its boards onto
commander / mainboard / sideboard, and hand back a Deck that freezes exactly
like a text file.

Network access is injectable (``fetch=``) so tests never touch the internet.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from .importer import Deck, Entry

MOXFIELD_API = "https://api2.moxfield.com/v3/decks/all/{deck_id}"
ARCHIDEKT_API = "https://archidekt.com/api/decks/{deck_id}/"
UA = "nebula-deck-audit/0.1 (+local, single-deck review)"

MOXFIELD_ZONES = {
    "commanders": "commander",
    "mainboard": "mainboard",
    "sideboard": "sideboard",
}
ARCHIDEKT_ZONES = {
    "commander": "commander",
    "mainboard": "mainboard",
    "sideboard": "sideboard",
}

_MOX = re.compile(r"moxfield\.com/decks/([A-Za-z0-9_-]+)", re.I)
_ARCH = re.compile(r"archidekt\.com/decks/(\d+)", re.I)


class LinkError(RuntimeError):
    """A deck link could not be turned into a decklist."""


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as rsp:
            return rsp.read()
    except urllib.error.HTTPError as exc:
        raise LinkError(f"{url} -> HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise LinkError(f"{url} -> {exc.reason}") from exc


def parse_deck_url(url: str) -> tuple[str, str]:
    """Return ("moxfield" | "archidekt", deck id). Raises LinkError."""
    match = _MOX.search(url)
    if match:
        return "moxfield", match.group(1)
    match = _ARCH.search(url)
    if match:
        return "archidekt", match.group(1)
    raise LinkError(f"unsupported deck link: {url}")


def _render(entries: list[Entry], source: str) -> Deck:
    """Build a Deck from API entries, with a stable text rendering for hashing."""
    deck = Deck(entries=list(entries), source=source, raw="")
    lines = []
    for zone, title in (("commander", "Commander"), ("mainboard", "Mainboard"), ("sideboard", "Sideboard")):
        rows = [e for e in deck.entries if e.zone == zone]
        if not rows:
            continue
        lines.append(title)
        lines.extend(f"{e.qty} {e.name}" for e in rows)
        lines.append("")
    deck.raw = "\n".join(lines)
    return deck


def deck_from_moxfield(payload: dict, deck_id: str = "") -> Deck:
    boards = payload.get("boards") or {}
    entries: list[Entry] = []
    flags: list[str] = []
    for board, data in boards.items():
        zone = MOXFIELD_ZONES.get(board)
        cards = (data or {}).get("cards") or {}
        if zone is None:
            if cards:
                flags.append(f"IGNORED_BOARD:{board}")
            continue
        for entry in cards.values():
            card = entry.get("card") or {}
            name = card.get("name")
            qty = int(entry.get("quantity") or 1)
            if name:
                entries.append(Entry(name=name, qty=qty, zone=zone))
    if not entries:
        raise LinkError("moxfield deck contained no cards")
    deck = _render(entries, f"moxfield:{deck_id or payload.get('publicId', '')}")
    deck.flags.extend(flags)
    if not deck.commanders:
        deck.flags.append("NO_COMMANDER_DECLARED")
    return deck


def deck_from_archidekt(payload: dict, deck_id: str = "") -> Deck:
    entries: list[Entry] = []
    flags: list[str] = []
    for row in payload.get("cards") or []:
        card = row.get("card") or {}
        oracle = card.get("oracleCard") or card
        name = oracle.get("name")
        qty = int(row.get("quantity") or 1)
        if not name:
            continue
        cats = [c.lower() for c in row.get("categories") or []]
        if "commander" in cats:
            zone = "commander"
        elif "sideboard" in cats:
            zone = "sideboard"
        else:
            zone = "mainboard"
        entries.append(Entry(name=name, qty=qty, zone=zone))
    if not entries:
        raise LinkError("archidekt deck contained no cards")
    deck = _render(entries, f"archidekt:{deck_id}")
    deck.flags.extend(flags)
    if not deck.commanders:
        deck.flags.append("NO_COMMANDER_DECLARED")
    return deck


def load_link(url: str, fetch=_http_get) -> Deck:
    """Fetch a deck from a Moxfield or Archidekt link."""
    source, deck_id = parse_deck_url(url)
    if source == "moxfield":
        payload = json.loads(fetch(MOXFIELD_API.format(deck_id=deck_id)).decode("utf-8"))
        return deck_from_moxfield(payload, deck_id)
    payload = json.loads(fetch(ARCHIDEKT_API.format(deck_id=deck_id)).decode("utf-8"))
    return deck_from_archidekt(payload, deck_id)
