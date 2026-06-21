#!/usr/bin/env python3
"""
由本地 digest_session.session 生成 StringSession + 砌好 Fly secrets 檔。
唔會連線 TG(純讀 local session),所以唔會同跑緊嘅 bot 撞 session。
輸出寫入 .fly_secrets.tmp(gitignored),唔會 print 機密落 stdout。
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

here = Path(__file__).parent
load_dotenv(here / ".env")

api_id = int(os.environ["TG_API_ID"])
api_hash = os.environ["TG_API_HASH"]

# 唔 .connect() — 純讀 local sqlite session 轉做 string
client = TelegramClient(str(here / "digest_session"), api_id, api_hash)
ss = StringSession.save(client.session)

if not ss or len(ss) < 100:
    raise SystemExit("❌ session 轉換失敗(string 太短),確認 digest_session.session 存在且已登入")

lines = [
    f"TG_API_ID={os.environ['TG_API_ID']}",
    f"TG_API_HASH={os.environ['TG_API_HASH']}",
    f"ANTHROPIC_API_KEY={os.environ['ANTHROPIC_API_KEY']}",
    f"TG_SESSION_STRING={ss}",
]
(here / ".fly_secrets.tmp").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"✅ 已寫 .fly_secrets.tmp(4 secrets,session string 長度 {len(ss)})")
