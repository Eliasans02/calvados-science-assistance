# Telegram Bot (Calvados AI)

## Features

- `/health` command checks backend
- document upload: upload -> analyze -> report
- friendly error messages
- inline progress updates (`Processing... X/8 agents complete`)
- n8n mode (`USE_N8N=true`) or direct backend mode
- polling or webhook mode

## Environment

Copy `.env.example` to `.env` and fill:

- `TELEGRAM_BOT_TOKEN`
- `API_BASE_URL` (default `http://localhost:8000`)
- `N8N_WEBHOOK_URL` (required when `USE_N8N=true`)
- `USE_N8N=true|false`
- `USE_WEBHOOK=true|false`
- `BOT_WEBHOOK_URL` (required when `USE_WEBHOOK=true`)

## Local run

```bash
cd bots
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python telegram_bot.py
```

## Docker run

```bash
cd bots
cp .env.example .env
# edit .env
docker compose up --build -d
```

## systemd

Use `deploy/telegram-bot.service` as a template:

```bash
sudo cp deploy/telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-bot
```

## Smoke test (without Telegram)

```bash
API_BASE_URL=http://localhost:8000 python test_backend_flow.py
```
