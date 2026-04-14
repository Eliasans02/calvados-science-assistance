"""Agent endpoint handler for recommendations."""

from __future__ import annotations

from src.agents.common import collect_agent_outputs
from src.data.repository import BackendRepository
from src.modules.recommendation import build_recommendations


class RecommendationAgent:
    name = "recommendation"

    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def run(self, user_id: str, payload: dict) -> dict:
        prepared_payload = dict(payload)
        file_id = payload.get("file_id")
        file_record = None

        outputs = collect_agent_outputs(self._repository, user_id=user_id, file_id=file_id)
        issues = list(prepared_payload.get("issues") or [])
        if not issues:
            issues = self._collect_issues(outputs)
            prepared_payload["issues"] = issues

        if file_id and not prepared_payload.get("text"):
            file_record = self._repository.get_file(file_id=file_id, user_id=user_id)
            if file_record:
                prepared_payload["text"] = file_record.get("normalized_text") or ""
        elif file_id:
            file_record = self._repository.get_file(file_id=file_id, user_id=user_id)

        prepared_payload.setdefault("context", {})
        prepared_payload["context"]["agent_outputs"] = outputs
        if file_record:
            prepared_payload["context"]["file_warning"] = file_record.get("warning")
            prepared_payload["context"]["text_length"] = len(file_record.get("normalized_text") or "")
            prepared_payload["context"]["filename"] = file_record.get("filename") or ""
        result = build_recommendations(prepared_payload)

        persisted_payload = dict(prepared_payload)
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

    @staticmethod
    def _collect_issues(outputs: dict) -> list[dict]:
        issues: list[dict] = []
        issues.extend((outputs.get("text-analysis") or {}).get("issues") or [])
        issues.extend((outputs.get("requirement-analysis") or {}).get("issues") or [])

        compliance_output = outputs.get("compliance") or {}
        for item in compliance_output.get("missing_items") or []:
            issues.append(
                {
                    "type": "compliance_gap",
                    "item": item,
                    "severity": "High",
                    "recommendation": f"Закрыть комплаенс-пробел: {item}",
                }
            )

        structure_output = outputs.get("structure") or {}
        for section in structure_output.get("sections") or []:
            if section.get("status") == "missing":
                issues.append(
                    {
                        "type": "missing_requirement",
                        "item": section.get("id") or section.get("title"),
                        "severity": "High",
                        "recommendation": f"Добавить раздел структуры: {section.get('title', '')}",
                    }
                )
        return issues
