# Libris-Memoria

> *"A memory of books"* — a personal reading library system powered by TOML
> and designed for efficient interaction with Claude and Python.

---

## Architecture

```
libris-memoria.toml        ← canonical database (single source of truth)
lm_core.py                 ← shared TOML loader used by all tools
│
├── book-adder/            ← add books from natural language via LLM + web search
├── book-hound/            ← monitor upcoming releases via StoryGraph
├── book-recs/             ← generate reading profiles + LLM rec prompts
├── book-release-monitor/  ← countdown table for unreleased books
├── book-release-reminders/← Telegram alerts on release day(s)
├── library-maintainer/    ← validate + stats on the TOML file
├── markdown-book-parser/  ← migrate old Markdown → TOML + series reports
├── series-tracker/        ← reading progress by series
└── storygraph-skill/      ← StoryGraph enrichment guidance
```

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/unseenscholar/Libris-Memoria.git
cd Libris-Memoria

# Install optional dependencies
pip install requests tomli-w

# Copy the sample database to your home directory
cp libris-memoria.toml ~/libris-memoria.toml
```

---

## Database Format (`libris-memoria.toml`)

```toml
# Genre codes: F=Fantasy  SF=Science Fiction  A=Adventure  Ch=Children's  Mg=Magic
#              CA=Coming-of-age  H=Horror  M=Mystery  T=Thriller  R=Romance
#              HF=Historical Fiction  NF=Non-Fiction
# Status codes: r=read  re=reading  tr=to-read  ur=unreleased
# Rating fields (optional, 0–10): r=book  ra=audiobook  rm=movie

[series.dcc]
title  = "Dungeon Crawler Carl"
author = "Matt Dinniman"
genres = ["A","CA","F"]
books  = [
  {n=1, t="Dungeon Crawler Carl",  s="r", r=10, ra=10},
  {n=8, t="A Parade of Horribles", s="ur", release="2026-05-12", release_audio="2026-05-26"},
]

[standalone.phm]
title  = "Project Hail Mary"
author = "Andy Weir"
genres = ["SF","A"]
s  = "r"
r  = 8
ra = 10
rm = 8
```

**Key design decisions:**
- Series metadata (author, genres) is stored **once** — not repeated per book
- Only include rating fields that exist — omit unrated fields entirely
- Unreleased books require at least one of `release=` or `release_audio=`
- Standalone books are stored under `[standalone.<key>]`; the entry itself is the book

---

## Tools

### `book-adder` — Natural Language Ingestion ✨
The primary way to add new books. The LLM uses web search and StoryGraph to
look up metadata, then writes to the TOML through a validate → preview → commit flow.

```bash
# Check if a title already exists
python book-adder/adder.py exists "Mistborn"

# Generate web search queries for a user input
python book-adder/adder.py search "Mistborn by Brandon Sanderson, read book 1, loved it"

# Preview the TOML fragment (validates without writing)
python book-adder/adder.py preview '<json payload>'

# Commit to libris-memoria.toml (merges into existing series if key exists)
python book-adder/adder.py commit '<json payload>'

# Add or update a single book in an existing series
python book-adder/adder.py add_book '{"key":"dcc","book":{"n":8,"s":"r","r":10}}'

# Dump an existing entry as compact JSON for LLM context
python book-adder/adder.py show dcc
```

**LLM workflow:** `exists` → `search` (run web queries) → `preview` (show user) → `commit`

---

### `book-hound` — Release Monitor
```bash
python book-hound/monitor.py              # all series with read/unreleased books
python book-hound/monitor.py dcc hp       # specific series by key
python book-hound/monitor.py --all        # every series
```
Checks stored `ur` entries and searches StoryGraph for next unannounced books.

---

### `book-recs` — Recommendation Prompts
```bash
python book-recs/main.py profile    # JSON reading profile
python book-recs/main.py recs       # ready-to-paste Claude prompt
python book-recs/main.py json       # compact JSON for API use
```
Aggregates your genres, authors, and ratings into a Claude-ready prompt.

**Example output (`recs`):**
```
I have read 17 books. My top genres are: Adventure, Fantasy, Science Fiction.
Favourite authors: Matt Dinniman, J.K. Rowling, Andy Weir.
Average rating I give: 9.2/10.
Based on this, suggest 5 books I haven't read yet...
```

---

### `book-release-monitor` — Countdown Table
```bash
python book-release-monitor/monitor.py              # all unreleased books
python book-release-monitor/monitor.py --soon 30    # releasing within 30 days
python book-release-monitor/monitor.py --json       # machine-readable
```

---

### `book-release-reminders` — Telegram Alerts
```bash
python book-release-reminders/telegram.py test     # verify config
python book-release-reminders/telegram.py list     # dry run for today
python book-release-reminders/telegram.py check    # send due alerts
```
Edit `book-release-reminders/config.json` with your Telegram bot token and chat ID.
Add to cron for daily checks:
```
0 9 * * * python /path/to/book-release-reminders/telegram.py check
```

---

### `library-maintainer` — Validation & Stats
```bash
python library-maintainer/main.py           # validate TOML integrity
python library-maintainer/main.py stats     # library statistics
```
Checks status codes, rating ranges, genre codes, and duplicate book numbers.

---

### `markdown-book-parser` — Migration & Reports
```bash
# One-time migration from old Markdown format
python markdown-book-parser/generate_report.py migrate old_library.md

# Series progress report
python markdown-book-parser/generate_report.py report

# JSON version
python markdown-book-parser/generate_report.py report --json
```

---

## Using with Claude

The TOML format is optimised for minimal token use. Feed only what Claude needs:

```bash
# Dump one series as compact JSON
python -c "
import tomllib, json
data = tomllib.load(open('~/libris-memoria.toml','rb'))
print(json.dumps(data['series']['dcc'], separators=(',',':')))
"
```

Or pipe the whole file — at ~50 bytes per book entry it stays lean even with
hundreds of books.

When adding books conversationally, give Claude access to `book-adder/adder.py`
and your TOML path. It will handle lookup, validation, and writing automatically.

---

## Dependencies

| Package | Required by | Install |
|---|---|---|
| `tomllib` | all tools | built-in (Python 3.11+) |
| `tomli-w` | book-adder | `pip install tomli-w` |
| `requests` | book-hound, book-release-reminders, book-adder | `pip install requests` |

All other logic uses the Python standard library.
