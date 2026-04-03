# StoryGraph Skill

**Purpose:** Integrate Libris-Memoria's TOML-based library with StoryGraph lookups.

## Data Source
Primary local source is `~/libris-memoria.toml`, not `library.md`.
Series keys and unreleased entries in the TOML should be treated as the source of
truth for your personal library state.

## Suggested Workflow
1. Read the local TOML entry for the relevant series.
2. If the next book is unknown, search StoryGraph using series title + expected number.
3. If a release date is found, add it back to the TOML as `release` and optionally
   `release_audio`.
4. Keep web findings separate from confirmed local library state until reviewed.

## Query Patterns
- `"<series title> book <n>"`
- `"<series title> <n> release date"`
- `"site:thestorygraph.com <series title> book <n>"`

## Best Practice
Do not scrape and overwrite existing local entries blindly. The TOML file is the
canonical personal dataset; StoryGraph is a discovery/enrichment layer.
