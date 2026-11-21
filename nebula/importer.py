"""Deck import: text decklist -> zones.

Contract (NEBULA-CONTRACT-P0.md §2):
  * quantities are preserved, never stripped from a card name
  * zone membership comes from section headers, not guesses
  * an unparseable line is reported, not dropped

Recognised line shapes::

    1 Sol Ring
    1x Sol Ring
    Sol Ring                 (quantity 1)
    1 Sol Ring (LTC) 123     (set + collector number stripped)
    1 Sol Ring (LTC) 123 *F* (foil marker stripped)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

COMMANDER_HEADERS = {
    "commander", "commanders", "commander(s)", "commander deck", "command zone",
}
MAIN_HEADERS = {
    "mainboard", "main", "main deck", "maindeck", "deck", "library", "spells",
}
SIDE_HEADERS = {
    "sideboard", "maybe", "maybeboard", "companion", "tokens",
    "attractions", "contraptions", "planechase",
}

BASIC_LANDS = {
    "plains", "island", "swamp", "mountain", "forest", "wastes",
    "snow-covered plains", "snow-covered island", "snow-covered swamp",
    "snow-covered mountain", "snow-covered forest",
}

_CARD_LINE = re.compile(r"^(\d+)\s*[xX]?\s+(\S.*)$")
_SET_SUFFIX = re.compile(r"\s*\([A-Za-z0-9]{2,6}\)(\s+\d+)?\s*$")
_BRACKET_SUFFIX = re.compile(r"\s*\[[^\]]*\]\s*$")
_FOIL_SUFFIX = re.compile(r"\s*\*[A-Za-z]\*\s*$")
_TRAILING_COMMENT = re.compile(r"\s+#.*$")


@dataclass(frozen=True)
class Entry:
    name: str
    qty: int
    zone: str  # "commander" | "mainboard" | "sideboard"


@dataclass
class Deck:
    entries: list[Entry] = field(default_factory=list)
    source: str = "<text>"
    raw: str = ""
    flags: list[str] = field(default_factory=list)

    @property
    def commanders(self) -> list[Entry]:
        return [e for e in self.entries if e.zone == "commander"]

    @property
    def mainboard(self) -> list[Entry]:
        return [e for e in self.entries if e.zone == "mainboard"]

    @property
    def sideboard(self) -> list[Entry]:
        return [e for e in self.entries if e.zone == "sideboard"]

    @property
    def total(self) -> int:
        """Cards that count toward the 100-card deck (commanders + mainboard)."""
        return sum(e.qty for e in self.entries if e.zone != "sideboard")

    def counts(self) -> dict:
        out = {"commander": 0, "mainboard": 0, "sideboard": 0}
        for e in self.entries:
            out[e.zone] = out.get(e.zone, 0) + e.qty
        return out

    def names(self, zone: str | None = None) -> list[str]:
        return [e.name for e in self.entries if zone is None or e.zone == zone]


def clean_card_name(text: str) -> str:
    """Strip printing metadata, never a leading count or part of the name."""
    name = text.strip()
    name = _TRAILING_COMMENT.sub("", name)
    name = _FOIL_SUFFIX.sub("", name)
    name = _SET_SUFFIX.sub("", name)
    name = _BRACKET_SUFFIX.sub("", name)
    return name.strip()


def _header_zone(line: str) -> str | None:
    key = line.rstrip(":").strip().lower()
    if key in COMMANDER_HEADERS:
        return "commander"
    if key in MAIN_HEADERS:
        return "mainboard"
    if key in SIDE_HEADERS:
        return "sideboard"
    return None


def parse_decklist(text: str, source: str = "<text>") -> Deck:
    """Parse a decklist into zones. Raises ValueError on an empty list."""
    deck = Deck(source=source, raw=text)
    zone = "mainboard"
    zone_declared = False
    unparsed: list[str] = []

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip().lstrip("\ufeff")
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        header = _header_zone(line) if len(line) < 40 and not line[0].isdigit() else None
        if header:
            zone = header
            zone_declared = True
            continue

        match = _CARD_LINE.match(line)
        if match:
            qty, rest = int(match.group(1)), match.group(2)
        else:
            qty, rest = 1, line

        name = clean_card_name(rest)
        if not name or qty <= 0 or qty > 99:
            unparsed.append(raw_line.strip())
            continue
        deck.entries.append(Entry(name=name, qty=qty, zone=zone))

    if not deck.entries:
        raise ValueError(f"no cards parsed from {source!r}")

    if not deck.commanders:
        deck.flags.append("NO_COMMANDER_DECLARED")
    if unparsed:
        deck.flags.append(f"UNPARSED_LINES:{len(unparsed)}")
        deck.flags.extend(f"UNPARSED:{line}" for line in unparsed[:10])
    if zone_declared is False:
        deck.flags.append("NO_ZONE_HEADERS")

    return deck


def load_deck(path: str | Path) -> Deck:
    p = Path(path)
    return parse_decklist(p.read_text(encoding="utf-8"), source=str(p))
