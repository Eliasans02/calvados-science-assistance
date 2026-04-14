"""Recommendation service with ML-ready integration contract."""

from __future__ import annotations

import json
from typing import Any, Optional

from src.nlp.ai_client import AIClient


def build_recommendations(payload: dict[str, Any]) -> dict[str, Any]:
    issues = payload.get("issues", [])
    context = payload.get("context") or {}
    document_text = (payload.get("text") or "").strip()
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

    transparency = _build_transparency(
        document_text=document_text,
        issues=issues,
        context=context,
    )

    ai_enhancement = _build_ai_enhancement(
        document_text=document_text,
        issues=issues,
        recommendations=recommendations,
        ai_provider=str(context.get("ai_provider", "")).strip() or None,
        ai_api_key=str(context.get("ai_api_key", "")).strip() or None,
        transparency=transparency,
    )
    high_priority_count = sum(1 for item in recommendations if item.get("priority") == "High")

    return {
        "agent": "recommendation_agent",
        "recommendations": recommendations,
        "insight": {
            "issues_total": len(issues),
            "recommendations_total": len(recommendations),
            "high_priority_total": high_priority_count,
        },
        "transparency": transparency,
        "ai_enhancement": ai_enhancement,
        "ml_adapter": {
            "enabled": False,
            "ready_for_training_data": True,
            "expected_input_keys": ["issues", "historical_tz_examples", "domain"],
            "notes": "Подключите ML-модель через data layer без изменения контракта endpoint",
        },
    }


