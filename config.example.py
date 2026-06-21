# 複製呢個檔做 config.py,填返你自己嘅排程(config.py 已 gitignore,唔會 commit)。
#   cp config.example.py config.py
#
# 每個 job 格式:
#   (HKT 時, HKT 分, "@目標用戶", "時段", "群名關鍵字", 轉發設定 或 None)
#
#   - 時段:"7d" / "12h" / "1d" 等(數字 + d/h)
#   - 群名關鍵字:你想 digest 嗰個群 title 含嘅字(模糊 match)
#   - 轉發設定:None(唔轉發) 或 ("group_invite_hash", "forum_topic_關鍵字")
#       · invite hash = t.me/+xxxxxx 個「+」後面嗰串
#       · topic 關鍵字 = 目標 forum group 入面個 topic title 含嘅字
#
# 時區用香港時間(UTC+8)。改 digest.py 入面 scheduler_loop 個 +8 可換時區。

SCHEDULED_JOBS = [
    # 例:每日 00:00 整理 @someone 過去 1 日喺「mygroup」嘅發言,出 Saved Messages
    # (0, 0, "@someone", "1d", "mygroup", None),
    #
    # 例:同上,但同時轉發去某 forum group 嘅「alphacall」topic
    # (0, 0, "@someone", "1d", "mygroup", ("AbCdEfGhIjK", "alphacall")),
]
