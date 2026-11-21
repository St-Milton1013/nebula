"""Nebula - single-deck cEDH audit pipeline.

Stdlib only. Nothing here imports ``codie.*``: nebula inherits Codie's
conclusions (frozen data), never its code. See NEBULA-CONTRACT-P0.md.
"""

__version__ = "0.1.0"

from .cardtruth import CardTruth          # noqa: F401
from .freeze import fingerprint, write_snapshot  # noqa: F401
from .importer import Deck, Entry, parse_decklist  # noqa: F401
from . import legality                    # noqa: F401
