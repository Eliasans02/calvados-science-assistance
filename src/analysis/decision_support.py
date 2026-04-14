"""Decision Support System for Government Officials."""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ActionItem:
    """Single action item in decision workflow."""
    id: str
    title: str
    description: str
    priority: str  # Critical, High, Medium, Low
    category: str  # Review, Update, Revoke, Consult
    deadline_days: int
    responsible: str
    dependencies: List[str]
    status: str = "pending"


class DecisionSupportSystem:
    """Generate actionable recommendations for government officials."""
    
    def __init__(self):
        self.priority_weights = {
            "Critical": 100,
            "High": 75,
            "Medium": 50,
            "Low": 25
        }
    
    def generate_action_plan(self, analysis_result: Dict) -> Dict:
        """Generate structured action plan based on analysis results."""
        issues = analysis_result.get("issues_found", [])
        
        if not issues:
            return {
                "status": "no_actions_required",
                "message": "Критических проблем не выявлено. Документ соответствует стандартам.",
                "actions": [],
                "summary": {
                    "total_actions": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
        
        actions = []
        action_id = 1
        
        for issue in issues:
            action = self._create_action_from_issue(issue, action_id)
            if action:
                actions.append(action)
                action_id += 1
        
        # Sort by priority
        actions.sort(key=lambda x: self.priority_weights.get(x.priority, 0), reverse=True)
        
        # Generate workflow
        workflow = self._generate_workflow(actions)
        
        # Calculate summary
        summary = self._calculate_summary(actions)
        
        return {
            "status": "actions_required",
            "message": f"Выявлено {len(issues)} проблем. Требуются {len(actions)} действий.",
            "actions": [self._action_to_dict(a) for a in actions],
            "workflow": workflow,
            "summary": summary,
            "estimated_time_days": self._estimate_total_time(actions)
        }
    
    def _create_action_from_issue(self, issue: Dict, action_id: int) -> Optional[ActionItem]:
        """Convert issue to actionable item."""
        issue_type = issue.get("type", "unknown")
        severity = issue.get("severity", "Low")
        
        # Map issue type to action category and responsible party
        type_mapping = {
            "outdated_terms": {
                "category": "Update",
                "responsible": "Юридический отдел",
                "deadline_base": 30
            },
            "contradiction": {
                "category": "Review",
                "responsible": "Экспертная комиссия",
                "deadline_base": 45
            },
            "duplication": {
                "category": "Revoke",
                "responsible": "Законодательный отдел",
                "deadline_base": 60
            },
            "inapplicability": {
                "category": "Consult",
                "responsible": "Профильный комитет",
                "deadline_base": 30
            }
        }
        
        mapping = type_mapping.get(issue_type, {
            "category": "Review",
            "responsible": "Ответственный отдел",
            "deadline_base": 30
        })
        
        # Adjust deadline based on severity
        deadline_multiplier = {
            "Critical": 0.5,
            "High": 0.75,
            "Medium": 1.0,
            "Low": 1.5
        }
        
        deadline = int(mapping["deadline_base"] * deadline_multiplier.get(severity, 1.0))
        
        return ActionItem(
            id=f"ACT-{action_id:03d}",
            title=self._generate_action_title(issue_type, severity),
            description=issue.get("recommendation", "Требуется проверка"),
            priority=severity if severity in ["Critical", "High", "Medium", "Low"] else "Medium",
            category=mapping["category"],
            deadline_days=deadline,
            responsible=mapping["responsible"],
            dependencies=[],
            status="pending"
        )
    
    def _generate_action_title(self, issue_type: str, severity: str) -> str:
        """Generate human-readable action title."""
        titles = {
            "outdated_terms": "Обновить устаревшие термины и ссылки",
            "contradiction": "Устранить противоречия с действующим законодательством",
            "duplication": "Отменить дублирующую норму",
            "inapplicability": "Разработать механизм реализации нормы"
        }
        
        base_title = titles.get(issue_type, "Проверить выявленную проблему")
        
        if severity == "Critical":
            return f"[СРОЧНО] {base_title}"
        elif severity == "High":
            return f"[ПРИОРИТЕТ] {base_title}"
        else:
            return base_title
    
    def _generate_workflow(self, actions: List[ActionItem]) -> List[Dict]:
        """Generate step-by-step workflow."""
        workflow = []
        
        # Phase 1: Critical actions
        critical = [a for a in actions if a.priority == "Critical"]
        if critical:
            workflow.append({
                "phase": 1,
                "name": "Срочные меры",
                "description": "Немедленное реагирование на критические проблемы",
                "actions": [a.id for a in critical],
                "duration_days": max([a.deadline_days for a in critical]) if critical else 0
            })
        
        # Phase 2: High priority
        high = [a for a in actions if a.priority == "High"]
        if high:
            workflow.append({
                "phase": 2,
                "name": "Приоритетные задачи",
                "description": "Устранение существенных проблем",
                "actions": [a.id for a in high],
                "duration_days": max([a.deadline_days for a in high]) if high else 0
            })
        
        # Phase 3: Medium and Low
        medium_low = [a for a in actions if a.priority in ["Medium", "Low"]]
        if medium_low:
            workflow.append({
                "phase": 3,
                "name": "Плановые работы",
                "description": "Систематическое улучшение документа",
                "actions": [a.id for a in medium_low],
                "duration_days": max([a.deadline_days for a in medium_low]) if medium_low else 0
            })
        
        return workflow
    
    def _calculate_summary(self, actions: List[ActionItem]) -> Dict:
        """Calculate action summary."""
        from collections import Counter
        
        priority_counts = Counter(a.priority for a in actions)
        category_counts = Counter(a.category for a in actions)
        
        return {
            "total_actions": len(actions),
            "critical": priority_counts.get("Critical", 0),
            "high": priority_counts.get("High", 0),
            "medium": priority_counts.get("Medium", 0),
            "low": priority_counts.get("Low", 0),
            "by_category": dict(category_counts)
        }
    
    def _estimate_total_time(self, actions: List[ActionItem]) -> int:
        """Estimate total time considering parallel work."""
        if not actions:
            return 0
        
        # Group by responsible party (can work in parallel)
        from collections import defaultdict
        by_responsible = defaultdict(list)
        
        for action in actions:
            by_responsible[action.responsible].append(action.deadline_days)
        
        # Max time for each group (parallel execution)
        return max(max(deadlines) for deadlines in by_responsible.values())
    
    def _action_to_dict(self, action: ActionItem) -> Dict:
        """Convert ActionItem to dictionary."""
        return {
            "id": action.id,
            "title": action.title,
            "description": action.description,
            "priority": action.priority,
            "category": action.category,
            "deadline_days": action.deadline_days,
            "responsible": action.responsible,
            "dependencies": action.dependencies,
            "status": action.status
        }
    
    def export_action_plan(self, action_plan: Dict, format: str = "md") -> str:
        """Export action plan in specified format."""
        if format == "md":
            return self._export_markdown(action_plan)
        elif format == "json":
            import json
            return json.dumps(action_plan, ensure_ascii=False, indent=2)
        else:
            return str(action_plan)
    
    def _export_markdown(self, action_plan: Dict) -> str:
        """Export as Markdown document."""
        lines = []
        lines.append("# План действий по результатам анализа")
        lines.append(f"\n**Дата формирования:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        lines.append(f"**Статус:** {action_plan['message']}\n")
        
        summary = action_plan['summary']
        lines.append("## Сводка")
        lines.append(f"- Всего действий: {summary['total_actions']}")
        lines.append(f"- Критических: {summary['critical']}")
        lines.append(f"- Высокий приоритет: {summary['high']}")
        lines.append(f"- Средний приоритет: {summary['medium']}")
        lines.append(f"- Низкий приоритет: {summary['low']}")
        lines.append(f"\n**Ориентировочный срок:** {action_plan.get('estimated_time_days', 0)} дней\n")
        
        if action_plan.get('workflow'):
            lines.append("## Этапы работы\n")
            for phase in action_plan['workflow']:
                lines.append(f"### Этап {phase['phase']}: {phase['name']}")
                lines.append(f"*{phase['description']}*")
                lines.append(f"Срок: {phase['duration_days']} дней\n")
        
        lines.append("## Детальный план действий\n")
        
        for action in action_plan['actions']:
            lines.append(f"### {action['id']}: {action['title']}")
            lines.append(f"- **Приоритет:** {action['priority']}")
            lines.append(f"- **Категория:** {action['category']}")
            lines.append(f"- **Ответственный:** {action['responsible']}")
            lines.append(f"- **Срок:** {action['deadline_days']} дней")
            lines.append(f"- **Описание:** {action['description']}\n")
        
        return "\n".join(lines)