def _build_ai_enhancement(
    document_text: str,
    issues: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    ai_provider: Optional[str] = None,
    ai_api_key: Optional[str] = None,
    transparency: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    ai_client = AIClient(provider=ai_provider, api_key=ai_api_key)
    if not ai_client.is_available():
        return {
            "status": "unavailable",
            "reason": "ai_provider_not_configured",
            "provider": ai_client.provider,
            "summary": f"{ai_client.provider.upper()} API не настроен, использованы rule-based рекомендации.",
            "confidence": (transparency or {}).get("analysis_confidence", "medium"),
        }

    if not issues:
        quality_flag = ((transparency or {}).get("text_quality") or {}).get("quality_flag", "unknown")
        low_quality = quality_flag in {"poor", "low"}
        summary = "Критичных проблем не обнаружено, AI-обогащение не требуется."
        note = ""
        confidence = "high"
        if low_quality:
            summary = "Критичных проблем не найдено автоматикой, но качество извлечённого текста низкое."
            note = "Рекомендуется перепроверка OCR/исходного файла и ручная экспертная валидация."
            confidence = "low"
        elif len(document_text) < 1200:
            summary = "Критичных проблем не найдено, но документ короткий; результат может быть неполным."
            note = "Для большей точности загрузите полный текст ТЗ или улучшите OCR."
            confidence = "medium"
        return {
            "status": "skipped",
            "reason": "no_issues",
            "provider": ai_client.provider,
            "summary": summary,
            "note": note,
            "confidence": confidence,
        }

    doc_preview = document_text[:5000]
    prompt = (
        "Ты эксперт по оценке научно-технических ТЗ. "
        "На основе списка проблем и базовых рекомендаций сформируй усиленный план улучшений.\n\n"
        f"Проблемы:\n{json.dumps(issues, ensure_ascii=False, indent=2)}\n\n"
        f"Базовые рекомендации:\n{json.dumps(recommendations, ensure_ascii=False, indent=2)}\n\n"
        f"Фрагмент ТЗ (если есть):\n{doc_preview}\n\n"
        "Верни СТРОГО JSON формата:\n"
        "{"
        "\"executive_summary\": \"короткое резюме\","
        "\"priority_actions\": ["
        "{\"priority\":\"High|Medium|Low\",\"section\":\"раздел ТЗ\",\"problem\":\"что не так\",\"action\":\"что сделать\",\"expected_effect\":\"какой эффект\"}"
        "],"
        "\"quick_wins\": [\"быстрые улучшения (до 3 пунктов)\"],"
        "\"final_recommendation\": \"итоговый совет\""
        "}"
    )

    try:
        parsed = _call_ai_json(ai_client, prompt)
    except Exception as exc:
        return {
            "status": "error",
            "reason": "ai_call_failed",
            "provider": ai_client.provider,
            "error": str(exc),
        }

    return {
        "status": "ready",
        "provider": ai_client.provider,
        "model": getattr(ai_client, "model", ""),
        "executive_summary": str(parsed.get("executive_summary", "")).strip(),
        "priority_actions": parsed.get("priority_actions", []),
        "quick_wins": parsed.get("quick_wins", []),
        "final_recommendation": str(parsed.get("final_recommendation", "")).strip(),
        "confidence": (transparency or {}).get("analysis_confidence", "medium"),
    }


def _build_transparency(
    document_text: str,
    issues: list[dict[str, Any]],
    context: dict[str, Any],
) -> dict[str, Any]:
    agent_outputs = context.get("agent_outputs") or {}
    file_warning = str(context.get("file_warning") or "").strip()
    text_length = int(context.get("text_length") or len(document_text))

    text_quality = _estimate_text_quality(document_text=document_text, warning=file_warning)
    text_output = agent_outputs.get("text-analysis") or {}
    req_output = agent_outputs.get("requirement-analysis") or {}
    compliance_output = agent_outputs.get("compliance") or {}
    structure_output = agent_outputs.get("structure") or {}

    detected_by_agent = {
        "text-analysis": int(((text_output.get("summary") or {}).get("total_issues")) or 0),
        "requirement-analysis": int(((req_output.get("summary") or {}).get("total_issues")) or 0),
        "compliance-missing": len(compliance_output.get("missing_items") or []),
        "structure-missing-sections": sum(
            1 for section in (structure_output.get("sections") or []) if section.get("status") == "missing"
        ),
    }

    confidence = "high"
    if text_quality["quality_flag"] in {"poor", "low"}:
        confidence = "low"
    elif text_quality["quality_flag"] == "medium":
        confidence = "medium"

    notes: list[str] = []
    if file_warning:
        notes.append(file_warning)
    if text_length < 1200:
        notes.append("Короткий извлечённый текст: анализ может быть неполным.")
    if text_quality["noise_ratio"] > 0.18:
        notes.append("Много служебных/шумовых символов: стоит улучшить OCR.")
    if not notes:
        notes.append("Качество текста достаточное для автоматического анализа.")

    return {
        "text_length": text_length,
        "issue_count_total": len(issues),
        "detected_by_agent": detected_by_agent,
        "text_quality": text_quality,
        "file_warning": file_warning or None,
        "analysis_confidence": confidence,
        "notes": notes,
    }


def _estimate_text_quality(document_text: str, warning: str) -> dict[str, Any]:
    raw = document_text or ""
    length = len(raw)
    if length == 0:
        return {
            "quality_flag": "poor",
            "word_count": 0,
            "alpha_ratio": 0.0,
            "noise_ratio": 1.0,
            "ocr_warning_detected": bool(warning),
        }

    words = [token for token in raw.replace("\n", " ").split(" ") if token.strip()]
    word_count = len(words)
    alpha_count = sum(1 for ch in raw if ch.isalpha())
    printable_count = sum(1 for ch in raw if ch.isprintable())
    punctuation_count = sum(1 for ch in raw if ch in "[]{}<>|_/\\~=+*@#$%^&`")
    digit_count = sum(1 for ch in raw if ch.isdigit())

    alpha_ratio = alpha_count / max(1, length)
    noise_ratio = (punctuation_count + max(0, length - printable_count) + digit_count * 0.2) / max(1, length)
    ocr_warning_detected = bool(warning and "ocr" in warning.lower())

    quality_flag = "good"
    if length < 700 or word_count < 120 or alpha_ratio < 0.52 or noise_ratio > 0.24 or ocr_warning_detected:
        quality_flag = "low"
    if length < 300 or word_count < 60 or alpha_ratio < 0.42 or noise_ratio > 0.35:
        quality_flag = "poor"
    if quality_flag == "good" and (length < 1400 or word_count < 220 or noise_ratio > 0.14):
        quality_flag = "medium"

    return {
        "quality_flag": quality_flag,
        "word_count": word_count,
        "alpha_ratio": round(alpha_ratio, 3),
        "noise_ratio": round(noise_ratio, 3),
        "ocr_warning_detected": ocr_warning_detected,
    }


def _call_ai_json(ai_client: AIClient, prompt: str) -> dict[str, Any]:
    provider = ai_client.provider
    if provider in {"openai", "github", "openrouter"}:
        response = ai_client.client.chat.completions.create(
            model=ai_client.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты senior-эксперт по научно-техническим ТЗ. "
                        "Отвечай только валидным JSON, без markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2048,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return _safe_json_parse(content)

    if provider == "claude":
        response = ai_client.client.messages.create(
            model=ai_client.model,
            max_tokens=2048,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        return _safe_json_parse(content)

    raise RuntimeError(f"Unsupported AI provider for structured output: {provider}")


def _safe_json_parse(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        raise ValueError("Empty AI response")
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        text = text[start:end].strip() if end != -1 else text[start:].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        text = text[start:end].strip() if end != -1 else text[start:].strip()

    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        text = text[first : last + 1]

    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("AI JSON response must be an object")
    return parsed
