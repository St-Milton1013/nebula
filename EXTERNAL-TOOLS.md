# NEBULA — EXTERNAL TOOLS LOG

**Repo:** `nebula` (St-Milton1013/nebula)
**Purpose:** Track every external tool, API, and library the adapter will consume, with connection details, licensing, and pipeline usage.
**Status:** Draft for review — no contracts or API keys stored here (remember: vault data stays local; nothing is stored by the tool).

---

## Legend

| Marker | Meaning |
|---|---|
| **ADAPTER** | Consumed by the `num_adapter` LLM-facing tool |
| **REF** | Reference only; not called directly |
| **CACHE** | Local cached data already on disk |
| **ACTIVE** | Maintained, used for new work |
| **ARCHIVED** | No longer maintained; reference only |

---

## Quick reference

| Tool | Owner | Tool | Adapter use | Format | License |
|---|---|---|---|---|---|
| scryfall | Scryfall (Wizards) | Card data, bulk data, rules | **ADAPTER** | REST API + bulk JSON | Open (api.scryfall.com) |
| academyruins | lunakv | Rules documents (CR, MTR, IPG) | **ADAPTER** | REST API + structured JSON | Open (api.academyruins.com) |
| topdeck | TopDeck.gg | Tournament data, top-16 decklists | **ADAPTER** + local cache | JSON | Open (topdeck.gg) |
| moxfield | Moxfield | Deck decks (via mtg-parser) | **ADAPTER** | REST API + parser | Terms of Service |
| edhrec | EDHREC (Wizards) | Commander staples, synergy | **ADAPTER** | REST API | Open (edhrec.com) |
| cedhstats | CedhStats.org | CEDH stats | **ADAPTER** | REST API | Open (cedhstats.org) |
| cedhdata | CedhData.com | External meta intelligence | **ADAPTER** (optional) | REST API | **PAID** (requires consent + credentials) |
| urn | Alex Riley (ajcr) | Multivariate hypergeometric calculator | **ADAPTER** | pip package (`urn-calculator`) | Open (MIT) |
| mtg-parser | lheyberger | Decklist parser | **ADAPTER** | pip package (`mtg-parser`) | Open (PyPI) |
| mtgcompare | pvarasa | MTG card comparison | **REF** | pip package | Open (PyPI) |
| sylvan-librarian | jbylund | Card search engine (Rust query engine) | **REF** | pip package (`sylvan-librarian`) | ISC |

---

## A. Card & Rules Data (adapters)

### A1. scryfall (REST API + bulk data)
- **Owner:** Scryfall (Wizards of the Coast Fan Content Policy)
- **Purpose:** Card details (name, mana, type, oracle, colors, legality), bulk data, EDHREC rank, rule text
- **Adapter role:** PRIMARY card-truth source. Adapter is implemented at `archetype/scryfall.py` (`num_adapter(mode="scryfall", decklist, options)`).
- **Connection:** `https://api.scryfall.com` (REST) + `https://scryfall.com/bulk-data` (JSON dumps)
- **Format:** JSON (REST), bulk JSON
- **License:** Open; requires attribution
- **Pipeline stage:** Step 7 (metrics), Step 9 (roles), local card truth
- **Lock-down:** Adapter is self-contained. `cards.json` is optional local cache (pre-fetched from bulk API). Fallback chain: local cache → Scryfall API → skip (return PARTIAL). No hard dependency on `cards.json`.
- **No live API calls during the audit** — cache is pre-fetched; the adapter can be tested with the live API in a separate pass.

### A2. deck validator (deck_validator)
- **Owner:** Codie (measurement) + Jin (interpretation)
- **Purpose:** Validates decklist against Commander format rules (card count, commander inclusion, singleton, color identity, banned cards).
- **Adapter role:** Foundational adapter — every other component depends on a clean card list.
- **Connection:** Local `cards.json` cache + optional Commander ban list (`commander_banlist.json`).
- **Lock-down:** Adapter is self-contained. `cards.json` is optional for card facts. Ban list is optional — if missing, mark PARTIAL.
- **No live API calls during the audit** — local cache only.

