# TG Digest Bot

A self-hostable Telegram **userbot** that summarizes what specific people said in a group over a time window — powered by Claude.

It reads message history, filters by sender, summarizes (text **and** chart/data images), delivers the result to your Saved Messages, can optionally forward to a forum topic, and can run on a daily schedule — 24/7 on Fly.io or locally.

> ⚠️ **Read [DISCLAIMER.md](DISCLAIMER.md) before using.** This logs in as a *user account* (not a Bot API bot), which is against the spirit of Telegram's ToS for automation, and it processes/redistributes other people's messages. Use responsibly and at your own risk.

## Why a userbot (not a Bot API bot)?

Bot API bots **cannot read group history** or messages from senders before the bot joined. A userbot (logged in as you) can read any history you already have access to — which is exactly what "summarize person X over the last N days" needs.

## Features

- `/digest @user 7d` — summarize a user's messages over a window, on demand
- **Stealth mode** — run the command from your own Saved Messages so it isn't visible in the group
- **Image-aware** — reads K-line / data / chart screenshots (Claude vision) and folds them into the summary
- **Daily scheduled digests**
- **Optional auto-forward** to a forum topic
- Plain-text, Telegram-friendly output (no broken Markdown tables)

## Prerequisites

- Telegram `api_id` + `api_hash` — https://my.telegram.org
- Anthropic API key — https://console.anthropic.com
- (For 24/7) a Fly.io account

## Setup

```bash
git clone <your-repo-url> && cd tg-digest-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill TG_API_ID / TG_API_HASH / ANTHROPIC_API_KEY
cp config.example.py config.py   # set scheduled jobs (optional; see comments inside)
```

### First login (generates your session)

```bash
set -a; source .env; set +a
python3 digest.py
```

Enter your phone + the login code (and 2FA password if enabled). The session is saved to `digest_session.session`. Once you see `listening`, it's working. Ctrl+C to stop.

## Usage

In any group you're a member of:

```
/digest @username 7d                      # last 7 days
/digest @username 12h                      # last 12 hours
/digest @username 2026-05-01 2026-06-01    # explicit UTC date range
/digest 7d                                 # reply to a message first, then send
```

**Stealth mode** — type in your own **Saved Messages** and add a group keyword at the end:

```
/digest @username 1d mygroupkeyword
/digest @username 1d mygroupkeyword #2     # pick the Nth match if names collide
```

Output is sent to your Saved Messages and also saved under `reports/`.

## Daily schedule

Edit `config.py` (format documented in `config.example.py`):

```python
SCHEDULED_JOBS = [
    (0, 0, "@someone", "1d", "mygroup", None),                       # daily 00:00
    (8, 30, "@someone", "12h", "mygroup", ("inviteHash", "alpha")),  # + forward to a topic
]
```

Times are **HKT (UTC+8)**; change the `+8` offset in `scheduler_loop` for other timezones.

## Deploy to Fly.io (24/7)

After a successful local login:

```bash
python3 export_session.py                       # writes .fly_secrets.tmp (StringSession + keys)
flyctl apps create your-app-name
flyctl secrets import -a your-app-name < .fly_secrets.tmp
rm .fly_secrets.tmp
flyctl deploy -a your-app-name --ha=false       # MUST be single instance
```

> ⚠️ A userbot must run as **exactly one instance**. Never scale beyond 1 — Telegram invalidates the session if the same login connects from two places.

Edit `app` in `fly.toml` to your app name (or just pass `-a your-app-name` to every command).

## Manage

```bash
flyctl logs -a your-app-name
flyctl deploy -a your-app-name --ha=false --strategy immediate   # after a code change
```

## License

MIT — see [LICENSE](LICENSE).
