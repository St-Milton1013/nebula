"""Runtime configuration: the numbers that are policy, not data.

Only values that a decision explicitly made adjustable belong here. Everything
else is derived. Adding a knob costs a test and a line in the contract, so this
file stays small on purpose.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

CONFIG_NAME = "nebula.config.json"
ENV_PREFIX = "NEBULA_"


@dataclass(frozen=True)
class Config:
    # D10: an event counts as cEDH at this many players. Adjustable by design -
    # the floor is a judgement call and will move as the format does.
    min_event_players: int = 30

    # D9: private first. Nothing is published, so no report carries attribution
    # obligations it cannot meet.
    share_reports: bool = False

    # D17: package derivation. These three are the difference between a stable
    # cluster and noise, so they are policy numbers, not constants.
    min_population_lists: int = 50      # lists needed to compute at all
    support_floor: float = 0.05         # a card pair must appear in 5% of lists
    stability_threshold: float = 0.80   # share of resamples a cluster must recur in

    # D17: fall back to colour identity when a commander pair is too thin.
    allow_colour_pooling: bool = True

    def as_dict(self) -> dict:
        return asdict(self)


def load(path: str | Path | None = None, env: dict | None = None) -> Config:
    """Resolve config: defaults <- json file <- environment variables."""
    env = os.environ if env is None else env
    values: dict = {}

    candidate = Path(path) if path else Path(CONFIG_NAME)
    if candidate.exists():
        raw = json.loads(candidate.read_text(encoding="utf-8"))
        known = {f.name for f in fields(Config)}
        unknown = sorted(set(raw) - known)
        if unknown:
            raise ValueError(f"unknown config keys in {candidate}: {unknown}")
        values.update({k: v for k, v in raw.items() if k in known})

    for field in fields(Config):
        key = ENV_PREFIX + field.name.upper()
        if key not in env:
            continue
        raw = env[key]
        default = field.default
        if isinstance(default, bool):
            values[field.name] = str(raw).strip().lower() in ("1", "true", "yes", "on")
        elif isinstance(default, float):
            values[field.name] = float(raw)
        elif isinstance(default, int):
            values[field.name] = int(raw)
        else:
            values[field.name] = str(raw)

    return Config(**values)


def is_cedh_event(players: int, config: Config | None = None) -> bool:
    """The event floor, applied in one place so no module invents its own."""
    return players >= (config or load()).min_event_players
