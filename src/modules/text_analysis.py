"""Rule-based text quality analysis for technical specifications."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from src.utils.file_io import extract_snippet


VAGUE_PATTERNS = [
    r"\bпри необходимости\b",
    r"\bпо возможности\b",
    r"\bи\s+т\.?д\.?\b",
    r"\bв\s+кратчайшие\s+сроки\b",
    r"\bэффективн\w*\b",
    r"\bкачественн\w*\b",
    r"\bоптимальн\w*\b",
]


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def analyze_text(text: str) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    lower_text = text.lower()

    for pattern in VAGUE_PATTERNS:
        for match in re.finditer(pattern, lower_text):
            issues.append(
                {
                    "type": "vague_formulation",
                    "quote": extract_snippet(text, match.start()),
                    "severity": "Medium",
                    "recommendation": "Заменить размытую формулировку на измеримый критерий",
                }
            )

    sentences = _split_sentences(text)
    seen_pairs: set[tuple[int, int]] = set()
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            similarity = SequenceMatcher(None, sentences[i].lower(), sentences[j].lower()).ratio()
            if similarity >= 0.92:
                pair = (i, j)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                issues.append(
                    {
                        "type": "duplicate_requirement",
                        "quote": f"{sentences[i]} || {sentences[j]}",
                        "severity": "Low",
                        "recommendation": "Удалить дублирование или объединить требования в один пункт",
                    }
                )

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    for paragraph in paragraphs:
        p = paragraph.lower()
        has_positive = "должен" in p or "обязательно" in p
        has_negative = "не должен" in p or "запрещ" in p
        if has_positive and has_negative:
            issues.append(
                {
                    "type": "logical_conflict",
                    "quote": paragraph[:280],
                    "severity": "High",
                    "recommendation": "Разделить и уточнить противоречивые утверждения",
                }
            )

    return {
        "agent": "text_analysis_agent",
        "issues": issues,
        "summary": {
            "total_issues": len(issues),
            "vague_formulations": sum(1 for issue in issues if issue["type"] == "vague_formulation"),
            "duplicates": sum(1 for issue in issues if issue["type"] == "duplicate_requirement"),
            "logical_conflicts": sum(1 for issue in issues if issue["type"] == "logical_conflict"),
        },
    }
