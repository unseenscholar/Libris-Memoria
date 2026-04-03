#!/usr/bin/env python3
"""
book-adder — LLM-assisted tool to add books to libris-memoria.toml.

This script is the BACKEND used by an LLM (Claude, etc.) that has web search.
The LLM calls this script's subcommands to:
  1. Search StoryGraph / web for book/series metadata
  2. Preview the TOML fragment that would be written
  3. Commit the entry to the TOML file

The LLM should follow the protocol in SKILL.md.

Usage (direct):
  python adder.py search  "<user input>"
  python adder.py preview "<json payload from LLM>"
  python adder.py commit  "<json payload from LLM>"
  python adder.py exists  "<series title or standalone title>"
  python adder.py show    "<series key>"
"""

import sys
import json
import re
import tomllib
import tomli_w          # pip install tomli-w
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lm_core import load, DEFAULT_DB

VALID_STATUSES  = {"r", "re", "tr", "ur"}
VALID_GENRES    = {"F","SF","A","Ch","Mg","CA","H","M","T","R","HF","NF"}
GENRE_MAP       = {
    "fantasy":"F", "science fiction":"SF", "sci-fi":"SF", "scifi":"SF",
    "adventure":"A", "children":"Ch", "children's":"Ch", "magic":"Mg",
    "coming-of-age":"CA", "coming of age":"CA", "horror":"H",
    "mystery":"M", "thriller":"T", "romance":"R",
    "historical fiction":"HF", "non-fiction":"NF", "nonfiction":"NF",
}


# ── helpers ────────────────────────────────────────────────────────────────────

def _slug(text: str, length: int = 8) -> str:
    """Make a short lowercase alphanumeric key."""
    return re.sub(r"[^a-z0-9]", "", text.lower())[:length]


def _parse_genres(raw: list[str]) -> list[str]:
    codes = []
    for g in raw:
        g = g.strip()
        if g in VALID_GENRES:
            codes.append(g)
        elif g.lower() in GENRE_MAP:
            codes.append(GENRE_MAP[g.lower()])
    return list(dict.fromkeys(codes))  # deduplicate, preserve order


def _validate_payload(p: dict) -> list[str]:
    """Return a list of error strings, empty = valid."""
    errs = []
    kind = p.get("kind")
    if kind not in ("series", "standalone"):
        errs.append("'kind' must be 'series' or 'standalone'")
    if not p.get("title"):
        errs.append("'title' is required")
    if not p.get("author"):
        errs.append("'author' is required")
    for g in p.get("genres", []):
        if g not in VALID_GENRES:
            errs.append(f"unknown genre code '{g}' — use one of {sorted(VALID_GENRES)}")
    if kind == "series":
        books = p.get("books", [])
        if not books:
            errs.append("series must have at least one book")
        for b in books:
            if b.get("s") not in VALID_STATUSES:
                errs.append(f"book n={b.get('n')}: unknown status '{b.get('s')}'")
            if b.get("s") == "ur" and not b.get("release") and not b.get("release_audio"):
                errs.append(f"book n={b.get('n')}: status=ur requires release or release_audio date")
            for field in ("r", "ra", "rm"):
                v = b.get(field)
                if v is not None and not (0 <= v <= 10):
                    errs.append(f"book n={b.get('n')}: {field}={v} out of range 0-10")
    else:
        if p.get("s") not in VALID_STATUSES:
            errs.append(f"standalone status '{p.get('s')}' is invalid")
        if p.get("s") == "ur" and not p.get("release") and not p.get("release_audio"):
            errs.append("standalone status=ur requires release or release_audio date")
    return errs


def _build_series_dict(p: dict) -> dict:
    entry = {
        "title":  p["title"],
        "author": p["author"],
        "genres": p.get("genres", []),
        "books":  [],
    }
    for b in p.get("books", []):
        book = {"n": b["n"], "t": b["t"], "s": b["s"]}
        for opt in ("r", "ra", "rm", "release", "release_audio"):
            if b.get(opt) is not None:
                book[opt] = b[opt]
        entry["books"].append(book)
    return entry


