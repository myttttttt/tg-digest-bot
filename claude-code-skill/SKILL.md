---
name: tg-digest-setup
description: Step-by-step guide to set up TG Digest Bot — a self-hosted Telegram userbot that summarizes a specific person's group messages with Claude. Trigger when the user has cloned the tg-digest-bot repo and wants help installing, configuring schedules, or deploying it to Fly.io.
---

# TG Digest Bot — Setup Guide

You are guiding a user through setting up **TG Digest Bot**. Go step by step, confirm each step works before moving to the next, and keep it concise.

## Before you start
- Confirm the user is inside the cloned `tg-digest-bot` repo directory.
- Confirm Python 3.10+ is available (`python3 --version`).

## Step 1 — Install dependencies
```
pip install -r requirements.txt
```

## Step 2 — Credentials & .env
Easiest: have them run `python setup.py` and walk through the prompts.
Or create `.env` manually with:
- `TG_API_ID` + `TG_API_HASH` — from https://my.telegram.org → API development tools
- `ANTHROPIC_API_KEY` — from https://console.anthropic.com → API Keys

## Step 3 — First login (THE USER MUST DO THIS THEMSELVES)
⚠️ You cannot do this step for them — Telegram login is interactive.
Tell them to run `python digest.py`, enter their phone number, then the login
code Telegram sends (and 2FA password if enabled). When they see `listening`,
login worked and the session is saved to `digest_session.session`.

## Step 4 — Test
Have them type `/digest @someone 1d` in any group they're a member of — or in
their **Saved Messages** with a group keyword: `/digest @someone 1d groupkeyword`.
The summary appears in Saved Messages.

## Step 5 — Daily schedule (optional)
Edit `config.py` (format in `config.example.py`). Each job is:
`(HKT_hour, HKT_minute, "@target", "window", "group_keyword", forward_or_None)`
where `forward_or_None` is `None` or `("group_invite_hash", "forum_topic_keyword")`.

## Step 6 — Deploy 24/7 on Fly.io (optional)
1. `python export_session.py` → writes `.fly_secrets.tmp` (StringSession + keys)
2. `flyctl apps create their-app-name`
3. `flyctl secrets import -a their-app-name < .fly_secrets.tmp` then `rm .fly_secrets.tmp`
4. `flyctl deploy -a their-app-name --ha=false`  ← MUST be a single instance

## Key rules (do not skip)
- A userbot must run as **exactly one instance** — never scale beyond 1, or Telegram invalidates the session.
- Remind them to read `DISCLAIMER.md` — userbot automation is a Telegram ToS grey area and it processes third-party messages.
- Never let them commit `.env`, `config.py`, or `*.session` (all gitignored by default).
