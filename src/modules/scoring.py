"""Scoring module (stub contract for future advanced scoring)."""

from __future__ import annotations

from typing import Any


def score_tz(payload: dict[str, Any]) -> dict[str, Any]:
    issue_count = int(payload.get("issue_count", 0))
    missing_sections = int(payload.get("missing_sections", 0))
    base = 85
    score = max(0, base - issue_count * 3 - missing_sections * 5)
    return {
        "agent": "scoring_agent",
        "score": score,
        "max_score": 100,
        "status": "stub",
        "explanation": "Временная формула. Будет заменена на ML/экспертную модель scoring.",
    }
