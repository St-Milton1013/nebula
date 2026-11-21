# nebula

New codie iteration — modular, single-deck CEDH deck audit tool.

- **Purpose:** run an audit on a **single** CEDH deck; each audit returns useful info on **cards**, **deckbuilding**, and **meta**.
- **Status:** P0 CONTRACT LOCKED (2026-11-21) — see `NEBULA-CONTRACT-P0.md`; pipeline stages still decided one at a time.
- **Structure:**
  - `NEBULA-CHECKLIST.md` — decision menu: five principles locked, pipeline stages open (see `NEBULA-HANDBOOK.md`).
  - `NEBULA-HANDBOOK.md` — handoff doc for new chats (master rule + the codie items to decide on).
  - `NEBULA-CONTRACT-P0.md` — the frozen audit contract: inputs, evidence labels, module statuses, simulation scope, report structure.
- **Scope:** planning stage only. Code for the audit modules is written in separate chats; this repo owns the roadmap and tracking.

---

## P0 — evidence layer (branch `p0-evidence-layer`)

The first pipeline stage is built and runnable. Stdlib only; nothing imports
`codie.*`.

| Module | Contract |
|---|---|
| `nebula/importer.py` | text decklist → zones. Quantities preserved, printing metadata stripped, unparseable lines reported not dropped |
| `nebula/freeze.py` | canonical rendering + `deck_sha256` + immutable snapshot; same deck always hashes the same |
| `nebula/cardtruth.py` | frozen Scryfall index: full Oracle text, both faces, per-format legality |
| `nebula/legality.py` | 903.5a size, commander count, partner/background pairing, singleton, colour identity, ban list — every check returns a status |
| `nebula/decklink.py` | Moxfield + Archidekt via their JSON APIs (the pages are Cloudflare-protected, the APIs are not). Network is injectable, so tests never reach out |
| `nebula/tagger.py` | Scryfall Tagger store: tag ancestry, per-card tags by oracle id |
| `nebula/roles.py` | role coverage from Tagger parents (D6): ramp, draw, tutor, removal, counter, wipe, protection, stax, recursion |

```bash
python scripts/build_card_truth.py --out data/card_truth.json.gz   # 38,838 cards, 4.3 MB, ~5 s
python scripts/build_tags.py --out data/oracle_tags.json.gz        # 4,607 tags, 36,519 cards, 2.0 MB, ~2 s
python -m nebula.cli --deck tests/fixtures/ishai_rograkh.deck      # import + freeze + validate
python -m nebula.cli --link https://www.moxfield.com/decks/<id> --roles   # from a deck link
python -m unittest discover -s tests -t .                          # 49 tests
```

`data/` is rebuilt, never committed; the manifest beside it records the source
timestamp and content hash, and every result names the card-truth version it used.

Role coverage is Tagger-derived (D6). A card counts for a role when any of its tags
inherits the role's anchor tag, so `tutor-creature-giant` counts as `tutor` because the
tree says so. Lands carry no role and are excluded from the denominator; untagged cards
are listed by name rather than quietly dropped.
