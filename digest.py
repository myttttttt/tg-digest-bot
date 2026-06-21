#!/usr/bin/env python3
"""
TG Digest Bot — Telethon userbot 模式
你喺任何群打 `/digest @某人 7d`,腳本回溯讀歷史 → Claude 整理 → 發去 Saved Messages + 存檔。

指令格式(喺任何群,outgoing 自己打):
    /digest @username 7d                抓 @username 過去 7 日
    /digest @username 12h               過去 12 小時
    /digest @username 2026-05-01 2026-06-01   日期區間 (UTC)
    /digest 7d                          先 reply 某條消息 → 抓嗰個人

setup 見 README.md
"""

import os
import asyncio
import base64
import re
import sys
import datetime as dt
from pathlib import Path

from telethon import TelegramClient, events
import anthropic

# 自動 load 同目錄 .env(唔使每次 source)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ---- config ----
API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
MODEL = os.environ.get("DIGEST_MODEL", "claude-sonnet-4-6")
MAX_MESSAGES = int(os.environ.get("DIGEST_MAX_MESSAGES", "1500"))  # 安全閥,超過會大聲 warn
MAX_IMAGES = int(os.environ.get("DIGEST_MAX_IMAGES", "15"))  # 每次 digest 最多讀幾多張圖(控成本)
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# 雲端(Fly)用 StringSession 登入(冇得互動輸驗證碼);本地用 file session
SESSION_STRING = os.environ.get("TG_SESSION_STRING", "").strip()
if SESSION_STRING:
    from telethon.sessions import StringSession
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH, catch_up=False)
else:
    client = TelegramClient("digest_session", API_ID, API_HASH, catch_up=False)

ant = anthropic.Anthropic()  # 讀 ANTHROPIC_API_KEY


# ---- 時段 parse ----
def parse_window(tokens):
    """
    return (start_utc, end_utc, label)
    tokens 例: ['7d'] / ['12h'] / ['2026-05-01', '2026-06-01']
    """
    now = dt.datetime.now(dt.timezone.utc)
    if len(tokens) == 1:
        m = re.fullmatch(r"(\d+)([dh])", tokens[0])
        if not m:
            raise ValueError(f"睇唔明時段 `{tokens[0]}`,用 7d / 12h / 兩個日期")
        n, unit = int(m.group(1)), m.group(2)
        delta = dt.timedelta(days=n) if unit == "d" else dt.timedelta(hours=n)
        return now - delta, now, f"過去 {tokens[0]}"
    if len(tokens) == 2:
        try:
            start = dt.datetime.fromisoformat(tokens[0]).replace(tzinfo=dt.timezone.utc)
            end = dt.datetime.fromisoformat(tokens[1]).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            raise ValueError("日期格式要 YYYY-MM-DD")
        return start, end, f"{tokens[0]} → {tokens[1]}"
    raise ValueError("時段參數唔啱,用 7d / 12h / 兩個日期")


def split_window(parts):
    """由 parts 抽出時段 token,剩低當群名關鍵字。return (window_tokens, rest)"""
    if not parts:
        raise ValueError("缺時段,例:/digest @user 7d")
    if re.fullmatch(r"\d+[dh]", parts[0]):
        return parts[:1], parts[1:]
    if (len(parts) >= 2 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[0])
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[1])):
        return parts[:2], parts[2:]
    raise ValueError(f"睇唔明時段 `{parts[0]}`,用 7d / 12h / 或兩個日期")


