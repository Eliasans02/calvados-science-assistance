"""Automatic draft generation for technical specification."""

from __future__ import annotations

from typing import Any


def generate_tz(payload: dict[str, Any]) -> dict[str, Any]:
    project_title = payload.get("project_title", "Новая научно-техническая программа")
    priority = payload.get("priority", "Энергия, передовые материалы и транспорт")
    specialization = payload.get("specialization", "Цифровые технологии и ИИ")
    budget_total = payload.get("budget_total", "1 500 000 тыс. тенге")
    years = payload.get("years", ["2026", "2027", "2028"])
    year_budget = payload.get("year_budget", "500 000 тыс. тенге")

    generated_text = f"""
1. Общие сведения
1.1. Наименование приоритета: {priority}
1.2. Наименование специализированного направления: {specialization}

2. Цели и задачи программы
2.1. Цель программы: {project_title}
2.2. Задачи программы:
- Исследование и разработка методологии
- Создание цифровой платформы и интеграция AI-инструментов
- Проведение пилотной апробации и оценка эффективности

3. Пункты стратегических и программных документов
- Указать конкретные документы, постановления и пункты реализации

4. Ожидаемые результаты
4.1. Прямые результаты:
- Научные публикации, патенты, программные модули, аналитические отчеты
- Количественные KPI (не менее X публикаций, не менее Y внедрений)
4.2. Конечный результат:
- Повышение технологической готовности и социально-экономического эффекта

5. Предельная сумма программы
На весь срок: {budget_total}
{chr(10).join([f"- на {y} г.: {year_budget}" for y in years])}
""".strip()

    return {
        "agent": "generation_agent",
        "generated_title": project_title,
        "template": "pcf_scientific_tz",
        "generated_text": generated_text,
    }
