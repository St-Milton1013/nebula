import json
import unittest

from nebula.decklink import (LinkError, deck_from_archidekt, deck_from_moxfield,
                             load_link, parse_deck_url)
from nebula.importer import parse_decklist

MOX = {
    "publicId": "abc",
    "boards": {
        "commanders": {"count": 1, "cards": {
            "c1": {"quantity": 1, "card": {"name": "Norman Osborn // Green Goblin"}}}},
        "mainboard": {"count": 2, "cards": {
            "c2": {"quantity": 1, "card": {"name": "Sol Ring"}},
            "c3": {"quantity": 2, "card": {"name": "Island"}}}},
        "maybeboard": {"count": 1, "cards": {
            "c4": {"quantity": 1, "card": {"name": "Mana Crypt"}}}},
    },
}

ARCH = {
    "cards": [
        {"quantity": 1, "categories": ["Commander"],
         "card": {"oracleCard": {"name": "Kraum, Ludevic's Opus"}}},
        {"quantity": 1, "categories": ["Mainboard"],
         "card": {"oracleCard": {"name": "Sol Ring"}}},
        {"quantity": 1, "categories": ["Sideboard"],
         "card": {"oracleCard": {"name": "Pyroblast"}}},
    ],
}


class UrlTests(unittest.TestCase):
    def test_parse_moxfield(self):
        self.assertEqual(parse_deck_url("https://www.moxfield.com/decks/V4ZllY7oHUGVc9AZPM2DEA"),
                         ("moxfield", "V4ZllY7oHUGVc9AZPM2DEA"))

    def test_parse_archidekt(self):
        self.assertEqual(parse_deck_url("https://archidekt.com/decks/1234567"),
                         ("archidekt", "1234567"))

    def test_unknown_host(self):
        with self.assertRaises(LinkError):
            parse_deck_url("https://example.com/decks/1")


class MoxfieldTests(unittest.TestCase):
    def test_boards_map_to_zones(self):
        deck = deck_from_moxfield(MOX, "abc")
        self.assertEqual(deck.counts(), {"commander": 1, "mainboard": 3, "sideboard": 0})
        self.assertEqual(deck.commanders[0].name, "Norman Osborn // Green Goblin")
        self.assertIn("IGNORED_BOARD:maybeboard", deck.flags)

    def test_quantity_is_kept(self):
        deck = deck_from_moxfield(MOX, "abc")
        island = [e for e in deck.entries if e.name == "Island"][0]
        self.assertEqual(island.qty, 2)

    def test_raw_rendering_is_parseable(self):
        deck = deck_from_moxfield(MOX, "abc")
        reparsed = parse_decklist(deck.raw)
        self.assertEqual(sorted((e.zone, e.qty, e.name) for e in reparsed.entries),
                         sorted((e.zone, e.qty, e.name) for e in deck.entries))

    def test_empty_deck_raises(self):
        with self.assertRaises(LinkError):
            deck_from_moxfield({"boards": {}}, "abc")


class ArchidektTests(unittest.TestCase):
    def test_categories_map_to_zones(self):
        deck = deck_from_archidekt(ARCH, "123")
        self.assertEqual(deck.counts(), {"commander": 1, "mainboard": 1, "sideboard": 1})

    def test_empty_deck_raises(self):
        with self.assertRaises(LinkError):
            deck_from_archidekt({"cards": []}, "123")


class LoadLinkTests(unittest.TestCase):
    def test_injected_fetch_is_used(self):
        calls = []

        def fake_fetch(url):
            calls.append(url)
            return json.dumps(MOX).encode("utf-8")

        deck = load_link("https://www.moxfield.com/decks/abc", fetch=fake_fetch)
        self.assertEqual(deck.total, 4)
        self.assertTrue(calls[0].startswith("https://api2.moxfield.com/v3/decks/all/abc"))

    def test_network_error_surfaces_as_link_error(self):
        def boom(url):
            raise LinkError("nope")

        with self.assertRaises(LinkError):
            load_link("https://www.moxfield.com/decks/abc", fetch=boom)


if __name__ == "__main__":
    unittest.main()