# ---- Claude 整理 ----
PROMPT = """你係一個 TG 群消息整理助手。以下係 {who} 喺群「{chat}」嘅發言,時段:{label}。
總共 {n} 條消息,由舊到新排好。

請用書面繁體中文整理。

【輸出格式】呢份嘢會喺 Telegram 純文字顯示,所以絕對唔好用 Markdown(唔好用 #、星號、反引號、| 表格 |、---)。改用以下純文字排版,務求喺手機 TG 睇得清楚:

━━━━━━━━━━
① 重點摘要
━━━━━━━━━━

• 第一個重點

• 第二個重點

(每個重點用「• 」開頭,每點之間空一行,簡潔有力)

━━━━━━━━━━
② 立場 / 觀點
━━━━━━━━━━

(每個議題一行,用 emoji + 議題 +「:」+ 立場,例如)
📉 ETH:明確看淡,HTF bias 不變
🛢️ 石油:看多,入場點優質

(如有前後態度轉變或矛盾,另起一段)
⚠️ 態度轉變
• 一兩句描述,可引時間

━━━━━━━━━━
③ Action / 待辦
━━━━━━━━━━

(只抽交易/投資/加密/美股相關嘅 action。每個標的一小段,唔好用表格,例如)
• ETH(做空)
  狀況:14:47 SL 已 hit 出場
  計劃:HTF 仍看淡,等下次

(生活瑣事唔好寫;冇 action 就寫「無」)

直接由「① 重點摘要」上面嗰條分隔線開始,唔好加大標題、開場白或結尾。

【關於圖片】消息標住 [圖片#N] 嘅對應後面第 N 張圖。圖只係幫你理解佢喺講緊咩(例如佢 send ETH 圖配文字睇空,你就知講緊 ETH)。唔好獨立列出對圖嘅技術分析(例如「圖#3 顯示 1750 壓力、Bear Flag」呢種脫離圖嘅 TA 段落)— 報告冇咗張圖,呢啲好難睇。只將圖反映嘅嘢自然融入佢嘅發言重點;如果佢淨係 send 圖冇講嘢,簡短帶過(例如「佢發咗張 ETH 4H 圖」)即可。無關圖(meme、自拍)忽略。

只整理實際存在嘅內容,唔好虛構或腦補。某節真係冇料就寫「無」。

===
消息原文:
{body}
"""


async def build_report(who, chat, label, messages):
    lines = []
    images = []  # 下載到嘅 photo bytes,順序對應 [圖片#N]
    for m in messages:
        ts = m.date.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
        text = (m.message or "").strip()
        tag = ""
        if m.photo:
            if len(images) < MAX_IMAGES:
                try:
                    data = await client.download_media(m, file=bytes)
                    if data and len(data) < 4_000_000:
                        images.append(data)
                        tag = f" [圖片#{len(images)}]"
                    else:
                        tag = " [圖片(太大跳過)]"
                except Exception:
                    tag = " [圖片(下載失敗)]"
            else:
                tag = " [圖片(超出讀圖上限)]"
        elif m.media:
            tag = f" [{type(m.media).__name__}]"
        if not text and not tag:
            text = "[非文字]"
        lines.append(f"[{ts}] {text}{tag}")
    body = "\n".join(lines)

    prompt = PROMPT.format(
        who=who, chat=chat, label=label, n=len(messages), body=body
    )
    content = [{"type": "text", "text": prompt}]
    for data in images:
        b64 = base64.standard_b64encode(data).decode()
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
        })
    resp = ant.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": content}],
    )
    return resp.content[0].text


# ---- digest 核心(handler 同排程共用)----
async def resolve_group(keyword):
    """模糊 match dialog title,跳過已遷移/停用嘅舊空殼。return matches list。"""
    matches = []
    async for d in client.iter_dialogs():
        if not (d.is_group or d.is_channel):
            continue
        ent = d.entity
        if getattr(ent, "migrated_to", None) is not None:
            continue
        if getattr(ent, "deactivated", False):
            continue
        if keyword.lower() in (d.title or "").lower():
            matches.append(d)
    return matches


async def resolve_invite_channel(invite_hash):
    """由 invite hash(t.me/+xxx 個 xxx)resolve 返已加入嘅 private channel/group entity。"""
    from telethon.tl.functions.messages import CheckChatInviteRequest
    from telethon.tl.types import ChatInviteAlready
    res = await client(CheckChatInviteRequest(invite_hash))
    if isinstance(res, ChatInviteAlready):
        return res.chat
    return None  # 未加入嗰個 channel


