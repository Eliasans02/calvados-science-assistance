"""Asynchronous statistics tracking with JSON persistence."""

from __future__ import annotations

import json
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    import config
except ModuleNotFoundError:  # pragma: no cover - test/import context fallback
    from src import config


@dataclass
class StatsEvent:
    """Event payload for tracking document processing."""

    document_type: str
    source: str
    ai_result: str  # success | failed | skipped
    document_title: str = ""
    issues_found: int = 0
    analysis_status: str = "success"  # success | failed
    error_message: str = ""


class StatsService:
    """Thread-safe, async stats accumulator with on-disk persistence."""

    VALID_AI_RESULTS = {"success", "failed", "skipped"}
    VALID_ANALYSIS_STATUS = {"success", "failed"}
    MAX_HISTORY_ITEMS = 200

    def __init__(self, stats_path: Optional[Path] = None):
        self._stats_path = stats_path or (config.PROCESSED_DATA_DIR / "stats.json")
        self._queue: "queue.Queue[StatsEvent]" = queue.Queue()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._run_worker, daemon=True)
        self._stats = self._load_stats()
        self._worker.start()

    def track_document(self, event: StatsEvent) -> None:
        """Queue event for asynchronous processing."""
        self._queue.put(event)

    def get_stats(self) -> Dict:
        """Return current stats snapshot."""
        with self._lock:
            return json.loads(json.dumps(self._stats))

    def flush(self, timeout: float = 2.0) -> None:
        """Wait until pending events are processed and persisted."""
        self._queue.join()
        self._persist()

    def stop(self) -> None:
        """Stop worker thread (useful for tests)."""
        self._stop_event.set()
        self._worker.join(timeout=1)
        self._persist()

    def _run_worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                event = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self._apply_event(event)
                self._persist()
            except Exception:
                # Keep worker alive even if one malformed/legacy payload fails.
                pass
            finally:
                self._queue.task_done()

    def _apply_event(self, event: StatsEvent) -> None:
        doc_type = (event.document_type or "unknown").strip().lower()
        source = (event.source or "unknown").strip().lower()
        ai_result = (event.ai_result or "skipped").strip().lower()
        analysis_status = (event.analysis_status or "success").strip().lower()
        if ai_result not in self.VALID_AI_RESULTS:
            ai_result = "skipped"
        if analysis_status not in self.VALID_ANALYSIS_STATUS:
            analysis_status = "success"

        with self._lock:
            self._ensure_schema_locked()
            self._stats["total_processed_documents"] += 1
            self._stats["document_types"][doc_type] = self._stats["document_types"].get(doc_type, 0) + 1
            self._stats["document_sources"][source] = self._stats["document_sources"].get(source, 0) + 1
            self._stats["ai_results"][ai_result] = self._stats["ai_results"].get(ai_result, 0) + 1
            self._stats["analysis_results"][analysis_status] = self._stats["analysis_results"].get(analysis_status, 0) + 1
            self._stats["recent_analyses"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "title": (event.document_title or "Без названия").strip() or "Без названия",
                    "document_type": doc_type,
                    "source": source,
                    "issues_found": max(0, int(event.issues_found or 0)),
                    "ai_result": ai_result,
                    "status": analysis_status,
                    "error": (event.error_message or "").strip(),
                }
            )
            if len(self._stats["recent_analyses"]) > self.MAX_HISTORY_ITEMS:
                self._stats["recent_analyses"] = self._stats["recent_analyses"][-self.MAX_HISTORY_ITEMS :]
            self._stats["updated_at"] = datetime.utcnow().isoformat()

    def _load_stats(self) -> Dict:
        stats: Dict
        if self._stats_path.exists():
            try:
                stats = json.loads(self._stats_path.read_text(encoding="utf-8"))
                return self._with_defaults(stats)
            except Exception:
                pass
        return self._with_defaults({
            "total_processed_documents": 0,
            "document_types": {},
            "document_sources": {},
            "ai_results": {"success": 0, "failed": 0, "skipped": 0},
            "analysis_results": {"success": 0, "failed": 0},
            "recent_analyses": [],
            "updated_at": datetime.utcnow().isoformat(),
        })

    def _with_defaults(self, stats: Dict) -> Dict:
        """Backfill missing keys for older persisted stats schema."""
        if not isinstance(stats, dict):
            stats = {}
        stats.setdefault("total_processed_documents", 0)
        stats.setdefault("document_types", {})
        stats.setdefault("document_sources", {})
        stats.setdefault("ai_results", {})
        stats.setdefault("analysis_results", {})
        stats.setdefault("recent_analyses", [])
        stats.setdefault("updated_at", datetime.utcnow().isoformat())

        for key in ("success", "failed", "skipped"):
            stats["ai_results"].setdefault(key, 0)
        for key in ("success", "failed"):
            stats["analysis_results"].setdefault(key, 0)
        if not isinstance(stats["recent_analyses"], list):
            stats["recent_analyses"] = []
        return stats

    def _ensure_schema_locked(self) -> None:
        """Ensure in-memory schema is complete. Call only under lock."""
        self._stats = self._with_defaults(self._stats)

    def _persist(self) -> None:
        self._stats_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            payload = json.dumps(self._stats, ensure_ascii=False, indent=2)
        self._stats_path.write_text(payload, encoding="utf-8")


_stats_service_singleton: Optional[StatsService] = None


def get_stats_service() -> StatsService:
    """Get process-wide stats service singleton."""
    global _stats_service_singleton
    if _stats_service_singleton is None:
        _stats_service_singleton = StatsService()
    return _stats_service_singleton
