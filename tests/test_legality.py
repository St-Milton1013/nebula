import unittest

from nebula.cardtruth import CardTruth
from nebula.importer import parse_decklist
from nebula import legality

NAMED = [
    {"name": "Ishai, Ojutai Dragonspeaker", "color_identity": ["W", "U"],
     "type_line": "Legendary Creature - Bird Monk", "oracle_text": "Partner",
     "legalities": {"commander": "legal"}},
    {"name": "Rograkh, Son of Rohgahh", "color_identity": ["R"],
     "type_line": "Legendary Creature - Kobold Warrior", "oracle_text": "Partner",
     "legalities": {"commander": "legal"}},
    {"name": "Thrasios, Triton Hero", "color_identity": ["G", "U"],
     "type_line": "Legendary Creature - Merfolk Wizard", "oracle_text": "Partner",
     "legalities": {"commander": "legal"}},
    {"name": "Kraum, Ludevic's Opus", "color_identity": ["U", "R"],
     "type_line": "Legendary Creature - Zombie Horror", "oracle_text": "Flying",
     "legalities": {"commander": "legal"}},
    {"name": "Sol Ring", "color_identity": [], "type_line": "Artifact",
     "oracle_text": "Add CC.", "legalities": {"commander": "legal"}},
    {"name": "Golos, Tireless Pilgrim", "color_identity": [], "type_line": "Legendary Artifact Creature",
     "oracle_text": "Search your library.", "legalities": {"commander": "banned"}},
    {"name": "Forest", "color_identity": ["G"], "type_line": "Basic Land - Forest",
     "oracle_text": "", "legalities": {"commander": "legal"}},
    {"name": "Ancient Tomb", "color_identity": [], "type_line": "Land",
     "oracle_text": "Add CC.", "legalities": {"commander": "legal"}},
]

FILLERS = [
    {"name": f"Filler {i:02d}", "color_identity": [], "type_line": "Artifact",
     "oracle_text": "", "legalities": {"commander": "legal"}}
    for i in range(1, 99)
]

RECORDS = NAMED + FILLERS


def make_deck(extra: str = "",
              commanders: str = "1 Ishai, Ojutai Dragonspeaker\n1 Rograkh, Son of Rohgahh"):
    """A 100-card deck. `extra` replaces fillers so size stays legal."""
    replacements = len([ln for ln in extra.splitlines() if ln.strip()])
    fillers = 98 - replacements
    if fillers < 0:
        raise ValueError("extra too large")
    body = "\n".join(f"1 Filler {i:02d}" for i in range(1, fillers + 1))
    text = f"Commander\n{commanders}\n\nMainboard\n{body}\n{extra}"
    return parse_decklist(text)


class LegalityTests(unittest.TestCase):
    def setUp(self):
        self.truth = CardTruth.from_records(RECORDS)

    def status_of(self, result, code):
        return {f["code"]: f["status"] for f in result["findings"]}.get(code)

    def test_clean_deck(self):
        deck = make_deck()
        self.assertEqual(deck.total, 100)
        result = legality.check(deck, self.truth)
        self.assertEqual(result["status"], "AVAILABLE", result["findings"])
        self.assertEqual(result["summary"]["fails"], 0)

    def test_size_fail(self):
        deck = make_deck()
        deck.entries = [e for e in deck.entries if e.name != "Filler 98"]
        result = legality.check(deck, self.truth)
        self.assertEqual(self.status_of(result, "DECK_SIZE"), "FAIL")

    def test_singleton_fail(self):
        deck = make_deck(extra="1 Filler 01\n")
        result = legality.check(deck, self.truth)
        self.assertEqual(self.status_of(result, "SINGLETON"), "FAIL")
        self.assertIn("Filler 01", [c for f in result["findings"]
                                    if f["code"] == "SINGLETON" for c in f["cards"]])

    def test_color_identity_fail(self):
        deck = make_deck(extra="1 Forest\n")
        result = legality.check(deck, self.truth)
        self.assertEqual(self.status_of(result, "COLOR_IDENTITY"), "FAIL")

    def test_banned_fail(self):
        deck = make_deck(extra="1 Golos, Tireless Pilgrim\n")
        result = legality.check(deck, self.truth)
        self.assertEqual(self.status_of(result, "BANNED"), "FAIL")

    def test_unresolved_is_partial_not_silent(self):
        deck = make_deck(extra="1 Card That Does Not Exist\n")
        result = legality.check(deck, self.truth)
        self.assertEqual(self.status_of(result, "CARD_RESOLUTION"), "PARTIAL")
        self.assertEqual(result["status"], "PARTIAL")

    def test_partner_pairing_fails_for_non_partners(self):
        deck = make_deck(commanders="1 Ishai, Ojutai Dragonspeaker\n1 Kraum, Ludevic's Opus")
        result = legality.check(deck, self.truth)
        self.assertEqual(self.status_of(result, "COMMANDER_PAIRING"), "FAIL")

    def test_partner_pairing_passes_for_partners(self):
        deck = make_deck(commanders="1 Ishai, Ojutai Dragonspeaker\n1 Thrasios, Triton Hero")
        result = legality.check(deck, self.truth)
        self.assertEqual(self.status_of(result, "COMMANDER_PAIRING"), "VERIFIED")

    def test_color_identity_uses_union_of_both_commanders(self):
        # Ishai is WU, Rograkh is R: a red card is legal only via the second commander
        deck = make_deck(extra="1 Filler 99\n")
        truth = CardTruth.from_records(NAMED + FILLERS + [
            {"name": "Filler 99", "color_identity": ["R"], "type_line": "Instant",
             "oracle_text": "", "legalities": {"commander": "legal"}}])
        result = legality.check(deck, truth)
        self.assertEqual(self.status_of(result, "COLOR_IDENTITY"), "VERIFIED")


if __name__ == "__main__":
    unittest.main()
