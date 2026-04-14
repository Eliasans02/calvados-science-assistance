"""Repository layer for backend persistence."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from src.data.db import Database, get_db


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BackendRepository:
    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db or get_db()

    def create_user(self, email: str, name: str, password_hash: str) -> dict[str, Any]:
        user_id = str(uuid.uuid4())
        created_at = _utc_now_iso()
        self._db.execute(
            """
            INSERT INTO users(id, email, name, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, email.lower(), name, password_hash, created_at),
        )
        return {
            "id": user_id,
            "email": email.lower(),
            "name": name,
            "created_at": created_at,
        }

    def get_user_by_email(self, email: str) -> Optional[dict[str, Any]]:
        row = self._db.fetchone("SELECT * FROM users WHERE email = ?", (email.lower(),))
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        row = self._db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
        return dict(row) if row else None

    def ensure_external_user(self, user_id: str) -> dict[str, Any]:
        existing = self.get_user_by_id(user_id)
        if existing:
            return existing
        created_at = _utc_now_iso()
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", user_id)
        email = f"ext_{safe}@integration.local"
        name = f"External {user_id[:12]}"
        password_hash = "external-no-password"
        self._db.execute(
            """
            INSERT INTO users(id, email, name, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, email.lower(), name, password_hash, created_at),
        )
        return {"id": user_id, "email": email.lower(), "name": name, "created_at": created_at}

    def create_session(self, user_id: str, ttl_hours: int = 24) -> dict[str, str]:
        token = str(uuid.uuid4()) + str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(hours=ttl_hours)
        self._db.execute(
            """
            INSERT INTO sessions(token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, user_id, created_at.isoformat(), expires_at.isoformat()),
        )
        return {"token": token, "expires_at": expires_at.isoformat()}

    def get_session(self, token: str) -> Optional[dict[str, Any]]:
        row = self._db.fetchone("SELECT * FROM sessions WHERE token = ?", (token,))
        if not row:
            return None
        session = dict(row)
        if datetime.fromisoformat(session["expires_at"]) <= datetime.now(timezone.utc):
            self._db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            return None
        return session

    def save_file(
        self,
        user_id: str,
        filename: str,
        content_type: str,
        stored_path: str,
        normalized_text: str,
        warning: Optional[str] = None,
    ) -> dict[str, Any]:
        file_id = str(uuid.uuid4())
        uploaded_at = _utc_now_iso()
        self._db.execute(
            """
            INSERT INTO files(id, user_id, filename, content_type, stored_path, normalized_text, warning, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (file_id, user_id, filename, content_type, stored_path, normalized_text, warning, uploaded_at),
        )
        return {
            "id": file_id,
            "user_id": user_id,
            "filename": filename,
            "content_type": content_type,
            "stored_path": stored_path,
            "uploaded_at": uploaded_at,
            "warning": warning,
        }

    def get_file(self, file_id: str, user_id: Optional[str] = None) -> Optional[dict[str, Any]]:
        if user_id:
            row = self._db.fetchone("SELECT * FROM files WHERE id = ? AND user_id = ?", (file_id, user_id))
        else:
            row = self._db.fetchone("SELECT * FROM files WHERE id = ?", (file_id,))
        return dict(row) if row else None

    def list_files(self, user_id: str) -> list[dict[str, Any]]:
        rows = self._db.fetchall(
            "SELECT id, filename, content_type, warning, uploaded_at FROM files WHERE user_id = ? ORDER BY uploaded_at DESC",
            (user_id,),
        )
        return [dict(row) for row in rows]

    def save_agent_result(
        self,
        user_id: str,
        file_id: Optional[str],
        agent_name: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
    ) -> dict[str, Any]:
        result_id = str(uuid.uuid4())
        created_at = _utc_now_iso()
        self._db.execute(
            """
            INSERT INTO agent_results(id, user_id, file_id, agent_name, input_json, output_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result_id,
                user_id,
                file_id,
                agent_name,
                json.dumps(input_payload, ensure_ascii=False),
                json.dumps(output_payload, ensure_ascii=False),
                created_at,
            ),
        )
        return {"id": result_id, "created_at": created_at}

    def list_agent_results(self, user_id: str, file_id: str) -> list[dict[str, Any]]:
        rows = self._db.fetchall(
            """
            SELECT id, agent_name, input_json, output_json, created_at
            FROM agent_results
            WHERE user_id = ? AND file_id = ?
            ORDER BY created_at ASC
            """,
            (user_id, file_id),
        )
        results: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["input_json"] = json.loads(item["input_json"])
            item["output_json"] = json.loads(item["output_json"])
            results.append(item)
        return results

    def get_latest_agent_result(self, user_id: str, file_id: str, agent_name: str) -> Optional[dict[str, Any]]:
        row = self._db.fetchone(
            """
            SELECT id, agent_name, input_json, output_json, created_at
            FROM agent_results
            WHERE user_id = ? AND file_id = ? AND agent_name = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, file_id, agent_name),
        )
        if not row:
            return None
        item = dict(row)
        item["input_json"] = json.loads(item["input_json"])
        item["output_json"] = json.loads(item["output_json"])
        return item

    def save_report(
        self,
        user_id: str,
        file_id: str,
        report_format: str,
        report_path: str,
        report_payload: dict[str, Any],
    ) -> dict[str, Any]:
        report_id = str(uuid.uuid4())
        created_at = _utc_now_iso()
        self._db.execute(
            """
            INSERT INTO reports(id, user_id, file_id, report_format, report_path, report_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                user_id,
                file_id,
                report_format,
                report_path,
                json.dumps(report_payload, ensure_ascii=False),
                created_at,
            ),
        )
        return {"id": report_id, "created_at": created_at, "report_path": report_path}

    def get_latest_report(self, user_id: str, file_id: str) -> Optional[dict[str, Any]]:
        row = self._db.fetchone(
            """
            SELECT * FROM reports
            WHERE user_id = ? AND file_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, file_id),
        )
        if not row:
            return None
        payload = dict(row)
        payload["report_json"] = json.loads(payload["report_json"])
        return payload

    def save_chat_message(
        self,
        user_id: str,
        file_id: Optional[str],
        message: str,
        agent_name: str,
        response_payload: dict[str, Any],
    ) -> dict[str, Any]:
        message_id = str(uuid.uuid4())
        created_at = _utc_now_iso()
        self._db.execute(
            """
            INSERT INTO chat_messages(id, user_id, file_id, message, agent_name, response_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                user_id,
                file_id,
                message,
                agent_name,
                json.dumps(response_payload, ensure_ascii=False),
                created_at,
            ),
        )
        return {"id": message_id, "created_at": created_at}

    def list_chat_messages(self, user_id: str, file_id: Optional[str], limit: int = 50) -> list[dict[str, Any]]:
        if file_id:
            rows = self._db.fetchall(
                """
                SELECT id, file_id, message, agent_name, response_json, created_at
                FROM chat_messages
                WHERE user_id = ? AND file_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, file_id, limit),
            )
        else:
            rows = self._db.fetchall(
                """
                SELECT id, file_id, message, agent_name, response_json, created_at
                FROM chat_messages
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
        out: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["response_json"] = json.loads(item["response_json"])
            out.append(item)
        return out

    def save_api_log(
        self,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
        user_id: Optional[str] = None,
    ) -> None:
        self._db.execute(
            """
            INSERT INTO api_logs(id, request_id, method, path, user_id, status_code, latency_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                request_id,
                method,
                path,
                user_id,
                status_code,
                latency_ms,
                _utc_now_iso(),
            ),
        )
