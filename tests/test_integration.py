"""End-to-end P0 run against the frozen data store.

Skipped when data/card_truth.json.gz is absent (it is rebuilt, not committed).
Run:  python scripts/build_card_truth.py   then   python -m unittest discover -s tests
"""

import os
import unittest
from pathlib import Path

from nebula import legality
from nebula.cardtruth import CardTruth
from nebula.freeze import write_snapshot
from nebula.importer import load_deck

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "data" / "card_truth.json.gz"
DECK = ROOT / "tests" / "fixtures" / "ishai_rograkh.deck"


@unittest.skipUnless(TRUTH.exists(), "data/card_truth.json.gz not built")
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.truth = CardTruth.load(TRUTH)
        cls.deck = load_deck(DECK)

    def test_truth_store_is_complete(self):
        self.assertGreater(len(self.truth), 30_000)
        self.assertTrue(self.truth.version)

    def test_every_card_in_the_fixture_resolves(self):
        missing = [e.name for e in self.deck.entries if self.truth.resolve(e.name) is None]
        self.assertEqual(missing, [], f"unresolved: {missing}")

    def test_deck_import_shape(self):
        self.assertEqual(self.deck.total, 100)
        self.assertEqual(len(self.deck.commanders), 2)
        self.assertEqual(len(self.deck.mainboard), 98)

    def test_legality_on_a_real_deck(self):
        result = legality.check(self.deck, self.truth)
        codes = {f["code"]: f["status"] for f in result["findings"]}
        self.assertEqual(codes["DECK_SIZE"], "VERIFIED")
        self.assertEqual(codes["SINGLETON"], "VERIFIED")
        self.assertEqual(codes["COLOR_IDENTITY"], "VERIFIED")
        self.assertEqual(codes["BANNED"], "VERIFIED")
        self.assertEqual(codes["COMMANDER_PAIRING"], "VERIFIED")
        self.assertEqual(result["status"], "AVAILABLE", result["findings"])

    def test_snapshot_carries_the_fingerprint(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            meta = write_snapshot(self.deck, tmp, extra={"card_truth": self.truth.version})
            self.assertEqual(meta["total"], 100)
            self.assertEqual(len(meta["deck_sha256"]), 64)
            self.assertTrue(os.path.exists(meta["path"]))


if __name__ == "__main__":
    unittest.main()
