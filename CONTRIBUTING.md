# Contributing

Thanks for your interest in improving TG Digest Bot!

## Ground rules

- **Never commit secrets.** `.env`, `config.py`, `*.session`, and Fly secrets are gitignored — keep them that way. Always check `git status` before you commit.
- Be mindful of the [DISCLAIMER](DISCLAIMER.md). This tool touches ToS-sensitive and privacy-sensitive territory; please don't add features that encourage abuse (mass scraping, spam, evading bans, etc.).

## How to contribute

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-thing`
3. Make a focused change
4. Test locally — at minimum `python -m py_compile digest.py`; ideally run the bot against a test group
5. Open a Pull Request describing **what** changed and **why**

## Ideas / good first issues

- Multi-target digests (`/digest @A @B` in one run)
- Configurable timezone (currently hardcoded UTC+8 in `scheduler_loop`)
- Additional output destinations / formats
- Better duplicate-group disambiguation

Bug reports and feature requests are welcome via Issues.
