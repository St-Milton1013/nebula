# NEBULA — FREQUENCY POOL — DESIGN (ARCHIVED)

**Archive date:** 2026-10-24
**Status:** ARCHIVED — superseded by `NEBULA-FREQUENCY-POOL.md` (repo root).
**Note:** This file is the original design reference. The mature blueprint now lives at `NEBULA-FREQUENCY-POOL.md` in the repo root, which supersedes this document for all implementation purposes.

Original content (untouched, for reference):
- Pipeline: num_adapter("meta_pool") → patch TopDeck events (play>=50) → last-6-months filter → parse top-16 decklists → remove stickers → remove commanders → compute frequency → compute typing averages → return headers + frequency distribution.
- Runtime filters: play_count (>=50), date (<=6 months). The 50+ filter is NOT satisfiable locally (all 25 events have 16 players) — PARTIAL.
- Output: headers block with meta-card reference info.
- Open items: live API for 50+ events; date parsing; 6-month reference date; top-N cutoff.

See `NEBULA-FREQUENCY-POOL.md` for the full, current design.
