#!/usr/bin/env python3
"""BookReleaseReminders — Telegram notifications for upcoming releases."""
import sys, json, os
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lm_core import load, unreleased

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {
        "bot_token": os.environ.get("TG_BOT_TOKEN", ""),
        "chat_id": os.environ.get("TG_CHAT_ID", ""),
        "alert_days": [30, 7, 3, 1],
    }


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    if not HAS_REQUESTS:
        print("[reminders] requests not installed — cannot send Telegram message.")
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )
    return r.ok


def days_until(date_str: str):
    try:
        return (date.fromisoformat(date_str) - date.today()).days
    except Exception:
        return None


def build_alerts(data: dict, alert_days: list) -> list:
    alerts = []
    for key, s, b in unreleased(data):
        for field, label in [("release", "ebook"), ("release_audio", "audiobook")]:
            rel = b.get(field)
            if not rel:
                continue
            d = days_until(rel)
            if d is not None and d in alert_days:
                alerts.append({
                    "series": s.get("title", key),
                    "author": s.get("author", ""),
                    "book_n": b.get("n"),
                    "book_title": b.get("t", ""),
                    "format": label,
                    "release": rel,
                    "days": d,
                })
    return alerts


def format_message(alert: dict) -> str:
    d = alert["days"]
    when = "today! 🎉" if d == 0 else f"in *{d} day{'s' if d != 1 else ''}*"
    return (
        f"📚 *Book Release Alert*\n\n"
        f"*{alert['series']}* — Book {alert['book_n']}: _{alert['book_title']}_\n"
        f"Author: {alert['author']}\n"
        f"Format: {alert['format'].capitalize()} releases {when}\n"
        f"Date: `{alert['release']}`"
    )


def main():
    cfg = load_config()
    data = load()
    args = sys.argv[1:]
    cmd = args[0] if args else "list"
    if cmd == "test":
        ok = send_telegram(cfg["bot_token"], cfg["chat_id"], "✅ Libris-Memoria reminders connected!")
        print("Sent!" if ok else "Failed — check bot_token and chat_id in config.json")
        return
    alerts = build_alerts(data, cfg.get("alert_days", [30, 7, 3, 1]))
    if cmd == "list":
        if not alerts:
            print("No alerts scheduled for today.")
        for a in alerts:
            print(format_message(a).replace("*", "").replace("_", "").replace("`", ""))
        return
    if cmd == "check":
        if not alerts:
            print("Nothing to send today.")
            return
        for a in alerts:
            msg = format_message(a)
            ok = send_telegram(cfg["bot_token"], cfg["chat_id"], msg)
            status = "✓ sent" if ok else "✗ failed"
            print(f"[{status}] {a['series']} book {a['book_n']} ({a['format']})")


if __name__ == "__main__":
    main()
