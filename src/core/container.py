"""Dependency container for API services."""

from __future__ import annotations

from fastapi import Request

from src.agents.registry import AgentRegistry
from src.auth.service import AuthService
from src.data.repository import BackendRepository
from src.modules.file_service import FileService
from src.modules.history import HistoryService
from src.modules.report import ReportService


class ServiceContainer:
    def __init__(self) -> None:
        self.repository = BackendRepository()
        self.auth_service = AuthService(self.repository)
        self.file_service = FileService(self.repository)
        self.history_service = HistoryService(self.repository)
        self.report_service = ReportService(self.repository)
        self.agent_registry = AgentRegistry(self.repository)


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container