def _build_standalone_dict(p: dict) -> dict:
    entry = {"title": p["title"], "author": p["author"],
             "genres": p.get("genres", []), "s": p["s"]}
    for opt in ("r", "ra", "rm", "release", "release_audio"):
        if p.get(opt) is not None:
            entry[opt] = p[opt]
    return entry


def _toml_fragment(kind: str, key: str, entry: dict) -> str:
    """Render an entry as a TOML snippet for human preview."""
    lines = [f"[{kind}.{key}]"]
    lines.append(f'title  = "{entry["title"]}"')
    lines.append(f'author = "{entry["author"]}"')
    genres_str = ", ".join(f'"{g}"' for g in entry["genres"])
    lines.append(f'genres = [{genres_str}]')
    if kind == "series":
        lines.append("books  = [")
        for b in entry["books"]:
            parts = [f'n={b["n"]}', f't="{b["t"]}"', f's="{b["s"]}"']
            for opt in ("r", "ra", "rm"):
                if opt in b:
                    parts.append(f'{opt}={b[opt]}')
            for opt in ("release", "release_audio"):
                if opt in b:
                    parts.append(f'{opt}="{b[opt]}"')
            lines.append("  {" + ", ".join(parts) + "},")
        lines.append("]")
    else:
        lines.append(f's  = "{entry["s"]}"')
        for opt in ("r", "ra", "rm"):
            if opt in entry:
                lines.append(f'{opt}  = {entry[opt]}')
        for opt in ("release", "release_audio"):
            if opt in entry:
                lines.append(f'{opt} = "{entry[opt]}"')
    return "\n".join(lines)


# ── subcommands ────────────────────────────────────────────────────────────────

def cmd_exists(query: str) -> None:
    """
    Check if a title already exists in the TOML.
    Prints JSON: {"found": bool, "kind": "series"|"standalone"|null, "key": str|null}
    """
    data = load()
    q = query.lower().strip()
    for key, s in data.get("series", {}).items():
        if s.get("title", "").lower() == q:
            print(json.dumps({"found": True, "kind": "series", "key": key}))
            return
    for key, s in data.get("standalone", {}).items():
        if s.get("title", "").lower() == q:
            print(json.dumps({"found": True, "kind": "standalone", "key": key}))
            return
    print(json.dumps({"found": False, "kind": None, "key": None}))


def cmd_show(key: str) -> None:
    """Print a compact JSON view of an existing series/standalone for the LLM."""
    data = load()
    entry = data.get("series", {}).get(key) or data.get("standalone", {}).get(key)
    if not entry:
        print(json.dumps({"error": f"key '{key}' not found"}))
        return
    print(json.dumps(entry, separators=(",", ":")))


def cmd_search(user_input: str) -> None:
    """
    Emit a structured search plan for the LLM to execute.
    The LLM uses these queries with its web search tool, then calls `preview`.
    """
    queries = [
        f"site:app.thestorygraph.com {user_input}",
        f"{user_input} book series author genres",
        f"{user_input} release date",
    ]
    plan = {
        "instruction": (
            "Use your web search tool to run these queries. "
            "From the results extract: title, author, series name (if any), "
            "number of books, genres, and release dates for upcoming books. "
            "Then call: python adder.py preview '<json>'"
        ),
        "queries": queries,
        "payload_schema": {
            "kind": "series | standalone",
            "title": "string",
            "author": "string",
            "genres": ["genre code strings — e.g. F, SF, A"],
            "key": "optional short slug override",
            "books (series only)": [
                {"n": "int", "t": "string", "s": "r|re|tr|ur",
                 "r": "0-10 optional", "ra": "0-10 optional",
                 "release": "YYYY-MM-DD optional",
                 "release_audio": "YYYY-MM-DD optional"}
            ],
            "s (standalone only)": "r|re|tr|ur",
            "r": "0-10 optional", "ra": "0-10 optional", "rm": "0-10 optional",
        },
    }
    print(json.dumps(plan, indent=2))


