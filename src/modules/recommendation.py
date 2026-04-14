"""Recommendation service with ML-ready integration contract."""

from __future__ import annotations

from typing import Any


def build_recommendations(payload: dict[str, Any]) -> dict[str, Any]:
    issues = payload.get("issues", [])
    recommendations: list[dict[str, Any]] = []

    for issue in issues:
        issue_type = issue.get("type", "unknown")
        severity = issue.get("severity", "Medium")
        if issue_type == "missing_requirement":
            recommendations.append(
                {
                    "priority": "High",
                    "category": "structure",
                    "text": f"Добавьте обязательный раздел: {issue.get('item', '')}",
                    "source": "rule-based",
                }
            )
        elif issue_type == "missing_kpi":
            recommendations.append(
                {
                    "priority": "High",
                    "category": "kpi",
                    "text": "Определите минимум 3 измеримых KPI с базовым и целевым значением",
                    "source": "rule-based",
                }
            )
        elif issue_type == "vague_formulation":
            recommendations.append(
                {
                    "priority": "Medium",
                    "category": "clarity",
                    "text": "Замените расплывчатые формулировки на проверяемые критерии",
                    "source": "rule-based",
                }
            )
        elif issue_type == "duplicate_requirement":
            recommendations.append(
                {
                    "priority": "Low",
                    "category": "consistency",
                    "text": "Уберите дублирующие требования, оставьте единую формулировку",
                    "source": "rule-based",
                }
            )
        else:
            recommendations.append(
                {
                    "priority": severity,
                    "category": "general",
                    "text": issue.get("recommendation", "Проведите дополнительную верификацию раздела"),
                    "source": "rule-based",
                }
            )

    if not recommendations:
        recommendations.append(
            {
                "priority": "Low",
                "category": "general",
                "text": "Критических проблем не найдено. Проведите экспертную финальную проверку",
                "source": "rule-based",
            }
        )

    return {
        "agent": "recommendation_agent",
        "recommendations": recommendations,
        "ml_adapter": {
            "enabled": False,
            "ready_for_training_data": True,
            "expected_input_keys": ["issues", "historical_tz_examples", "domain"],
            "notes": "Подключите ML-модель через data layer без изменения контракта endpoint",
        },
    }
