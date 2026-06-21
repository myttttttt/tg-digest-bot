FROM python:3.11-slim

WORKDIR /app

# 先裝依賴(cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# code(config*.py: 你嘅 config.py 連 example 一齊 copy;開源用戶只有 example 都唔會 fail)
COPY digest.py config*.py ./
RUN mkdir -p /app/reports

ENV PYTHONUNBUFFERED=1

# userbot worker — 背景 listening,唔 serve http
CMD ["python", "digest.py"]