async def do_digest(target_handle, target, target_chat_id, chat_title,
                    start, end, label, progress=None, forward_to=None):
    """抓消息 → 整理 → 存檔 → 發 Saved Messages(+ 可選轉發 channel)。progress = optional async callback(msg)。"""
    async def say(msg):
        if progress:
            await progress(msg)

    await say(f"⏳ 抓緊 {target_handle}（{chat_title}）嘅消息…")
    messages = []
    truncated = False
    async for m in client.iter_messages(target_chat_id, from_user=target):
        if m.date > end:
            continue
        if m.date < start:
            break
        messages.append(m)
        if len(messages) >= MAX_MESSAGES:
            truncated = True
            break

    if not messages:
        await say(f"🔍 {target_handle} 喺呢段時間({label})冇發言。")
        return False, "no_messages"

    messages.reverse()
    await say(f"🧠 整理緊 {len(messages)} 條消息…")
    report_body = await build_report(target_handle, chat_title, label, messages)

    warn = ""
    if truncated:
        warn = (
            f"\n\n⚠️ **注意:消息數已達上限 {MAX_MESSAGES},只整理咗最新嗰批,"
            f"較舊嘅消息未包含。** 收窄時段再跑一次。"
        )

    header = f"{target_handle} 【{label}】\n\n"
    full = header + report_body + warn

    safe = re.sub(r"[^\w]+", "_", target_handle.lstrip("@"))
    fname = REPORTS_DIR / f"{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}.md"
    fname.write_text(full, encoding="utf-8")

    chunks = [full[i:i + 4000] for i in range(0, len(full), 4000)]
    for c in chunks:
        await client.send_message("me", c)

    # 自動轉發去 group 嘅 forum topic(forward_to = (invite_hash, topic 關鍵字))
    fwd_info = ""
    if forward_to:
        try:
            inv_hash, topic_kw = forward_to
            group = await resolve_invite_channel(inv_hash)
            if not group:
                fwd_info = ";⚠️ 轉發失敗(未加入該 group)"
            else:
                from telethon.tl.functions.messages import GetForumTopicsRequest
                res = await client(GetForumTopicsRequest(
                    peer=group, offset_date=None, offset_id=0, offset_topic=0, limit=100))
                norm = topic_kw.lower().replace(" ", "")
                topic_id = None
                tlist = []
                for t in res.topics:
                    ti = getattr(t, "title", "") or ""
                    tlist.append((t.id, ti))
                    if norm in ti.lower().replace(" ", ""):
                        topic_id = t.id
                print(f"⏰ forum topics={tlist} → matched={topic_id}", flush=True)
                for c in chunks:
                    if topic_id:
                        await client.send_message(group, c, reply_to=topic_id)
                    else:
                        await client.send_message(group, c)
                fwd_info = (f";已轉發去 alphacall(topic {topic_id})" if topic_id
                            else ";⚠️ 揾唔到 alphacall topic,暫發咗去主分區")
        except Exception as e:
            import traceback
            fwd_info = f";⚠️ 轉發失敗:{type(e).__name__}: {e}"
            print(f"⏰ forward 出錯:\n{traceback.format_exc()}", flush=True)
        print(f"⏰ forward → {fwd_info or '(forward_to 為空)'}", flush=True)

    await say(f"✅ 完成。已發去 Saved Messages,存檔:{fname.name}{fwd_info}")
    return True, fname.name


# ---- 主 handler ----
@client.on(events.NewMessage(outgoing=True, pattern=r"^/digest(\s|$)"))
async def handler(event):
    raw = event.raw_text.strip()
    parts = raw.split()[1:]  # 去掉 /digest

    # 喺 Saved Messages(俾自己)打 = 隱形模式,需要喺尾指定群名關鍵字
    me = await client.get_me()
    is_saved = event.chat_id == me.id

    try:
        # 解析 target(@username 或 reply)
        target = None
        if parts and parts[0].startswith("@"):
            target_handle = parts[0]
            parts = parts[1:]
            target = await client.get_entity(target_handle)
        elif event.is_reply and not is_saved:
            replied = await event.get_reply_message()
            target = await replied.get_sender()
            target_handle = f"@{getattr(target, 'username', None) or target.id}"
        else:
            await event.reply(
                "⚠️ 要 `/digest @username 7d`"
                + ("(Saved Messages 模式必須用 @username)" if is_saved
                   else ",或先 reply 一條消息再 `/digest 7d`")
            )
            return

        # 分離時段 + 群名關鍵字
        window_tokens, rest = split_window(parts)
        start, end, label = parse_window(window_tokens)

        # 決定 digest 邊個群
        if is_saved:
            # 支援 #N 揀第幾個 match(應付同名群)
            pick = None
            kw_tokens = []
            for t in rest:
                mm = re.fullmatch(r"#(\d+)", t)
                if mm:
                    pick = int(mm.group(1))
                else:
                    kw_tokens.append(t)
            keyword = " ".join(kw_tokens).strip()
            if not keyword:
                await event.reply(
                    "⚠️ Saved Messages 模式要喺尾指定群名關鍵字,例:`/digest @user 3h 雞腿`"
                )
                return
            matches = await resolve_group(keyword)
            if not matches:
                await event.reply(f"⚠️ 揾唔到名含「{keyword}」嘅群")
                return
            if len(matches) > 1 and not pick:
                lines_ = []
                for i, d in enumerate(matches[:10], 1):
                    kind = "頻道" if (d.is_channel and not d.is_group) else "群"
                    members = getattr(getattr(d, "entity", None), "participants_count", None)
                    extra = f" · {members} 人" if members else ""
                    lines_.append(f"{i}. {d.title}（{kind} · id…{str(d.id)[-5:]}{extra}）")
                await event.reply(
                    "⚠️ match 到多過一個,加 `#編號` 揀(例:`/digest @user 1d 雞腿 #2`):\n"
                    + "\n".join(lines_)
                )
                return
            if pick is not None:
                if not (1 <= pick <= len(matches)):
                    await event.reply(f"⚠️ #編號 超出範圍(得 {len(matches)} 個 match)")
                    return
                chosen = matches[pick - 1]
            else:
                chosen = matches[0]
            target_chat_id = chosen.id
            chat_title = chosen.title
        else:
            chat = await event.get_chat()
            target_chat_id = event.chat_id
            chat_title = getattr(chat, "title", str(event.chat_id))

    except ValueError as e:
        await event.reply(f"⚠️ {e}")
        return
    except Exception as e:
        await event.reply(f"⚠️ 搞唔掂:{e}")
        return

    # 執行 digest,進度即時 edit 返條 command 消息
    async def progress(msg):
        await event.edit(f"{raw}\n{msg}")

    try:
        await do_digest(target_handle, target, target_chat_id, chat_title,
                        start, end, label, progress=progress)
    except Exception as e:
        await event.edit(f"{raw}\n❌ 出錯:{e}")


