#!/usr/bin/env python3
"""Telegram bot for Calvados AI platform.

Features:
- backend health check
- upload -> analysis -> report flow
- progress updates
- n8n webhook mode (or direct backend mode)
- polling or webhook runtime mode
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Callable, Optional

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOGGER = logging.getLogger("calvados-telegram-bot")


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()
USE_N8N = os.getenv("USE_N8N", "false").strip().lower() == "true"
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").strip().lower() == "true"
BOT_WEBHOOK_URL = os.getenv("BOT_WEBHOOK_URL", "").strip()
BOT_WEBHOOK_PORT = int(os.getenv("BOT_WEBHOOK_PORT", "8080"))
BOT_WEBHOOK_PATH = os.getenv("BOT_WEBHOOK_PATH", TELEGRAM_BOT_TOKEN).strip() or TELEGRAM_BOT_TOKEN


@dataclass
class BackendClient:
    base_url: str
    timeout_sec: int = 120

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            resp = await client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            return resp.json()

    async def upload(self, user_id: str, filename: str, content: bytes, content_type: str) -> dict[str, Any]:
        files = {"file": (filename, content, content_type)}
        data = {"user_id": user_id}
        last_exc: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                    resp = await client.post(f"{self.base_url}/api/upload", data=data, files=files)
                if resp.status_code >= 500 and attempt < 3:
                    await asyncio.sleep(1)
                    continue
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_exc = exc
                if attempt < 3:
                    await asyncio.sleep(1)
                    continue
                raise
        if last_exc:
            raise last_exc
        raise RuntimeError("Upload failed")

    async def call_agent(self, agent_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            resp = await client.post(f"{self.base_url}/agent/{agent_name}", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def download_report_json(self, file_id: str, user_id: str) -> bytes:
        params = {"format": "json", "user_id": user_id}
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            resp = await client.get(f"{self.base_url}/api/report/{file_id}/download", params=params)
            resp.raise_for_status()
            return resp.content

    async def trigger_n8n(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not N8N_WEBHOOK_URL:
            raise ValueError("N8N_WEBHOOK_URL is empty while USE_N8N=true")
        last_exc: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                    resp = await client.post(N8N_WEBHOOK_URL, json=payload)
                if resp.status_code == 404:
                    try:
                        error_payload = resp.json()
                        message = str(error_payload.get("message", "")).strip()
                        hint = str(error_payload.get("hint", "")).strip()
                        details = " ".join(part for part in [message, hint] if part).strip()
                    except ValueError:
                        details = (resp.text or "").strip()
                    if "/webhook-test/" in N8N_WEBHOOK_URL:
                        raise RuntimeError(f"n8n-test-webhook-not-registered: {details}")
                    raise RuntimeError(f"n8n-prod-webhook-not-registered: {details}")
                if resp.status_code >= 500 and attempt < 3:
                    await asyncio.sleep(1)
                    continue
                resp.raise_for_status()
                raw_text = (resp.text or "").strip()
                if not raw_text:
                    return {
                        "status": "ok",
                        "warning": "n8n-empty-response",
                        "hint": "Configure n8n Webhook to respond via 'Respond to Webhook' node with a JSON body.",
                    }
                if "application/json" in (resp.headers.get("content-type") or "").lower():
                    try:
                        return resp.json()
                    except ValueError:
                        return {"status": "ok", "raw": raw_text}
                return {"status": "ok", "raw": raw_text}
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                status = exc.response.status_code if exc.response is not None else 0
                if 400 <= status < 500:
                    raise
                if attempt < 3:
                    await asyncio.sleep(1)
                    continue
                raise
            except RuntimeError as exc:
                if str(exc).startswith("n8n-"):
                    raise
                last_exc = exc
                if attempt < 3:
                    await asyncio.sleep(1)
                    continue
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < 3:
                    await asyncio.sleep(1)
                    continue
                raise
        if last_exc:
            raise last_exc
        raise RuntimeError("n8n webhook call failed")


BACKEND = BackendClient(base_url=API_BASE_URL)


def _friendly_error_message(exc: Exception) -> str:
    text = str(exc)
    if "n8n-prod-webhook-not-registered" in text:
        return "n8n production webhook не зарегистрирован. Включите workflow (Active) в n8n и повторите."
    if "n8n-test-webhook-not-registered" in text:
        return "n8n test webhook не зарегистрирован. Нажмите Execute workflow / Listen for test event в n8n и отправьте файл снова."
    if "503" in text:
        return "Сервис временно недоступен (503). Проверьте, что backend и ngrok работают, и повторите попытку."
    if "401" in text:
        return "Авторизация не пройдена на backend. Проверьте API настройки."
    if "404" in text:
        return "Нужный endpoint не найден. Проверьте URL backend/n8n."
    if "timeout" in text.lower():
        return "Запрос превысил лимит времени. Попробуйте снова."
    if "Connection refused" in text or "All connection attempts failed" in text:
        return "Backend недоступен. Убедитесь, что API запущен на localhost:8000."
    return "Произошла ошибка при обработке. Попробуйте еще раз позже."


async def _update_progress(
    message,
    done: int,
    total: int,
    step_name: str,
) -> None:
    await message.edit_text(f"Processing... {done}/{total} agents complete\nCurrent step: {step_name}")


async def _run_direct_pipeline(
    user_id: str,
    file_id: str,
    progress_cb: Callable[[int, int, str], Any],
) -> dict[str, Any]:
    steps = [
        "text-analysis",
        "requirement-analysis",
        "structure",
        "compliance",
        "scoring",
        "recommendation",
        "generation",
        "report",
    ]
    last_result: dict[str, Any] = {}
    total = len(steps)
    for idx, agent in enumerate(steps, start=1):
        payload: dict[str, Any] = {"file_id": file_id, "user_id": user_id}
        if agent == "generation":
            payload.update({"project_title": "TZ draft from Telegram bot"})
        last_result = await BACKEND.call_agent(agent, payload)
        await progress_cb(idx, total, agent)
    return last_result


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Привет! Я Calvados AI Bot.\n\n"
        "Отправьте мне PDF/DOCX/TXT файл, и я запущу анализ ТЗ.\n\n"
        "Команды:\n"
        "/health - проверить backend\n"
        "/mode - показать режим работы (n8n/direct, webhook/polling)"
    )
    await update.message.reply_text(text)


async def cmd_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"USE_N8N={USE_N8N}\nUSE_WEBHOOK={USE_WEBHOOK}\nAPI_BASE_URL={API_BASE_URL}\nN8N_WEBHOOK_URL={N8N_WEBHOOK_URL or '-'}"
    )


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        backend = await BACKEND.health()
        await update.message.reply_text(
            "✅ Backend is healthy\n"
            f"Status: {backend.get('status')}\n"
            f"Agents: {', '.join(backend.get('agents', []))}"
        )
    except Exception as exc:  # explicit user-facing message
        LOGGER.exception("Health check failed")
        await update.message.reply_text(f"❌ {_friendly_error_message(exc)}")


async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    chat_id = update.effective_chat.id
    user_id = str(chat_id)

    if not message or not message.document:
        return

    doc = message.document
    filename = doc.file_name or "document.bin"
    content_type = doc.mime_type or "application/octet-stream"

    progress_message = await message.reply_text("Processing... 0/8 agents complete\nCurrent step: upload")
    try:
        tg_file = await context.bot.get_file(doc.file_id)
        with tempfile.NamedTemporaryFile(delete=True) as temp:
            await tg_file.download_to_drive(custom_path=temp.name)
            with open(temp.name, "rb") as fh:
                data = fh.read()

        upload_result = await BACKEND.upload(
            user_id=user_id,
            filename=filename,
            content=data,
            content_type=content_type,
        )
        file_id = upload_result["file_id"]
        await progress_message.edit_text("Processing... upload complete\nCurrent step: orchestration")

        if USE_N8N:
            n8n_payload = {
                "file_id": file_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "filename": filename,
                "mode": "telegram",
            }
            result = await BACKEND.trigger_n8n(n8n_payload)
            await progress_message.edit_text("✅ n8n workflow started/completed")
            await message.reply_text(
                "Результат n8n:\n```json\n%s\n```" % json.dumps(result, ensure_ascii=False, indent=2),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        async def _cb(done: int, total: int, step_name: str) -> None:
            await _update_progress(progress_message, done, total, step_name)

        final_result = await _run_direct_pipeline(user_id=user_id, file_id=file_id, progress_cb=_cb)
        report_json = await BACKEND.download_report_json(file_id=file_id, user_id=user_id)

        await progress_message.edit_text("✅ Analysis complete")
        await message.reply_text(
            "Итоговый результат:\n```json\n%s\n```"
            % json.dumps(final_result, ensure_ascii=False, indent=2),
            parse_mode=ParseMode.MARKDOWN,
        )
        await message.reply_document(
            document=report_json,
            filename=f"calvados-report-{file_id}.json",
            caption="Итоговый отчёт (JSON)",
        )
    except Exception as exc:
        LOGGER.exception("Document processing failed")
        await progress_message.edit_text(f"❌ {_friendly_error_message(exc)}")


def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(CommandHandler("mode", cmd_mode))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    return app


async def _run_polling(app: Application) -> None:
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    LOGGER.info("Telegram bot running in polling mode")
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


def main() -> None:
    app = build_application()
    if USE_WEBHOOK:
        if not BOT_WEBHOOK_URL:
            raise RuntimeError("BOT_WEBHOOK_URL is required when USE_WEBHOOK=true")
        webhook_url = f"{BOT_WEBHOOK_URL.rstrip('/')}/{BOT_WEBHOOK_PATH}"
        LOGGER.info("Starting bot in webhook mode: %s", webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=BOT_WEBHOOK_PORT,
            webhook_url=webhook_url,
            url_path=BOT_WEBHOOK_PATH,
            drop_pending_updates=True,
        )
    else:
        LOGGER.info("Starting bot in polling mode")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
