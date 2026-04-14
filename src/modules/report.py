"""Final report composition and persistence."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Optional

from src import config
from src.data.repository import BackendRepository


class ReportService:
    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def compose(self, user_id: str, file_id: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        file_record = self._repository.get_file(file_id=file_id, user_id=user_id)
        if not file_record:
            raise ValueError("File not found for this user")

        agent_results = self._repository.list_agent_results(user_id=user_id, file_id=file_id)
        payload = {
            "file": {
                "id": file_record["id"],
                "filename": file_record["filename"],
                "uploaded_at": file_record["uploaded_at"],
                "warning": file_record["warning"],
            },
            "agent_results": agent_results,
            "context": context or {},
        }

        markdown_report = self._build_markdown(payload)
        report_id = str(uuid.uuid4())
        md_path = config.REPORTS_DATA_DIR / f"{report_id}.md"
        json_path = config.REPORTS_DATA_DIR / f"{report_id}.json"
        md_path.write_text(markdown_report, encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        self._repository.save_report(
            user_id=user_id,
            file_id=file_id,
            report_format="markdown",
            report_path=str(md_path),
            report_payload=payload,
        )

        return {
            "agent": "report_agent",
            "report_id": report_id,
            "markdown_path": str(md_path),
            "json_path": str(json_path),
            "summary": {
                "agent_steps": len(agent_results),
                "file_id": file_id,
            },
            "report": payload,
        }

    def _build_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Итоговый отчёт анализа ТЗ",
            "",
            f"- **Файл:** {payload['file']['filename']}",
            f"- **File ID:** {payload['file']['id']}",
            f"- **Дата загрузки:** {payload['file']['uploaded_at']}",
            "",
            "## Промежуточные результаты агентов",
        ]
        if not payload["agent_results"]:
            lines.append("- Агентные результаты пока отсутствуют.")
        for result in payload["agent_results"]:
            lines.extend(
                [
                    "",
                    f"### {result['agent_name']}",
                    f"- Время: {result['created_at']}",
                    "```json",
                    json.dumps(result["output_json"], ensure_ascii=False, indent=2),
                    "```",
                ]
            )
        return "\n".join(lines)
