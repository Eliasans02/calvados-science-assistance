"""Agent endpoint handler for TZ structure building."""

from __future__ import annotations

from src.agents.common import resolve_text
from src.data.repository import BackendRepository
from src.modules.structure_builder import build_structure


class StructureAgent:
    name = "structure"

    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def run(self, user_id: str, payload: dict) -> dict:
        text, file_id = resolve_text(self._repository, user_id=user_id, payload=payload)
        result = build_structure(text)
        self._repository.save_agent_result(
            user_id=user_id,
            file_id=file_id,
            agent_name=self.name,
            input_payload=payload,
            output_payload=result,
        )
        return result
