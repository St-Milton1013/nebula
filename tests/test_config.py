import json
import os
import tempfile
import unittest
from pathlib import Path

from nebula.config import Config, is_cedh_event, load


class ConfigTests(unittest.TestCase):
    def test_default_floor_is_thirty(self):
        self.assertEqual(load(env={}).min_event_players, 30)

    def test_env_override(self):
        cfg = load(env={"NEBULA_MIN_EVENT_PLAYERS": "64"})
        self.assertEqual(cfg.min_event_players, 64)

    def test_json_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "nebula.config.json"
            p.write_text(json.dumps({"min_event_players": 40}), encoding="utf-8")
            self.assertEqual(load(p, env={}).min_event_players, 40)

    def test_env_beats_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "nebula.config.json"
            p.write_text(json.dumps({"min_event_players": 40}), encoding="utf-8")
            cfg = load(p, env={"NEBULA_MIN_EVENT_PLAYERS": "50"})
            self.assertEqual(cfg.min_event_players, 50)

    def test_unknown_key_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "nebula.config.json"
            p.write_text(json.dumps({"min_events": 40}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load(p, env={})

    def test_package_derivation_defaults(self):
        cfg = load(env={})
        self.assertEqual(cfg.min_population_lists, 50)
        self.assertAlmostEqual(cfg.support_floor, 0.05)
        self.assertAlmostEqual(cfg.stability_threshold, 0.80)
        self.assertTrue(cfg.allow_colour_pooling)

    def test_float_and_bool_env_parsing(self):
        cfg = load(env={
            "NEBULA_SUPPORT_FLOOR": "0.10",
            "NEBULA_STABILITY_THRESHOLD": "0.9",
            "NEBULA_ALLOW_COLOUR_POOLING": "false",
        })
        self.assertAlmostEqual(cfg.support_floor, 0.10)
        self.assertAlmostEqual(cfg.stability_threshold, 0.9)
        self.assertFalse(cfg.allow_colour_pooling)

    def test_bool_accepts_common_spellings(self):
        for raw, expected in (("true", True), ("1", True), ("off", False), ("no", False)):
            with self.subTest(raw=raw):
                cfg = load(env={"NEBULA_SHARE_REPORTS": raw})
                self.assertEqual(cfg.share_reports, expected)

    def test_event_floor_boundary(self):
        cfg = Config(min_event_players=30)
        self.assertFalse(is_cedh_event(29, cfg))
        self.assertTrue(is_cedh_event(30, cfg))
        self.assertTrue(is_cedh_event(31, cfg))


if __name__ == "__main__":
    unittest.main()
