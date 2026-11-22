import json
import tempfile
import unittest
from pathlib import Path

from nebula.freeze import canonical, fingerprint, write_snapshot
from nebula.importer import parse_decklist


class FreezeTests(unittest.TestCase):
    def test_order_does_not_change_the_fingerprint(self):
        a = parse_decklist("Commander\n1 Rograkh, Son of Rohgahh\nMainboard\n1 Sol Ring\n1 Forest\n")
        b = parse_decklist("Mainboard\n1 Forest\n1 Sol Ring\nCommander\n1 Rograkh, Son of Rohgahh\n")
        self.assertEqual(fingerprint(a)["deck_sha256"], fingerprint(b)["deck_sha256"])

    def test_different_deck_different_hash(self):
        a = parse_decklist("1 Sol Ring\n")
        b = parse_decklist("1 Mana Crypt\n")
        self.assertNotEqual(fingerprint(a)["deck_sha256"], fingerprint(b)["deck_sha256"])

    def test_line_endings_do_not_change_the_fingerprint(self):
        # git rewrites CRLF on checkout; a byte hash of the file would drift.
        lf = parse_decklist("Commander\n1 Rograkh, Son of Rohgahh\nMainboard\n1 Sol Ring\n")
        crlf = parse_decklist(
            "Commander\r\n1 Rograkh, Son of Rohgahh\r\nMainboard\r\n1 Sol Ring\r\n")
        self.assertEqual(fingerprint(lf)["deck_sha256"], fingerprint(crlf)["deck_sha256"])
        self.assertEqual(fingerprint(lf)["text_sha256"], fingerprint(crlf)["text_sha256"])

    def test_fingerprint_has_no_volatile_byte_hash(self):
        fp = fingerprint(parse_decklist("1 Sol Ring\n"))
        self.assertIn("text_sha256", fp)
        self.assertNotIn("raw_sha256", fp)

    def test_snapshot_is_written_once_and_idempotent(self):
        deck = parse_decklist("Commander\n1 Rograkh, Son of Rohgahh\nMainboard\n1 Sol Ring\n")
        with tempfile.TemporaryDirectory() as tmp:
            first = write_snapshot(deck, tmp)
            second = write_snapshot(deck, tmp)
            self.assertTrue(Path(first["path"]).exists())
            self.assertEqual(first["deck_sha256"], second["deck_sha256"])
            self.assertEqual(len(list(Path(tmp).glob("*.json"))), 1)
            saved = json.loads(Path(first["path"]).read_text(encoding="utf-8"))
            self.assertEqual(saved["total"], 2)
            self.assertEqual(saved["schema"], 1)


if __name__ == "__main__":
    unittest.main()
