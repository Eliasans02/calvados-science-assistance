"""Detection of missing requirements and KPI blocks."""

from __future__ import annotations

import re
from typing import Any


REQUIRED_SECTIONS = {
    "1.1_priority": r"(1\.1|приоритет)",
    "1.2_specialization": r"(1\.2|специализированн\w+\s+направлен)",
    "2.1_goal": r"(2\.1|цель\s+программы)",
    "2.2_tasks": r"(2\.2|задач\w+\s+программ)",
    "3_strategy_docs": r"(3\.|стратегическ\w+|программн\w+\s+документ\w+)",
    "4.1_direct_results": r"(4\.1|прям\w+\s+результат)",
    "4.2_final_result": r"(4\.2|конечн\w+\s+результат)",
    "5_budget": r"(5\.|предельн\w+\s+сумм\w+|тенге)",
}


def analyze_requirements(text: str) -> dict[str, Any]:
    normalized = text.lower()
    missing_sections: list[str] = []

    for section_name, pattern in REQUIRED_SECTIONS.items():
        if not re.search(pattern, normalized, flags=re.IGNORECASE):
            missing_sections.append(section_name)

    has_kpi = bool(
        re.search(r"\bkpi\b", normalized)
        or re.search(r"не\s+менее\s+\d+", normalized)
        or re.search(r"\d+\s*%", normalized)
        or re.search(r"количественн\w+\s+показател", normalized)
    )

    missing_kpi = not has_kpi
    issues: list[dict[str, str]] = []
    for section in missing_sections:
        issues.append(
            {
                "type": "missing_requirement",
                "item": section,
                "severity": "High",
                "recommendation": f"Добавить обязательный раздел: {section}",
            }
        )
    if missing_kpi:
        issues.append(
            {
                "type": "missing_kpi",
                "item": "kpi",
                "severity": "High",
                "recommendation": "Добавить измеримые KPI и ожидаемые количественные результаты",
            }
        )

    return {
        "agent": "requirement_analysis_agent",
        "missing_sections": missing_sections,
        "missing_kpi": missing_kpi,
        "issues": issues,
        "summary": {
            "required_sections_total": len(REQUIRED_SECTIONS),
            "missing_sections_count": len(missing_sections),
            "has_kpi": has_kpi,
            "total_issues": len(issues),
        },
    }
