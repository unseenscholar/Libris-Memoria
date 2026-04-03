#!/usr/bin/env python3
"""
Book-Hound — upcoming release monitor for Libris-Memoria.
Reads libris-memoria.toml; searches StoryGraph/web for next books in tracked series.
"""
import sys, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lm_core import load

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def search_storygraph(series_title: str, book_num: int) -> list:
    if not HAS_REQUESTS:
        return []
    queries = [f"{series_title} book {book_num}", f"{series_title} {book_num} release date"]
    results = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for q in queries:
        try:
            r = requests.get(f"https://app.thestorygraph.com/browse?search_term={q.replace(' ', '+')}", headers=headers, timeout=8)
            matches = re.findall(r'<h3[^>]*>([^<]{5,80})</h3>', r.text)
            for m in matches[:3]:
                results.append({"source": "storygraph", "text": m.strip()})
        except Exception:
            pass
    return results


def check_series(data: dict, key: str) -> dict:
    s = data["series"].get(key)
    if not s:
        return {}
    books = s.get("books", [])
    max_read = max((b["n"] for b in books if b.get("s") == "r"), default=0)
    ur_books = [b for b in books if b.get("s") == "ur"]
    next_num = max_read + 1
    report = {
        "key": key,
        "title": s["title"],
        "author": s["author"],
        "books_read": max_read,
        "unreleased": ur_books,
        "web_results": []
    }
    if ur_books:
        report["web_results"] = search_storygraph(s["title"], ur_books[0]["n"])
    elif max_read > 0:
        report["web_results"] = search_storygraph(s["title"], next_num)
    return report


def main():
    data = load()
    args = sys.argv[1:]
    if args and args[0] != "--all":
        keys = args
    elif "--all" in args:
        keys = list(data.get("series", {}).keys())
    else:
        keys = [k for k, s in data.get("series", {}).items() if any(b.get("s") in {"r", "ur"} for b in s.get("books", []))]

    for key in keys:
        r = check_series(data, key)
        if not r:
            print(f"[book-hound] Key '{key}' not found.")
            continue
        print(f"\n📚 {r['title']} by {r['author']} (read: {r['books_read']} books)")
        if r["unreleased"]:
            for b in r["unreleased"]:
                rel = b.get("release", "TBA")
                rel_a = b.get("release_audio", "")
                print(f"  ⏳ Book {b['n']}: {b['t']} — ebook: {rel}" + (f" | audio: {rel_a}" if rel_a else ""))
        if r["web_results"]:
            print("  🔍 Web mentions:")
            for w in r["web_results"][:3]:
                print(f"     [{w['source']}] {w['text']}")


if __name__ == "__main__":
    main()
