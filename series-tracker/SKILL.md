# Series-Tracker

**Purpose:** Track reading progress by series using `libris-memoria.toml`.

## Data Model
Each series is stored once under `[series.<key>]` with shared metadata:
- `title`
- `author`
- `genres`
- `books = [{n,t,s,r,ra,rm,release,release_audio}]`

## Status Codes
- `r` = read
- `re` = reading
- `tr` = to-read
- `ur` = unreleased

## Typical Queries
- Find the next unread book in a series
- Show completion progress (`read / total`)
- List unreleased books by release date
- Export a single series as compact JSON for LLM context

## Recommended Access
Use `lm_core.py` and iterate over `data["series"]` directly rather than parsing text.
