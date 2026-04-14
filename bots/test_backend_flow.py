#!/usr/bin/env python3
"""Smoke test backend flow used by Telegram bot."""

from __future__ import annotations

import json
import os

import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
USER_ID = os.getenv("TEST_USER_ID", "bot-test-user")


def main() -> None:
    sample_text = (
        "1. Общие сведения\n"
        "2. Цели и задачи программы\n"
        "Требования должны выполняться по возможности.\n"
        "5. Предельная сумма программы\n"
    )
    files = {"file": ("sample_tz.txt", sample_text.encode("utf-8"), "text/plain")}
    upload = requests.post(f"{API_BASE_URL}/api/upload", data={"user_id": USER_ID}, files=files, timeout=60)
    upload.raise_for_status()
    uploaded = upload.json()
    file_id = uploaded["file_id"]

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
    last = None
    for agent in steps:
        payload = {"file_id": file_id, "user_id": USER_ID}
        if agent == "generation":
            payload["project_title"] = "Smoke test generation"
        resp = requests.post(f"{API_BASE_URL}/agent/{agent}", json=payload, timeout=90)
        resp.raise_for_status()
        last = resp.json()

    report_download = requests.get(
        f"{API_BASE_URL}/api/report/{file_id}/download",
        params={"format": "json", "user_id": USER_ID},
        timeout=90,
    )
    report_download.raise_for_status()

    print(
        json.dumps(
            {
                "upload": uploaded,
                "last_agent": last.get("agent") if isinstance(last, dict) else None,
                "report_status": report_download.status_code,
                "report_size": len(report_download.content),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
