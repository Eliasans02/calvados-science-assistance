"""SQLite backend storage for users, files, agent outputs and logs."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Iterable, Optional

from src import config


class Database:
    """Thread-safe SQLite helper with schema initialization."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or config.BACKEND_DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def execute(self, query: str, params: Iterable = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._conn.execute(query, tuple(params))
            self._conn.commit()
            return cur

    def executemany(self, query: str, params_seq: Iterable[Iterable]) -> None:
        with self._lock:
            self._conn.executemany(query, params_seq)
            self._conn.commit()

    def fetchone(self, query: str, params: Iterable = ()) -> Optional[sqlite3.Row]:
        with self._lock:
            cur = self._conn.execute(query, tuple(params))
            return cur.fetchone()

    def fetchall(self, query: str, params: Iterable = ()) -> list[sqlite3.Row]:
        with self._lock:
            cur = self._conn.execute(query, tuple(params))
            return cur.fetchall()

    def _init_schema(self) -> None:
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                normalized_text TEXT NOT NULL,
                warning TEXT,
                uploaded_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_results (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                file_id TEXT,
                agent_name TEXT NOT NULL,
                input_json TEXT NOT NULL,
                output_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE SET NULL
            )
            """
        )
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                file_id TEXT NOT NULL,
                report_format TEXT NOT NULL,
                report_path TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
            )
            """
        )
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                file_id TEXT,
                message TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE SET NULL
            )
            """
        )
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS api_logs (
                id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                user_id TEXT,
                status_code INTEGER NOT NULL,
                latency_ms REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


_db_singleton: Optional[Database] = None


def get_db() -> Database:
    global _db_singleton
    if _db_singleton is None:
        _db_singleton = Database()
    return _db_singleton
