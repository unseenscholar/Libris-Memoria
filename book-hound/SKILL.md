# Book-Hound

**Purpose:** Monitor upcoming releases for series tracked in `libris-memoria.toml`.

## Data Source
Reads `~/libris-memoria.toml`. Series with `s="ur"` books already have release
dates stored. Book-Hound checks for *new* announcements not yet in the file.

## Usage
```bash
python monitor.py                # check all series with read/unreleased books
python monitor.py dcc hp        # check specific series keys
python monitor.py --all         # check every series
```

## Output
For each series: books read count, any stored unreleased entries with dates,
and StoryGraph web search results for the next expected book number.

## Dependencies
- `lm_core.py` (shared TOML loader, one directory up)
- `requests` (optional — skips web search if absent)
