# LibraryMaintainer

**Purpose:** Validate `libris-memoria.toml` for integrity issues and print
library statistics.

## Usage
```bash
python main.py          # validate — report any issues
python main.py stats    # summary stats (read/unread/unreleased counts, genres)
```

## Validation Checks
- Unknown status codes (anything outside `r re tr ur`)
- Unreleased books missing a `release` or `release_audio` date
- Ratings outside 0–10
- Unknown genre codes
- Duplicate book numbers within a series

## Dependencies
- `lm_core.py` (shared TOML loader, one directory up)
