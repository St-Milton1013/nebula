# NEBULA — Deck Intelligence Script

**Status:** Proposed  
**Implementation authorized:** No

## Goal

Build a working script that accepts a supported MTG deck URL, retrieves the deck data, runs the required analyses, and produces a consolidated report containing the crucial information needed to evaluate the deck.

The finished product is a usable tool, not merely a collection of adapters, data schemas, or package-generation infrastructure.

## Expected workflow

1. The user supplies a deck URL.
2. The script retrieves the deck through the appropriate verified MCP integration.
3. The script validates the deck and resolves card identities.
4. The script runs the available analysis adapters.
5. The script consolidates their results, preserving sources, timestamps, and limitations.
6. The script produces a readable report and a structured JSON output.

The core workflow must function without an LLM.

## Required output

The report should consolidate the most useful available information:

- **Deck identity and structure:** Commander, card count, card list, quantities, and validation results.
- **Card data:** Canonical card identities and relevant card information.
- **Deck composition:** Relevant card categories, package counts, and other supported structural metrics.
- **Combo information:** Identified combos and their supporting evidence.
- **Probability analysis:** Clearly defined, reproducible calculations based on the deck's actual contents.
- **Meta context:** Relevant tournament and metagame information, with source, timeframe, and sample limitations.
- **Theory and strategic context:** Relevant material from supported sources, distinguished from verified facts and calculated results.
- **Source and reliability information:** Which analyses succeeded, which were partial or unavailable, and where each material result originated.

The script must not invent missing information or present incomplete evidence as a complete analysis. Exact report contents depend on what the existing adapters can reliably provide.

## Implementation approach

- Use MCP integrations as the primary ingestion method for supported deck platforms, initially evaluating Moxfield and Archidekt.
- Reuse existing validation, canonicalization, and analysis adapters where they meet requirements.
- Normalize their outputs into a common structure so the script can consolidate them.
- Generate the report deterministically from recorded results; do not require an LLM to assemble the package.
- Preserve reusable data where practical to reduce redundant requests and rate-limit consumption.
- Use captured responses for repeatable tests, with limited live tests to verify external integrations.
- Add optional LLM interpretation only as a separate capability, without making it a prerequisite for the core tool.

## Delivery phases

1. **Verify inputs and outputs:** Confirm what the existing MCP integrations and adapters actually provide.
2. **Define the useful report:** Specify the essential data the user should receive and identify gaps in current capabilities.
3. **Build the working pipeline:** Connect ingestion, validation, canonicalization, analysis, and report generation.
4. **Verify correctness:** Test individual adapters and the integrated script using captured data, then conduct limited live checks.
5. **Deliver the usable script:** Provide a documented command, clear output locations, understandable failures, and a sample report.

## Definition of done

The project is complete when a user can supply a supported deck URL and run one documented command to receive a useful, consolidated deck analysis in readable and structured formats.

The output must preserve evidence and explain missing or uncertain results. The script must work without an LLM, avoid unnecessary repeated data requests, and pass tests demonstrating that its reported results match its inputs and calculation methods.

A design document, an adapter collection, or a package generator without a functioning end-to-end workflow does not satisfy this goal.
