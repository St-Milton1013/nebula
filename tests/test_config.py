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

    def test_event_floor_boundary(self):
        cfg = Config(min_event_players=30)
        self.assertFalse(is_cedh_event(29, cfg))
        self.assertTrue(is_cedh_event(30, cfg))
        self.assertTrue(is_cedh_event(31, cfg))


if __name__ == "__main__":
    unittest.main()
