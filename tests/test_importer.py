import unittest

from nebula.importer import clean_card_name, parse_decklist


class ImporterTests(unittest.TestCase):
    def test_zones_and_quantities(self):
        text = """Commander
1 Ishai, Ojutai Dragonspeaker
1 Rograkh, Son of Rohgahh

Mainboard
1 Sol Ring
2 Forest
"""
        deck = parse_decklist(text)
        self.assertEqual(deck.counts(), {"commander": 2, "mainboard": 3, "sideboard": 0})
        self.assertEqual(deck.total, 5)
        self.assertEqual([e.name for e in deck.commanders],
                         ["Ishai, Ojutai Dragonspeaker", "Rograkh, Son of Rohgahh"])

    def test_counts_are_preserved_not_stripped_from_names(self):
        deck = parse_decklist("2 Sol Ring\nSol Ring\n1x Giant Growth\n")
        names = deck.names()
        self.assertIn("Sol Ring", names)
        self.assertEqual(len(names), 3)
        self.assertEqual(deck.total, 4)

    def test_multiword_name_is_not_treated_as_count(self):
        deck = parse_decklist("Giant Growth\n")
        self.assertEqual(deck.names(), ["Giant Growth"])

    def test_printing_metadata_is_stripped(self):
        for line in (
            "1 Sol Ring (LTC) 123",
            "1 Sol Ring (LTC) 123 *F*",
            "1 Sol Ring [LTC]",
        ):
            with self.subTest(line=line):
                deck = parse_decklist(line)
                self.assertEqual(deck.names(), ["Sol Ring"])
                self.assertEqual(deck.total, 1)

    def test_two_faced_name_survives(self):
        deck = parse_decklist("1 Birgi, God of Storytelling // Harnfel, Horn of Bounty\n")
        self.assertEqual(deck.names()[0], "Birgi, God of Storytelling // Harnfel, Horn of Bounty")

    def test_no_commander_flag(self):
        deck = parse_decklist("1 Sol Ring\n")
        self.assertIn("NO_COMMANDER_DECLARED", deck.flags)
        self.assertIn("NO_ZONE_HEADERS", deck.flags)

    def test_empty_input_raises(self):
        with self.assertRaises(ValueError):
            parse_decklist("\n\n# nothing here\n")


if __name__ == "__main__":
    unittest.main()
