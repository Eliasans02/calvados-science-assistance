"""Agent endpoint handler for scoring."""

from __future__ import annotations

from src.data.repository import BackendRepository
from src.modules.scoring import score_tz


class ScoringAgent:
    name = "scoring"

    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def run(self, user_id: str, payload: dict) -> dict:
        result = score_tz(payload)
        self._repository.save_agent_result(
            user_id=user_id,
            file_id=payload.get("file_id"),
            agent_name=self.name,
            input_payload=payload,
            output_payload=result,
        )
        return result