def cmd_preview(payload_json: str) -> None:
    """Validate and render the TOML fragment. Does NOT write anything."""
    try:
        p = json.loads(payload_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid JSON: {e}"}))
        return

    # Normalise genre strings to codes
    p["genres"] = _parse_genres(p.get("genres", []))

    errs = _validate_payload(p)
    if errs:
        print(json.dumps({"valid": False, "errors": errs}))
        return

    kind = p["kind"]
    key  = p.get("key") or _slug(p["title"])
    entry = _build_series_dict(p) if kind == "series" else _build_standalone_dict(p)
    fragment = _toml_fragment(kind, key, entry)

    # Check for collision
    data = load()
    collision = key in data.get(kind, {})

    print(json.dumps({
        "valid":     True,
        "key":       key,
        "kind":      kind,
        "collision": collision,
        "fragment":  fragment,
    }, indent=2))


def cmd_commit(payload_json: str) -> None:
    """
    Write the entry to libris-memoria.toml.
    If the series key already exists, merge new books (by book number).
    """
    try:
        p = json.loads(payload_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid JSON: {e}"}))
        return

    p["genres"] = _parse_genres(p.get("genres", []))
    errs = _validate_payload(p)
    if errs:
        print(json.dumps({"committed": False, "errors": errs}))
        return

    kind  = p["kind"]
    key   = p.get("key") or _slug(p["title"])
    entry = _build_series_dict(p) if kind == "series" else _build_standalone_dict(p)

    # Load raw TOML, mutate, write back
    db_path = DEFAULT_DB
    with open(db_path, "rb") as f:
        data = tomllib.load(f)

    section = data.setdefault(kind, {})
    action  = "added"

    if key in section and kind == "series":
        # Merge books by number
        existing_nums = {b["n"] for b in section[key].get("books", [])}
        new_books     = [b for b in entry["books"] if b["n"] not in existing_nums]
        section[key]["books"].extend(new_books)
        section[key]["books"].sort(key=lambda b: b["n"])
        action = f"merged ({len(new_books)} new book(s))"
    else:
        section[key] = entry

    with open(db_path, "wb") as f:
        tomli_w.dump(data, f)

    print(json.dumps({
        "committed": True,
        "action":    action,
        "key":       key,
        "kind":      kind,
        "db_path":   str(db_path),
    }))


def cmd_add_book(payload_json: str) -> None:
    """
    Add a single book to an existing series (e.g. mark a new release, update status).
    payload: {"key": "dcc", "book": {n, t, s, r?, ra?, release?, release_audio?}}
    """
    try:
        p = json.loads(payload_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid JSON: {e}"}))
        return

    key  = p.get("key")
    book = p.get("book", {})
    if not key or not book:
        print(json.dumps({"error": "'key' and 'book' are required"}))
        return

    db_path = DEFAULT_DB
    with open(db_path, "rb") as f:
        data = tomllib.load(f)

    series = data.get("series", {}).get(key)
    if not series:
        print(json.dumps({"error": f"series key '{key}' not found"}))
        return

    books = series.get("books", [])
    existing = {b["n"]: i for i, b in enumerate(books)}
    n = book.get("n")

    if n in existing:
        # Update existing entry (e.g. status change, add rating)
        books[existing[n]].update({k: v for k, v in book.items() if v is not None})
        action = f"updated book {n}"
    else:
        books.append(book)
        books.sort(key=lambda b: b["n"])
        action = f"added book {n}"

    series["books"] = books
    with open(db_path, "wb") as f:
        tomli_w.dump(data, f)

    print(json.dumps({"committed": True, "action": action, "key": key}))


# ── main ───────────────────────────────────────────────────────────────────────

SUBCOMMANDS = {
    "search":   cmd_search,
    "preview":  cmd_preview,
    "commit":   cmd_commit,
    "exists":   cmd_exists,
    "show":     cmd_show,
    "add_book": cmd_add_book,
}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    cmd = sys.argv[1]
    arg = sys.argv[2]
    fn  = SUBCOMMANDS.get(cmd)
    if not fn:
        print(json.dumps({"error": f"unknown command '{cmd}'",
                          "available": list(SUBCOMMANDS)}))
        return
    fn(arg)


if __name__ == "__main__":
    main()
