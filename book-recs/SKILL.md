# BookRecs

**Purpose:** Generate a reading profile and recommendation prompts from `libris-memoria.toml`.

## Usage
```bash
python main.py profile    # JSON reading profile (genres, authors, avg rating)
python main.py recs       # Ready-to-paste Claude/LLM recommendation prompt
python main.py json       # Compact JSON profile for API use
```

## How It Works
Reads all `s="r"` (read) books from the TOML, aggregates genres, authors, and
ratings, then generates a natural-language prompt you can send to Claude for
personalised recommendations.

## Dependencies
- `lm_core.py` (shared TOML loader, one directory up)
