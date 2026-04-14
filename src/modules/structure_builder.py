"""Template-aware structure builder for PCF technical specification."""

from __future__ import annotations

import re
from typing import Any


PCF_TEMPLATE = [
    {"id": "1", "title": "Общие сведения"},
    {"id": "1.1", "title": "Наименование приоритета программы"},
    {"id": "1.2", "title": "Наименование специализированного направления"},
    {"id": "2", "title": "Цели и задачи программы"},
    {"id": "2.1", "title": "Цель программы"},
    {"id": "2.2", "title": "Задачи программы"},
    {"id": "3", "title": "Пункты стратегических и программных документов"},
    {"id": "4", "title": "Ожидаемые результаты"},
    {"id": "4.1", "title": "Прямые результаты"},
    {"id": "4.2", "title": "Конечный результат"},
    {"id": "5", "title": "Предельная сумма программы"},
]


def build_structure(text: str) -> dict[str, Any]:
    normalized = text.lower()
    sections: list[dict[str, Any]] = []

    for section in PCF_TEMPLATE:
        marker_pattern = re.escape(section["id"]).replace(r"\.", r"\.")
        present = bool(re.search(rf"\b{marker_pattern}\b", normalized)) or section["title"].lower() in normalized
        sections.append(
            {
                "id": section["id"],
                "title": section["title"],
                "status": "present" if present else "missing",
            }
        )

    structured_outline = "\n".join(
        f"{item['id']}. {item['title']}: {'[заполнено]' if item['status'] == 'present' else '[добавить]'}"
        for item in sections
    )

    return {
        "agent": "structure_agent",
        "template_name": "pcf_scientific_tz",
        "sections": sections,
        "structured_outline": structured_outline,
        "summary": {
            "total_sections": len(sections),
            "present": sum(1 for item in sections if item["status"] == "present"),
            "missing": sum(1 for item in sections if item["status"] == "missing"),
        },
    }