# ---- 每日自動 digest 排程 ----
# 排程設定放喺 config.py(已 gitignore;複製 config.example.py 嚟改)。格式同說明見該檔。
try:
    from config import SCHEDULED_JOBS
except ImportError:
    SCHEDULED_JOBS = []


async def run_scheduled_job(target_handle, window, keyword, forward_to=None):
    """排程直接執行 digest(唔經 handler — self-send 唔會觸發自己 handler)。"""
    target = await client.get_entity(target_handle)
    window_tokens, _ = split_window(window.split())
    start, end, label = parse_window(window_tokens)
    matches = await resolve_group(keyword)
    if not matches:
        print(f"⏰ 排程:揾唔到名含「{keyword}」嘅群", flush=True)
        return
    ok, info = await do_digest(target_handle, target, matches[0].id, matches[0].title,
                               start, end, label, progress=None, forward_to=forward_to)
    print(f"⏰ 排程完成 {target_handle}({keyword}): ok={ok} {info}", flush=True)


async def scheduler_loop():
    """每 30 秒 check,命中 HKT 時間就 send 指令落 Saved Messages。"""
    last_run = {}  # job index -> 已跑嘅 HKT 日期(防同分鐘重複)
    while True:
        await asyncio.sleep(30)
        now_hkt = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=8)
        today = now_hkt.date()
        for idx, job in enumerate(SCHEDULED_JOBS):
            h, mi, tgt, win, kw = job[0], job[1], job[2], job[3], job[4]
            fwd = job[5] if len(job) > 5 else None
            if now_hkt.hour == h and now_hkt.minute == mi and last_run.get(idx) != today:
                last_run[idx] = today
                print(f"⏰ 排程觸發({now_hkt:%Y-%m-%d %H:%M} HKT): {tgt} {win} {kw}", flush=True)
                try:
                    await run_scheduled_job(tgt, win, kw, fwd)
                except Exception as e:
                    print(f"⏰ 排程失敗: {e}", flush=True)


async def amain():
    sched_started = False
    while True:
        try:
            await client.start()
            print("✅ 已登入,監聽中。喺任何群打 `/digest @user 7d` 即可。", flush=True)
            if SCHEDULED_JOBS and not sched_started:
                asyncio.create_task(scheduler_loop())
                sched_started = True
                desc = ", ".join(f"{j[0]:02d}:{j[1]:02d} HKT {j[2]} {j[3]} {j[4]}" for j in SCHEDULED_JOBS)
                print(f"⏰ 已啟動每日排程: {desc}", flush=True)
            await client.run_until_disconnected()
            break  # 正常 disconnect 先退出
        except Exception as e:
            # 遇到未知 update 類型 / 連線中斷,自動重連,唔好 kill 成個 bot
            print(f"⚠️ 連線中斷({type(e).__name__}: {e}),5 秒後重連", flush=True)
            try:
                await client.disconnect()
            except Exception:
                pass
            await asyncio.sleep(5)


def main():
    print("TG Digest Bot 啟動中… 第一次要輸入電話 + 驗證碼", flush=True)
    asyncio.run(amain())


if __name__ == "__main__":
    main()
