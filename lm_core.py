"""lm_core.py — shared TOML loader for all Libris-Memoria tools."""
import tomllib
from pathlib import Path

DEFAULT_DB = Path.home() / "libris-memoria.toml"

def load(path=None):
    p = Path(path) if path else DEFAULT_DB
    with open(p, "rb") as f:
        return tomllib.load(f)

def all_series(data):
    return data.get("series", {})

def all_standalone(data):
    return data.get("standalone", {})

def get_entry(data, key):
    return data.get("series", {}).get(key) or data.get("standalone", {}).get(key)

def iter_books(data):
    for k, s in data.get("series", {}).items():
        for b in s.get("books", []):
            yield k, s, b
    for k, s in data.get("standalone", {}).items():
        yield k, s, s

def unreleased(data):
    return [(k, s, b) for k, s, b in iter_books(data) if b.get("s") == "ur"]

def genre_expand(code):
    MAP = {"F":"Fantasy","SF":"Science Fiction","A":"Adventure","Ch":"Children's","Mg":"Magic","CA":"Coming-of-age","H":"Horror","M":"Mystery","T":"Thriller","R":"Romance","HF":"Historical Fiction","NF":"Non-Fiction"}
    return MAP.get(code, code)
