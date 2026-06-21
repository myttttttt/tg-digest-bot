# TG Digest Bot

[English](README.md) | 繁體中文

一個可自行架設嘅 Telegram **userbot**,用 Claude 整理特定人物喺群組某段時間嘅發言。

佢會讀取訊息歷史、按發送者篩選、整理(文字**加** K 線/數據圖),將結果送到你嘅 Saved Messages,可選擇轉發去 forum topic,亦可每日定時執行 —— 喺 Fly.io 24/7 運行或本地運行。

> ⚠️ **使用前請先閱讀 [DISCLAIMER.md](DISCLAIMER.md)。** 本工具以**個人帳號**登入(並非官方 Bot API bot),違反 Telegram ToS 對自動化嘅規定,而且會處理及再分發其他人嘅訊息。請負責任咁使用,風險自負。

## 為甚麼用 userbot(而非 Bot API bot)?

Bot API bot **讀唔到群組歷史**,亦讀唔到 bot 加入之前嘅發送者訊息。Userbot(以你身份登入)可以讀取你本身有權睇到嘅任何歷史 —— 呢個正正係「整理某人過去 N 日發言」所需要嘅。

## 功能

- `/digest @user 7d` — 即時整理某人喺指定時段嘅發言
- **隱形模式** — 喺自己嘅 Saved Messages 打指令,群組成員睇唔到
- **讀圖** — 讀 K 線/數據/圖表截圖(Claude vision),融入整理
- **每日定時整理**
- **可選自動轉發**去 forum topic
- 純文字、Telegram 友善嘅輸出(唔會出現亂咗嘅 Markdown 表格)

## 需要準備

- Telegram `api_id` + `api_hash` — https://my.telegram.org
- Anthropic API key — https://console.anthropic.com
- (要 24/7)一個 Fly.io 帳號

## 安裝

```bash
git clone <your-repo-url> && cd tg-digest-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

然後可以跑**互動式 setup 精靈**…

```bash
python setup.py     # 一步步引導你填 API key,自動寫 .env / config.py
```

…或者手動設定:

```bash
cp .env.example .env              # 填 TG_API_ID / TG_API_HASH / ANTHROPIC_API_KEY
cp config.example.py config.py    # 排程(可選)
```

### 第一次登入(生成 session)

```bash
set -a; source .env; set +a
python3 digest.py
```

輸入電話 + 登入驗證碼(如有開兩步驗證,再輸入密碼)。Session 會存喺 `digest_session.session`。見到「監聽中」就代表成功,Ctrl+C 停止。

## 使用

喺任何你係成員嘅群組:

```
/digest @username 7d                      # 過去 7 日
/digest @username 12h                      # 過去 12 小時
/digest @username 2026-05-01 2026-06-01    # 指定 UTC 日期區間
/digest 7d                                 # 先 reply 一條訊息,再傳
```

**隱形模式** — 喺自己嘅 **Saved Messages** 打,喺尾加群名關鍵字:

```
/digest @username 1d 群名關鍵字
/digest @username 1d 群名關鍵字 #2          # 同名群時揀第 N 個
```

結果會送到你嘅 Saved Messages,同時存喺 `reports/`。

## 每日排程

編輯 `config.py`(格式見 `config.example.py`):

```python
SCHEDULED_JOBS = [
    (0, 0, "@someone", "1d", "mygroup", None),                       # 每日 00:00
    (8, 30, "@someone", "12h", "mygroup", ("inviteHash", "alpha")),  # + 轉發去 topic
]
```

時間用**香港時間(UTC+8)**;改 `scheduler_loop` 入面個 `+8` 可換時區。

## 部署到 Fly.io(24/7)

本地登入成功之後:

```bash
python3 export_session.py                       # 生成 .fly_secrets.tmp(StringSession + keys)
flyctl apps create your-app-name
flyctl secrets import -a your-app-name < .fly_secrets.tmp
rm .fly_secrets.tmp
flyctl deploy -a your-app-name --ha=false       # 必須單一 instance
```

> ⚠️ Userbot 必須**只跑一個 instance**。永遠唔好 scale 過 1 —— 同一登入喺兩個地方連線,Telegram 會令 session 失效。

改 `fly.toml` 入面個 `app` 做你嘅 app name(或者每個指令都用 `-a your-app-name`)。

## 管理

```bash
flyctl logs -a your-app-name
flyctl deploy -a your-app-name --ha=false --strategy immediate   # 改完 code
```

## Claude Code 用戶

想要引導式 setup?repo 入面 [`claude-code-skill/`](claude-code-skill/) 有一個 Claude Code skill —— 複製去 `~/.claude/skills/`,Claude 就會一步步帶你完成安裝、設定同部署。詳見 [claude-code-skill/README.md](claude-code-skill/README.md)。

## 授權

MIT — 見 [LICENSE](LICENSE)。
