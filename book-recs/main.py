#!/usr/bin/env python3
"""BookRecs — personalized recommendations from libris-memoria.toml."""
import sys, json
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lm_core import load, iter_books, genre_expand


def build_profile(data: dict) -> dict:
    genres, authors, ratings = [], [], []
    read_count = unread_count = unreleased_count = 0
    for key, s, b in iter_books(data):
        status = b.get("s", "")
        if status == "r":
            read_count += 1
            ratings.append(b.get("r", 0))
            if b.get("ra"): ratings.append(b.get("ra"))
            authors.append(s.get("author", ""))
            for g in s.get("genres", []):
                genres.append(genre_expand(g))
        elif status == "tr":
            unread_count += 1
        elif status == "ur":
            unreleased_count += 1
    top_genres = [g for g, _ in Counter(genres).most_common(5)]
    top_authors = [a for a, _ in Counter(authors).most_common(5)]
    rated = [r for r in ratings if r]
    avg_r = round(sum(rated) / len(rated), 1) if rated else None
    return {
        "books_read": read_count,
        "books_to_read": unread_count,
        "books_unreleased": unreleased_count,
        "avg_rating": avg_r,
        "top_genres": top_genres,
        "top_authors": top_authors,
    }


def recs_prompt(profile: dict) -> str:
    return (
        f"I have read {profile['books_read']} books. "
        f"My top genres are: {', '.join(profile['top_genres'])}. "
        f"Favourite authors: {', '.join(profile['top_authors'])}. "
        f"Average rating I give: {profile['avg_rating']}/10. "
        "Based on this, suggest 5 books I haven't read yet. "
        "For each give: title, author, one-sentence reason why I'd like it."
    )


def main():
    data = load()
    args = sys.argv[1:]
    cmd = args[0] if args else "profile"
    profile = build_profile(data)
    if cmd == "profile":
        print(json.dumps(profile, indent=2))
    elif cmd == "recs":
        print(recs_prompt(profile))
        print("\n[Paste the above into Claude or any LLM to get recommendations]")
    elif cmd == "json":
        print(json.dumps(profile, separators=(",", ":")))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
