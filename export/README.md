# NEBULA Export Package

Self-contained export package for the NEBULA deck analyzer.

## Files

| File | Description |
|------|-------------|
|  | Export tool — generates JSON/text exports and single-file packages |
|  | Single-file version of the full NEBULA package (all adapters in one file) |
|  | Sample export — 23-card test decklist as JSON |

## Usage

### Export a local decklist


### Export a decklist from a Moxfield/Archidekt link

Note: Moxfield/Archidekt URLs often require Cloudflare bypass. The MCP  path is implemented but requires the MCP server to be available locally.

### Generate the single-file package


## Package Structure (nebula_package_single.py)

-  — Main entry point (, , )
-  — Scryfall card info adapter
-  — Deck validator (Commander format)
-  — LearnCEDH adapter
-  — Commander Spellbook stub (UNSUPPORTED)
-  — Hypercalculator stub (UNSUPPORTED)
-  — Meta Compare stub (UNSUPPORTED)

## Test Results

1. Local decklist (): Status: AVAILABLE, 7/7 adapters
2. Moxfield URL (): Cloudflare block (403)
3. Single-file package: Generated and verified (py_compile: OK)
