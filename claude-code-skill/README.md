# Claude Code skill — guided setup

If you use [Claude Code](https://claude.com/claude-code), this skill lets Claude
walk you through setting up TG Digest Bot interactively (install → credentials →
login → schedule → deploy).

## Install

```bash
mkdir -p ~/.claude/skills/tg-digest-setup
cp SKILL.md ~/.claude/skills/tg-digest-setup/SKILL.md
```

## Use

Open Claude Code inside the cloned `tg-digest-bot` repo and say:

> set up tg digest bot

Claude will pick up the `tg-digest-setup` skill and guide you step by step.

> Note: the Telegram login step (entering your phone + verification code) is
> interactive and must be done by you — Claude can't do it for you. The skill
> just guides and runs the non-interactive parts.
