#!/usr/bin/env python3
"""
markdown-book-parser — migrate old Markdown library to libris-memoria.toml.
Also generates a human-readable series report from the TOML.
"""
import sys, re, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lm_core import load, all_series, genre_expand

STAR_MAP = {"★": 2, "½": 1}


def stars_to_int(star_str: str):
    if not star_str:
        return None
    val = sum(STAR_MAP.get(c, 0) for c in star_str)
    return min(10, val) if val else None


def parse_markdown(content: str) -> list:
    books = []
    current = {}
    field_map = {
        "title": "title", "author": "author", "status": "status",
        "series": "series", "series position": "position",
        "genre": "genre", "rating": "rating",
        "audiobook rating": "audiobook_rating", "movie rating": "movie_rating",
    }
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            if current.get("title"):
                books.append(current)
            current = {}
            continue
        m = re.match(r'\*\*([^*]+)\*\*[:\s]+(.+)', line)
        if m:
            key = m.group(1).strip().lower()
            val = m.group(2).strip()
            if key in field_map:
                current[field_map[key]] = val
    if current.get("title"):
        books.append(current)
    return books


def md_to_toml_fragment(books: list) -> str:
    series_map = {}
    standalones = []
    for b in books:
        series = b.get("series", "")
        if not series or "standalone" in series.lower():
            standalones.append(b)
        else:
            series_map.setdefault(series, []).append(b)
    lines = ["# Auto-migrated from Markdown — review before saving\n"]
    for series_name, sbooks in series_map.items():
        author = sbooks[0].get("author", "Unknown")
        key = re.sub(r'[^a-z0-9]', '', series_name.lower())[:8]
        lines.append(f'[series.{key}]')
        lines.append(f'title = "{series_name}"')
        lines.append(f'author = "{author}"')
        lines.append('genres = []  # TODO: add genre codes')
        lines.append('books = [')
        for b in sbooks:
            pos_m = re.search(r'(\d+)', b.get("position", "1"))
            n = int(pos_m.group(1)) if pos_m else 1
            t = b.get("title", "")
            s = {"read": "r", "reading": "re", "to-read": "tr"}.get(b.get("status", "").lower(), "tr")
            r = stars_to_int(b.get("rating", ""))
            ra = stars_to_int(b.get("audiobook_rating", ""))
            entry = f'  {{n={n}, t="{t}", s="{s}"'
            if r: entry += f', r={r}'
            if ra: entry += f', ra={ra}'
            entry += '},'
            lines.append(entry)
        lines.append(']\n')
    for b in standalones:
        key = re.sub(r'[^a-z0-9]', '', b.get("title", "x").lower())[:8]
        lines.append(f'[standalone.{key}]')
        lines.append(f'title = "{b.get("title", "")}"')
        lines.append(f'author = "{b.get("author", "")}"')
        lines.append('genres = []  # TODO: add genre codes')
        s = {"read": "r", "reading": "re", "to-read": "tr"}.get(b.get("status", "").lower(), "tr")
        lines.append(f's = "{s}"')
        r = stars_to_int(b.get("rating", ""))
        ra = stars_to_int(b.get("audiobook_rating", ""))
        rm = stars_to_int(b.get("movie_rating", ""))
        if r: lines.append(f'r = {r}')
        if ra: lines.append(f'ra = {ra}')
        if rm: lines.append(f'rm = {rm}')
        lines.append('')
    return '\n'.join(lines)


def series_report(data: dict, as_json=False) -> None:
    rows = []
    for key, s in all_series(data).items():
        books = s.get("books", [])
        read = [b for b in books if b.get("s") == "r"]
        total = len(books)
        ratings = [b["r"] for b in read if b.get("r")]
        avg_r = round(sum(ratings)/len(ratings), 1) if ratings else None
        rows.append({
            "key": key,
            "title": s["title"],
            "author": s["author"],
            "read": len(read),
            "total": total,
            "pct": round(len(read)/total*100) if total else 0,
            "avg_rating": avg_r,
            "genres": [genre_expand(g) for g in s.get("genres", [])],
        })
    if as_json:
        print(json.dumps(rows, separators=(",", ":")))
        return
    print(f"{'Series':<30} {'Progress':<12} {'Avg Rating':<12} Genres")
    print('-' * 75)
    for r in rows:
        filled = r['pct'] // 10
        bar = ('█' * filled) + ('░' * (10 - filled))
        avg = f"{r['avg_rating']}/10" if r['avg_rating'] else '—'
        print(f"{r['title']:<30} {r['read']}/{r['total']} {bar}  {avg:<12} {', '.join(r['genres'])}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args[0] == 'migrate' and len(args) > 1:
        content = Path(args[1]).read_text()
        books = parse_markdown(content)
        print(md_to_toml_fragment(books))
    elif args[0] == 'report':
        data = load()
        series_report(data, as_json='--json' in args)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
