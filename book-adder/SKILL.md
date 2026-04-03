# book-adder

**Purpose:** LLM-driven tool to add books to `libris-memoria.toml` from
natural language user input — with web search and StoryGraph enrichment.

---

## How It Works

The LLM acts as an orchestrator. It uses `adder.py` as a structured backend and
its own web search capability to look up metadata. The script never guesses —
it only writes what the LLM provides.

---

## LLM Protocol

When the user says something like:
> *"Add Mistborn by Brandon Sanderson, I've read book 1 and it was amazing"*
> *"Track The Stormlight Archive — I haven't started yet"*
> *"Add Project Hail Mary, I've read it, 9/10, audiobook was even better, 10/10"*

Follow these steps **in order**:

### Step 1 — Check if it already exists
```bash
python adder.py exists "<title>"
# returns: {"found": bool, "kind": ..., "key": ...}
```
If found: ask the user if they want to update it (then use `add_book` or `commit`).

### Step 2 — Emit search queries
```bash
python adder.py search "<user input>"
# returns a search plan with queries + payload schema
```
Run those queries with your web search tool. Extract:
- Full series title, author
- Number of books published + upcoming
- Genres
- Release dates for upcoming books (ebook + audiobook separately if known)

Also search StoryGraph directly:
```
site:app.thestorygraph.com <series title>
```

### Step 3 — Preview the entry
```bash
python adder.py preview '<json>'
```

Build the JSON payload from gathered metadata + user's stated status/rating:

```json
{
  "kind": "series",
  "title": "Mistborn: The Original Trilogy",
  "author": "Brandon Sanderson",
  "genres": ["F", "A"],
  "books": [
    {"n": 1, "t": "The Final Empire",    "s": "r", "r": 10},
    {"n": 2, "t": "The Well of Ascension","s": "tr"},
    {"n": 3, "t": "The Hero of Ages",     "s": "tr"}
  ]
}
```

For a standalone:
```json
{
  "kind": "standalone",
  "title": "Project Hail Mary",
  "author": "Andy Weir",
  "genres": ["SF", "A"],
  "s": "r",
  "r": 9,
  "ra": 10
}
```

The preview command returns:
- `valid`: true/false
- `errors`: list of validation messages if invalid
- `collision`: true if the key already exists
- `fragment`: the TOML that will be written — **show this to the user for confirmation**

### Step 4 — Confirm and commit
Show the user the `fragment` from preview. Ask for confirmation.
If confirmed:
```bash
python adder.py commit '<same json>'
```

If the series key already exists, `commit` **merges** new books rather than overwriting.

---

## Adding a Single Book to an Existing Series

```bash
python adder.py add_book '{"key": "dcc", "book": {"n": 8, "t": "A Parade of Horribles", "s": "ur", "release": "2026-05-12"}}'
```

Also works for updating an existing book (e.g. marking it read after release):
```bash
python adder.py add_book '{"key": "dcc", "book": {"n": 8, "s": "r", "r": 10, "ra": 10}}'
```

---

## Status & Rating Reference

| Code | Meaning |
|---|---|
| `r` | Read |
| `re` | Currently reading |
| `tr` | To-read |
| `ur` | Unreleased (requires `release` or `release_audio` date) |

| Field | Meaning | Scale |
|---|---|---|
| `r` | Book rating | 0–10 |
| `ra` | Audiobook rating | 0–10 |
| `rm` | Movie/adaptation rating | 0–10 |

## Genre Codes

```
F=Fantasy  SF=Science Fiction  A=Adventure  Ch=Children's  Mg=Magic
CA=Coming-of-age  H=Horror  M=Mystery  T=Thriller  R=Romance
HF=Historical Fiction  NF=Non-Fiction
```

The `preview` and `commit` commands also accept full genre names
(e.g. `"Fantasy"`) and will auto-convert them to codes.

---

## Dependencies
- `lm_core.py` (shared TOML loader, one directory up)
- `tomli-w` — `pip install tomli-w` (for writing TOML back to disk)
- LLM web search capability (for Step 2)
