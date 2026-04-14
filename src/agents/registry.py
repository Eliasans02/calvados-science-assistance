"""Agent registry for external orchestration clients."""

from __future__ import annotations

from src.agents.compliance_agent import ComplianceAgent
from src.agents.generation_agent import GenerationAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.report_agent import ReportAgent
from src.agents.requirement_analysis_agent import RequirementAnalysisAgent
from src.agents.scoring_agent import ScoringAgent
from src.agents.structure_agent import StructureAgent
from src.agents.text_analysis_agent import TextAnalysisAgent
from src.data.repository import BackendRepository
from src.modules.report import ReportService


class AgentRegistry:
    def __init__(self, repository: BackendRepository) -> None:
        report_service = ReportService(repository)
        self._agents = {
            "text-analysis": TextAnalysisAgent(repository),
            "requirement-analysis": RequirementAnalysisAgent(repository),
            "structure": StructureAgent(repository),
            "generation": GenerationAgent(repository),
            "recommendation": RecommendationAgent(repository),
            "scoring": ScoringAgent(repository),
            "compliance": ComplianceAgent(repository),
            "report": ReportAgent(repository, report_service),
        }

    def execute(self, agent_name: str, user_id: str, payload: dict) -> dict:
        if agent_name not in self._agents:
            raise KeyError(f"Unknown agent: {agent_name}")
        return self._agents[agent_name].run(user_id=user_id, payload=payload)

    def list_agents(self) -> list[str]:
        return sorted(self._agents.keys())
