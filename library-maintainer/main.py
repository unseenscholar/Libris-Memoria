#!/usr/bin/env python3
"""LibraryMaintainer — validate and report on libris-memoria.toml integrity."""
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))
from lm_core import load, iter_books, genre_expand

VALID_STATUSES = {"r", "re", "tr", "ur"}
VALID_GENRE_CODES = {"F","SF","A","Ch","Mg","CA","H","M","T","R","HF","NF"}


def validate(data: dict) -> list:
    issues = []
    for key, s, b in iter_books(data):
        loc = f"[{key}]" + (f" book {b.get('n','?')}" if b is not s else "")
        st = b.get("s")
        if st not in VALID_STATUSES:
            issues.append(f"{loc}: unknown status '{st}' — expected one of {VALID_STATUSES}")
        if st == "ur" and not b.get("release") and not b.get("release_audio"):
            issues.append(f"{loc}: status='ur' but no 'release' or 'release_audio' date set")
        for field in ("r", "ra", "rm"):
            v = b.get(field)
            if v is not None and not (0 <= v <= 10):
                issues.append(f"{loc}: {field}={v} out of range 0-10")
        for g in s.get("genres", []):
            if g not in VALID_GENRE_CODES:
                issues.append(f"[{key}]: unknown genre code '{g}'")
    for key, s in data.get("series", {}).items():
        nums = [b["n"] for b in s.get("books", [])]
        dupes = [n for n, c in Counter(nums).items() if c > 1]
        if dupes:
            issues.append(f"[{key}]: duplicate book numbers: {dupes}")
    return issues


def stats(data: dict) -> dict:
    total = read = unread = reading = unreleased_n = 0
    series_count = len(data.get("series", {}))
    standalone_count = len(data.get("standalone", {}))
    genres = []
    for _, s, b in iter_books(data):
        total += 1
        st = b.get("s", "")
        if st == "r": read += 1
        elif st == "tr": unread += 1
        elif st == "re": reading += 1
        elif st == "ur": unreleased_n += 1
        for g in s.get("genres", []):
            genres.append(genre_expand(g))
    return {
        "series": series_count,
        "standalones": standalone_count,
        "total_books": total,
        "read": read,
        "reading": reading,
        "to_read": unread,
        "unreleased": unreleased_n,
        "top_genres": [g for g, _ in Counter(genres).most_common(3)],
    }


def main():
    data = load()
    args = sys.argv[1:]
    if "stats" in args:
        s = stats(data)
        print(f"Series tracked : {s['series']}  |  Standalones: {s['standalones']}")
        print(f"Total books    : {s['total_books']}")
        print(f"  ✓ Read       : {s['read']}")
        print(f"  ↻ Reading    : {s['reading']}")
        print(f"  ○ To-read    : {s['to_read']}")
        print(f"  ⏳ Unreleased: {s['unreleased']}")
        print(f"Top genres     : {', '.join(s['top_genres'])}")
        return
    issues = validate(data)
    if not issues:
        print("✅  libris-memoria.toml — no issues found.")
    else:
        print(f"⚠️  {len(issues)} issue(s) found:\n")
        for i in issues:
            print(f"  • {i}")


if __name__ == "__main__":
    main()
