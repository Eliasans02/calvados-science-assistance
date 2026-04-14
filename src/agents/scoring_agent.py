"""Agent endpoint handler for scoring."""

from __future__ import annotations

from src.agents.common import collect_agent_outputs
from src.data.repository import BackendRepository
from src.modules.scoring import score_tz


class ScoringAgent:
    name = "scoring"

    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def run(self, user_id: str, payload: dict) -> dict:
        scoring_payload = dict(payload)
        file_id = payload.get("file_id")

        if file_id and ("issue_count" not in scoring_payload or "missing_sections" not in scoring_payload):
            outputs = collect_agent_outputs(self._repository, user_id=user_id, file_id=file_id)
            text_summary = (outputs.get("text-analysis") or {}).get("summary") or {}
            req_output = outputs.get("requirement-analysis") or {}
            req_summary = req_output.get("summary") or {}
            compliance_output = outputs.get("compliance") or {}

            issue_count = int(text_summary.get("total_issues", 0)) + int(req_summary.get("total_issues", 0))
            issue_count += len(compliance_output.get("missing_items") or [])
            missing_sections = len(req_output.get("missing_sections") or [])

            scoring_payload["issue_count"] = issue_count
            scoring_payload["missing_sections"] = missing_sections

        result = score_tz(scoring_payload)
        self._repository.save_agent_result(
            user_id=user_id,
            file_id=file_id,
            agent_name=self.name,
            input_payload=scoring_payload,
            output_payload=result,
        )
        return result
