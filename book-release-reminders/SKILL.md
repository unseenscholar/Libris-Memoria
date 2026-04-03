# BookReleaseReminders

**Purpose:** Send Telegram alerts when a book in `libris-memoria.toml` is
approaching its release date.

## Setup
1. Create a Telegram bot via @BotFather, get the token.
2. Get your chat ID (send a message to your bot, then visit
   `https://api.telegram.org/bot<TOKEN>/getUpdates`).
3. Fill in `config.json` with `bot_token` and `chat_id`.
4. Add to cron: `0 9 * * * python /path/to/telegram.py check`

## Usage
```bash
python telegram.py list     # dry run — show today's alerts
python telegram.py check    # send any alerts due today
python telegram.py test     # send a test message to verify config
```

## Alert Timing
Configured via `alert_days` in `config.json`. Default: `[30, 7, 3, 1]` days
before both ebook and audiobook release dates. Each `release` and
`release_audio` field on unreleased books is monitored independently.

## Dependencies
- `lm_core.py` (shared TOML loader, one directory up)
- `requests`