### A3. academyruins (REST API)
- **Owner:** lunakv (Academy Ruins project)
- **Purpose:** Comprehensive Rules (CR), Magic Tournament Rules (MTR), IPG — raw and structured JSON
- **Adapter role:** Live rules lookups when the cache is insufficient; the local `rules_index_academyruins.json` (3,166 rules) is a cached snapshot of this API.
- **Connection:** `https://api.academyruins.com` (REST)
- **Format:** JSON (structured rules), XML/text (raw)
- **License:** Open (data attribution required)
- **Pipeline stage:** Step 7, Step 4 (rules), adapter `rules_lookup`

### A3. edhrec (REST API)
- **Owner:** EDHREC (Wizards of the Coast Fan Content Policy)
- **Purpose:** Commander staples, synergy scores, metagame data
- **Adapter role:** Staple lookups, synergy checks, metagame context (Steps 10–15)
- **Connection:** `https://edhrec.com/api` (REST)
- **Format:** JSON
- **Pipeline stage:** Step 10 (metagame), Step 15 (report)

### A4. cedhstats / cedhdata
- **Owner:** CedhStats.org (free), CedhData.com (paid)
- **Purpose:** CEDH tournament data, stats, meta intelligence
- **Adapter role:** `cedhstats` = free tournament/stats; `cedhdata` = premium meta analysis (requires explicit user consent + credentials — do not assume free access)
- **Connection:** `https://cedhstats.org` (REST), `https://cedhdata.com` (REST)
- **Format:** JSON
- **Pipeline stage:** Step 10 (metagame), cross-deck comparison

---

## B. Tournament & Meta Data (adapters)

### B1. topdeck (TopDeck.gg API)
- **Owner:** TopDeck.gg
- **Purpose:** Tournament metadata, top-16 decklists, standings, `cedh_eligibility`
- **Data on disk:** `mtg_laya_project/config/topdeck_*.json` (404 B / 13.7 MB / 5 MB; 25 CEDH tournaments, 400 top-16 decks)
- **Adapter role:** Meta-comparison (`archetype.meta_compare`) — parse top-16 decklists, compute archetype distributions
- **Connection:** `https://topdeck.gg/api` (REST) — live adapter also available
- **Format:** JSON
- **Caveat:** `cedh_eligibility` = `CANDIDATE_UNCONFIRMED` for all tournaments (must be flagged in reports)
- **Pipeline stage:** Step 15 (meta comparison), Step 9 (roles)

---

## C. Deck-Source Connectors (adapters)

### C1. mtg-parser (decklist parser)
- **Owner:** lheyberger
- **Purpose:** Download and parse MTG decklists from MTGO, MTGA, Archidekt, Moxfield, TopDeck, MTGGoldfish, Deckstats, MtGJSON, Scryfall, TappedOut, TCGplayer
- **Adapter role:** Parse raw decklists into canonical `Card` objects (name, quantity, extension, number, tags) for the tagger/bundler
- **Connection:** pip package `mtg-parser`; requires `requests`/`httpx` compatible client
- **Format:** Python `Iterable[Card]`
- **Caveat:** Moxfield ToS prohibits scraping; may need custom UA or alternative source
- **Pipeline stage:** Step 2 (tagger/bundler)

### C2. moxfield access
- **Owner:** Moxfield
- **Purpose:** Fetch user/public decks from Moxfield
- **Adapter role:** Optional deck source (if we want to support Moxfield URLs)
- **Connection:** Via `mtg-parser` (custom UA) or Moxfield API
- **Format:** JSON (API) / decklist text (parser)
- **Pipeline stage:** Step 2 (tagger/bundler)

---

## D. Calculation & Analysis Tools (adapters)

### D1. urn (multivariate hypergeometric calculator)
- **Owner:** Alex Riley (ajcr)
- **Purpose:** Compute probabilities of drawing target sets from a collection (multivariate hypergeometric)
- **Example query:** `PROBABILITY DRAW 7 FROM 'Ancestral Recall=4, Sol Ring=4, rest=52' WHERE 'x >= 1';`
- **Adapter role:** Compute draw odds per card type (opening hand, turn 1–10, etc.)
- **Connection:** pip package `urn-calculator` (optional `gmpy2` for speed)
- **Format:** CLI shell / API
- **Pipeline stage:** Step 7–8 (probability/odds), Deck analysis

