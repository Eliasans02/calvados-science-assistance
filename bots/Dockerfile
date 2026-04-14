FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY telegram_bot.py /app/telegram_bot.py
COPY .env.example /app/.env.example

CMD ["python", "/app/telegram_bot.py"]
