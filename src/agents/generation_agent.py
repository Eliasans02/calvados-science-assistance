"""Agent endpoint handler for automatic TZ generation."""

from __future__ import annotations

from src.data.repository import BackendRepository
from src.modules.generation import generate_tz


class GenerationAgent:
    name = "generation"

    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def run(self, user_id: str, payload: dict) -> dict:
        result = generate_tz(payload)
        self._repository.save_agent_result(
            user_id=user_id,
            file_id=payload.get("file_id"),
            agent_name=self.name,
            input_payload=payload,
            output_payload=result,
        )
        return result
