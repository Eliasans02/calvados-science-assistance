"""Agent endpoint handler for automatic TZ generation."""

from __future__ import annotations

import uuid

from src import config
from src.agents.common import resolve_text
from src.data.repository import BackendRepository
from src.modules.generation import generate_tz, render_generated_tz_docx


class GenerationAgent:
    name = "generation"

    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def run(self, user_id: str, payload: dict) -> dict:
        if (payload.get("file_id") or payload.get("text")):
            text, file_id = resolve_text(self._repository, user_id=user_id, payload=payload)
        else:
            text, file_id = "", payload.get("file_id")
        generation_payload = dict(payload)
        generation_payload["text"] = text
        generation_payload["file_id"] = file_id

        result = generate_tz(generation_payload)
        docx_id = str(uuid.uuid4())
        docx_path = config.REPORTS_DATA_DIR / f"{docx_id}.docx"
        render_generated_tz_docx(
            title=result.get("generated_title", "Сгенерированное ТЗ"),
            generated_text=result.get("generated_text", ""),
            output_path=docx_path,
        )
        result["generated_docx_path"] = str(docx_path)
        result["generated_docx_filename"] = docx_path.name
        result["file_id"] = file_id

        persisted_payload = dict(generation_payload)
        persisted_context = dict(persisted_payload.get("context") or {})
        persisted_context.pop("ai_api_key", None)
        persisted_payload["context"] = persisted_context
        self._repository.save_agent_result(
            user_id=user_id,
            file_id=file_id,
            agent_name=self.name,
            input_payload=persisted_payload,
            output_payload=result,
        )
        return result
