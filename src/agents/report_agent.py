"""Agent endpoint handler for final report."""

from __future__ import annotations

from fastapi import HTTPException, status

from src.data.repository import BackendRepository
from src.modules.report import ReportService


class ReportAgent:
    name = "report"

    def __init__(self, repository: BackendRepository, report_service: ReportService) -> None:
        self._repository = repository
        self._report_service = report_service

    def run(self, user_id: str, payload: dict) -> dict:
        file_id = payload.get("file_id")
        if not file_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file_id is required for report generation",
            )
        result = self._report_service.compose(
            user_id=user_id,
            file_id=file_id,
            context=payload.get("context", {}),
        )
        self._repository.save_agent_result(
            user_id=user_id,
            file_id=file_id,
            agent_name=self.name,
            input_payload=payload,
            output_payload=result,
        )
        return result
