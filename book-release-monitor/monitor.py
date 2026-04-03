#!/usr/bin/env python3
"""Book-Release-Monitor — show all unreleased books and days until release."""
import sys, json
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lm_core import load, unreleased


def days_until(date_str: str):
    try:
        return (date.fromisoformat(date_str) - date.today()).days
    except Exception:
        return None


def build_upcoming(data: dict) -> list:
    rows = []
    for key, s, b in unreleased(data):
        rel = b.get("release") or b.get("release_audio")
        d = days_until(rel) if rel else None
        rows.append({
            "key": key,
            "series": s.get("title", key),
            "author": s.get("author", ""),
            "book_n": b.get("n"),
            "title": b.get("t", ""),
            "release": b.get("release"),
            "release_audio": b.get("release_audio"),
            "days_until": d,
        })
    rows.sort(key=lambda r: r["days_until"] if r["days_until"] is not None else 9999)
    return rows


def main():
    data = load()
    args = sys.argv[1:]
    soon = None
    as_json = "--json" in args
    if "--soon" in args:
        idx = args.index("--soon")
        soon = int(args[idx + 1]) if idx + 1 < len(args) else 30
    rows = build_upcoming(data)
    if soon is not None:
        rows = [r for r in rows if r["days_until"] is not None and r["days_until"] <= soon]
    if as_json:
        print(json.dumps(rows, separators=(",", ":")))
        return
    if not rows:
        print("No upcoming releases found.")
        return
    print(f"{'Series':<30} {'Book':<4} {'Title':<35} {'Ebook':<12} {'Audio':<12} {'Days'}")
    print("-" * 100)
    for r in rows:
        d = f"{r['days_until']}d" if r["days_until"] is not None else "TBA"
        print(f"{r['series']:<30} {str(r['book_n']):<4} {r['title'][:34]:<35} {str(r['release'] or ''):<12} {str(r['release_audio'] or ''):<12} {d}")


if __name__ == "__main__":
    main()
