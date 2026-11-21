import unittest

from nebula.cardtruth import CardTruth

RECORDS = [
    {"name": "Ishai, Ojutai Dragonspeaker", "color_identity": ["W", "U"],
     "type_line": "Legendary Creature - Bird Monk", "oracle_text": "Partner\nFlying",
     "legalities": {"commander": "legal"}},
    {"name": "Rograkh, Son of Rohgahh", "color_identity": ["R"],
     "type_line": "Legendary Creature - Kobold Warrior",
     "oracle_text": "Partner\nFirst strike", "legalities": {"commander": "legal"}},
    {"name": "Birgi, God of Storytelling // Harnfel, Horn of Bounty",
     "color_identity": ["R"], "type_line": "Legendary Creature // Legendary Artifact",
     "oracle_text": "", "legalities": {"commander": "legal"},
     "card_faces": [{"name": "Birgi, God of Storytelling", "oracle_text": "Whenever"},
                    {"name": "Harnfel, Horn of Bounty", "oracle_text": "Discard"}]},
    {"name": "An Offer You Can't Refuse", "color_identity": ["U"],
     "type_line": "Instant", "oracle_text": "Counter target noncreature spell.",
     "legalities": {"commander": "legal"}},
]


class CardTruthTests(unittest.TestCase):
    def setUp(self):
        self.truth = CardTruth.from_records(RECORDS)

    def test_case_insensitive(self):
        self.assertIsNotNone(self.truth.resolve("ROGRAKH, SON OF ROHGAHH"))

    def test_two_faced_front_face_alias(self):
        rec = self.truth.resolve("Birgi, God of Storytelling")
        self.assertIsNotNone(rec)
        self.assertIn("//", rec["n"])

    def test_curly_apostrophe(self):
        rec = self.truth.resolve("An Offer You Can\u2019t Refuse")
        self.assertIsNotNone(rec)

    def test_miss_returns_none(self):
        self.assertIsNone(self.truth.resolve("Definitely Not A Card"))

    def test_legality_lookup(self):
        self.assertEqual(self.truth.legality("Ishai, Ojutai Dragonspeaker"), "legal")
        self.assertIsNone(self.truth.legality("Definitely Not A Card"))


if __name__ == "__main__":
    unittest.main()
