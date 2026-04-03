# Book-Release-Monitor

**Purpose:** List all unreleased (`s="ur"`) books from `libris-memoria.toml`
with days-until-release countdown.

## Usage
```bash
python monitor.py              # all unreleased books, sorted by release date
python monitor.py --soon 30    # only books releasing within 30 days
python monitor.py --json       # JSON output for scripting
```

## Output Columns
`Series | Book# | Title | Ebook date | Audio date | Days until`

## Dependencies
- `lm_core.py` (shared TOML loader, one directory up)
