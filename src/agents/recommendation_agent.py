"""Agent endpoint handler for recommendations."""

from __future__ import annotations

from src.data.repository import BackendRepository
from src.modules.recommendation import build_recommendations


class RecommendationAgent:
    name = "recommendation"

    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def run(self, user_id: str, payload: dict) -> dict:
        result = build_recommendations(payload)
        self._repository.save_agent_result(
            user_id=user_id,
            file_id=payload.get("file_id"),
            agent_name=self.name,
            input_payload=payload,
            output_payload=result,
        )
        return result
