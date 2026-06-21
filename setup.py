#!/usr/bin/env python3
"""
Interactive setup wizard for TG Digest Bot.
Walks you through creating .env and (optionally) config.py.

    python setup.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent


def ask(label, hint=None):
    if hint:
        print(f"   \033[2m{hint}\033[0m")
    return input(f"   {label}: ").strip()


def write_env():
    print("\n-- Telegram API --------------------------------")
    print("   Get these at https://my.telegram.org -> API development tools")
    api_id = ask("TG_API_ID")
    api_hash = ask("TG_API_HASH")
    print("\n-- Anthropic (Claude) API ----------------------")
    print("   Get a key at https://console.anthropic.com -> API Keys")
    ant = ask("ANTHROPIC_API_KEY")

    if not (api_id and api_hash and ant):
        print("\n   WARNING: some values were empty - re-run setup.py or edit .env later.")

    (HERE / ".env").write_text(
        f"TG_API_ID={api_id}\n"
        f"TG_API_HASH={api_hash}\n"
        f"ANTHROPIC_API_KEY={ant}\n"
        f"DIGEST_MODEL=claude-sonnet-4-6\n"
        f"DIGEST_MAX_MESSAGES=1500\n"
        f"DIGEST_MAX_IMAGES=15\n",
        encoding="utf-8",
    )
    print("\n   OK - wrote .env")


def write_config():
    print("\n-- Daily schedule (optional) -------------------")
    if input("   Set up a daily auto-digest now? (y/N): ").strip().lower() != "y":
        cfg = HERE / "config.py"
        if not cfg.exists():
            cfg.write_text("SCHEDULED_JOBS = []\n", encoding="utf-8")
        print("   Skipped - edit config.py later (see config.example.py).")
        return
    user = ask("Target username (e.g. @someone)")
    window = ask("Time window", "e.g. 1d / 12h / 7d (how far back)") or "1d"
    group = ask("Group name keyword", "part of the group's title to match")
    hh = ask("Hour to run (HKT, 0-23)", "e.g. 0 for midnight") or "0"
    mm = ask("Minute (0-59)") or "0"
    job = f'    ({hh}, {mm}, "{user}", "{window}", "{group}", None),'
    (HERE / "config.py").write_text(
        "# Personal schedule (gitignored). Format: see config.example.py\n"
        "SCHEDULED_JOBS = [\n" + job + "\n]\n",
        encoding="utf-8",
    )
    print("\n   OK - wrote config.py")


def main():
    print("=" * 48)
    print("   TG Digest Bot - Setup Wizard")
    print("=" * 48)

    if (HERE / ".env").exists():
        if input("\n.env already exists. Overwrite? (y/N): ").strip().lower() == "y":
            write_env()
        else:
            print("Keeping existing .env")
    else:
        write_env()

    write_config()

    print("\n" + "=" * 48)
    print("   Next steps")
    print("=" * 48)
    print(
        """
1. Install deps (if you haven't):
     pip install -r requirements.txt

2. First login (YOU must do this - it generates your session):
     python digest.py
   Enter your phone + the code Telegram sends (+ 2FA if set).
   When you see "listening", press Ctrl+C.

3. Try it - in any group you're in, or your Saved Messages:
     /digest @someone 1d

4. (Optional) Run 24/7 on Fly.io - see README.

NOTE: Read DISCLAIMER.md - this uses a personal account (Telegram ToS grey area).
"""
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)
