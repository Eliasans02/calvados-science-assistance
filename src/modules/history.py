"""History retrieval service."""

from __future__ import annotations

from src.data.repository import BackendRepository


class HistoryService:
    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def list_documents(self, user_id: str) -> dict:
        files = self._repository.list_files(user_id=user_id)
        return {"items": files, "total": len(files)}

    def get_document_details(self, user_id: str, file_id: str) -> dict:
        file_record = self._repository.get_file(file_id=file_id, user_id=user_id)
        if not file_record:
            raise ValueError("Document not found")
        results = self._repository.list_agent_results(user_id=user_id, file_id=file_id)
        report = self._repository.get_latest_report(user_id=user_id, file_id=file_id)
        return {
            "file": file_record,
            "agent_results": results,
            "latest_report": report,
        }
