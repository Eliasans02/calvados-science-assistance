"""Grant and R&D compliance checks."""

from __future__ import annotations

import re
from typing import Any


COMPLIANCE_RULES = {
    "strategic_points": r"(стратегическ\w+.*пункт|программн\w+.*пункт)",
    "budget_by_year": r"(на\s+20\d{2}\s*г\.)",
    "publication_targets": r"(не\s+менее\s+\d+.*(стат|публикац))",
    "patent_targets": r"(патент|заявк\w+\s+на\s+патент)",
    "consumers": r"(целев\w+\s+потребител)",
}


def check_compliance(text: str) -> dict[str, Any]:
    normalized = text.lower()
    missing_items: list[str] = []
    passed_items: list[str] = []
    for key, pattern in COMPLIANCE_RULES.items():
        if re.search(pattern, normalized):
            passed_items.append(key)
        else:
            missing_items.append(key)
    is_compliant = len(missing_items) == 0
    return {
        "agent": "compliance_agent",
        "is_compliant": is_compliant,
        "passed_items": passed_items,
        "missing_items": missing_items,
        "summary": {
            "rules_total": len(COMPLIANCE_RULES),
            "passed": len(passed_items),
            "failed": len(missing_items),
        },
        "recommendation": (
            "Документ соответствует базовым требованиям грантов и НИОКР"
            if is_compliant
            else "Дополните отсутствующие блоки для соответствия грантовым требованиям"
        ),
    }
