import unittest

from nebula.cardtruth import CardTruth
from nebula.importer import parse_decklist
from nebula.metrics import composition, primary_type

RECORDS = [
    {"name": "Island", "type_line": "Basic Land - Island", "cmc": 0},
    {"name": "Ancient Tomb", "type_line": "Land", "cmc": 0},
    {"name": "Sol Ring", "type_line": "Artifact", "cmc": 1},
    {"name": "Brainstorm", "type_line": "Instant", "cmc": 1},
    {"name": "Counterspell", "type_line": "Instant", "cmc": 2},
    {"name": "Birds of Paradise", "type_line": "Creature - Bird", "cmc": 1},
    {"name": "Thassa's Oracle", "type_line": "Creature - Merfolk Wizard", "cmc": 2},
    {"name": "Birgi, God of Storytelling // Harnfel, Horn of Bounty",
     "type_line": "Legendary Creature // Legendary Artifact", "cmc": 3},
    {"name": "Omniscience", "type_line": "Enchantment", "cmc": 10},
]


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.truth = CardTruth.from_records(RECORDS)
        self.deck = parse_decklist(
            "Commander\n1 Thassa's Oracle\n\nMainboard\n"
            "5 Island\n1 Ancient Tomb\n1 Sol Ring\n1 Brainstorm\n1 Counterspell\n"
            "1 Birds of Paradise\n1 Birgi, God of Storytelling // Harnfel, Horn of Bounty\n"
            "1 Omniscience\n1 Card Not In Truth\n"
        )

    def test_lands_and_nonlands(self):
        comp = composition(self.deck, self.truth)
        self.assertEqual(comp["lands"], 6)          # 5 Island + Ancient Tomb
        self.assertEqual(comp["basic_lands"], 5)
        self.assertEqual(comp["nonbasic_lands"], 1)
        self.assertEqual(comp["nonlands"], 7)       # 8 nonland minus 1 unresolved
        self.assertEqual(comp["unresolved"], 1)

    def test_curve_excludes_lands(self):
        comp = composition(self.deck, self.truth)
        self.assertEqual(sum(comp["curve"].values()), comp["nonlands"])
        self.assertEqual(comp["curve"]["6+"], 1)   # Omniscience at 10
        self.assertEqual(comp["curve"]["1"], 3)    # Sol Ring, Brainstorm, Birds

    def test_average_mana_value_ignores_lands(self):
        comp = composition(self.deck, self.truth)
        # (1+1+2+1+2+3+10) / 7
        self.assertEqual(comp["average_mana_value"], 2.86)
        self.assertEqual(comp["median_mana_value"], 2)

    def test_two_faced_card_counts_once_by_front_type(self):
        comp = composition(self.deck, self.truth)
        self.assertEqual(comp["types"]["Creature"], 3)  # Oracle, Birds, Birgi front
        self.assertEqual(comp["types"]["Artifact"], 1)  # Sol Ring only (Birgi counted as Creature)

    def test_percentages_use_nonland_denominator(self):
        comp = composition(self.deck, self.truth)
        total_pct = round(sum(comp["curve_pct"].values()), 1)
        self.assertTrue(99.0 <= total_pct <= 101.0, total_pct)


class PrimaryTypeTests(unittest.TestCase):
    def test_order_prefers_creature_over_artifact(self):
        self.assertEqual(primary_type("Artifact Creature \u2014 Golem"), "Creature")

    def test_legendary_artifact_is_artifact(self):
        self.assertEqual(primary_type("Legendary Artifact"), "Artifact")

    def test_front_face_of_dfc(self):
        self.assertEqual(primary_type("Legendary Creature // Legendary Artifact"), "Creature")

    def test_empty(self):
        self.assertEqual(primary_type(None), "Unknown")


if __name__ == "__main__":
    unittest.main()