### D2. mtgcompare (card comparison)
- **Owner:** pvarasa
- **Purpose:** Compare MTG cards side-by-side (mana, stats, synergy, inclusion, combos, price)
- **Adapter role:** REF — useful for card comparison tables in reports
- **Connection:** pip package `mtgcompare`
- **Pipeline stage:** Step 15 (report enhancement)

### D3. sylvan-librarian (card search engine)
- **Owner:** jbylund
- **Purpose:** MTG card search implementing Scryfall query syntax, with arithmetic expressions and Rust query engine
- **Adapter role:** REF — card search/filter tool for the LLM; Card Tagging System reference
- **Connection:** pip package `sylvan-librarian`
- **Pipeline stage:** Step 7, Step 9 (card search could be exposed as `card_search`)

---

## E. Local Cached Data (no network)

| Data | Location | Contents |
|---|---|---|
| cards.json | `mountgate_cards/` or local | 102-card card truth database (94 found, 8 not-found) |
| rules index | `nodes/00_CardTruth/rules/rules_index_academyruins.json` | 3,166 rules from Academy Ruins API |
| TopDeck config | `mtg_laya_project/config/topdeck_*.json` | 25 CEDH tournaments, 400 top-16 decks |
| local metagame | `Projects/Codie/Research/CedhStats/` | commanders.json, tournaments.json, meta.json |

These are read-only snapshots for adapter lookups; live sources are in B1/A1/A2.

---

## F. Connection & Protocol Summary

| Dimension | Value |
|---|---|
| **Network** | HTTP/REST (JSON) for all external APIs |
| **Local sources** | File reads (`cards.json`, `rules_index_*.json`, TopDeck config) |
| **Packages** | pip (`urn`, `mtg-parser`, `mtgcompare`, `sylvan-librarian`) |
| **Credentials** | None in this document; CedhData.com requires explicit consent + credentials (redacted) |
| **Caching** | Adapter results cached locally; snapshots timestamped |
| **Offline mode** | `cards.json` + local caches (TopDeck, metagame) + local rules index |

---

## Open Questions

1. **CedhData.com:** Paid — need explicit user consent + credentials before activation.
2. **Moxfield:** ToS prohibits scraping; confirm source path for Moxfield decks.
3. **TopDeck live API:** Verify the live endpoint returns `cedh_eligibility` reliably; our local cache is the authoritative snapshot.
4. **Adapter invocation:** Choose subprocess vs direct import for `urn`, `mtg-parser`, `sylvan-librarian`.

## Resolved: Scryfall adapter lock-down

- **LOCK-DOWN:** The Scryfall adapter no longer depends on `cards.json` as a hard requirement. The Scryfall API is the single authoritative source for every card field. `cards.json` is an optional local cache (pre-fetched from bulk API). Fallback chain: local cache → Scryfall API → skip (return PARTIAL). The adapter is self-contained and can be tested with the live API in a separate pass.
- **STATUS:** Implemented. Adapter code at `archetype/scryfall.py` (`num_adapter(mode="scryfall", decklist, options)`). Design doc at `NEBULA-SCRYFALL.md`.

## Resolved: Deck validator adapter

- **LOCK-DOWN:** The deck validator adapter validates decklists against Commander format rules using local card data from `cards.json`. The Commander ban list is optional — if missing, mark `PARTIAL` for banned-card checks.
- **STATUS:** Implemented. Adapter code at `archetype/deck_validator.py` (`num_adapter(mode="deck_validator", decklist, options)`). Design doc at `NEBULA-DECKVALIDATOR.md`.

---

## Cross-reference

| Capability | File | External tools used |
|---|---|---|
| `archetype.classify` | `NEBULA-ARCHETYPE-CLASSIFICATION.md` | scryfall, urn |
| `archetype.meta_compare` | `NEBULA-META-COMPARE.md`, `NEBULA-IDEAS/00-topdeck_meta_meta.md` | topdeck, cedhstats, cedhdata |
| Rules index | `nodes/00_CardTruth/rules/rules_index_academyruins.json` | academyruins |
| Tagger/bundler | `NEBULA-STEPS-DETAIL.md` | mtg-parser, moxfield |
| Card truth | local `cards.json` | scryfall (bulk), sylvan |
| Report | `NEBULA-STEPS-DETAIL.md` | mtgcompare, edhrec |

---

*Log created 2026-10-24. All entries verified against GitHub repos and API docs during research. Nothing is a hard dependency — every tool is optional and can be swapped.*
