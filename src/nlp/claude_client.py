"""Claude Opus client for legal text analysis."""

import os
from typing import Dict, List, Optional
import sys
sys.path.append(str(os.path.dirname(os.path.dirname(__file__))))
from config import CLAUDE_API_KEY, CLAUDE_MODEL


class ClaudeClient:
    """Client for interacting with Claude Opus API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude client."""
        self.api_key = api_key or CLAUDE_API_KEY
        self.model = CLAUDE_MODEL
        self.client = None
        
        # Only initialize if API key is valid
        if self.api_key and self.api_key != "sk-ant-your-key-here":
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
                print("✅ Claude API инициализирован")
            except Exception as e:
                print(f"⚠️ Claude API недоступен: {e}")
                self.client = None
        else:
            print("ℹ️ Claude API не настроен (работает базовая детекция)")
    
    def is_available(self) -> bool:
        """Check if Claude API is available."""
        return self.client is not None
    
    def detect_dead_regulations(self, document_text: str, document_title: str = "") -> Dict:
        """
        Detect dead regulations in a legal document.
        
        Args:
            document_text: Full text of the legal document
            document_title: Title/name of the document
            
        Returns:
            Dictionary with detected issues and explanations
        """
        if not self.is_available():
            return {
                "has_issues": False,
                "issues": [],
                "summary": "Claude API не настроен. Используйте базовую детекцию.",
                "error": "NO_API_KEY"
            }
        
        prompt = f"""Проанализируй следующий нормативный акт Казахстана на наличие "мёртвых регуляций".

Название документа: {document_title}

Текст документа:
{document_text[:4000]}

Найди следующие проблемы:

1. **Устаревшие термины**: Ссылки на несуществующие органы, устаревшие названия, отменённые структуры
2. **Противоречия**: Конфликты с более новыми законами или внутренние противоречия
3. **Дублирование**: Нормы, которые дублируют другие законы
4. **Неприменимость**: Нормы без механизма реализации

Для каждой найденной проблемы предоставь:
- Тип проблемы
- Цитата из документа (точный текст)
- Детальное объяснение почему это проблема
- Критичность (High/Medium/Low)
- Рекомендации по устранению

Ответ предоставь в формате JSON:
{{
    "has_issues": true/false,
    "issues": [
        {{
            "type": "outdated_terms" | "contradiction" | "duplication" | "inapplicability",
            "quote": "точная цитата",
            "explanation": "детальное объяснение",
            "severity": "High" | "Medium" | "Low",
            "recommendation": "рекомендация"
        }}
    ],
    "summary": "краткое резюме анализа"
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract JSON from response
            content = response.content[0].text
            
            # Try to parse JSON from response
            import json
            # Find JSON in response (Claude might wrap it in markdown)
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"❌ Error calling Claude API: {e}")
            return {
                "has_issues": False,
                "issues": [],
                "summary": f"Ошибка API: {str(e)}",
                "error": str(e)
            }
    
    def explain_issue(self, issue_text: str, context: str = "") -> str:
        """
        Generate detailed explanation for a specific issue.
        
        Args:
            issue_text: The problematic text
            context: Additional context
            
        Returns:
            Detailed explanation
        """
        if not self.is_available():
            return "Claude API не настроен для генерации объяснений."
        
        prompt = f"""Объясни простым языком, почему следующий фрагмент закона является проблемным:

Фрагмент: {issue_text}

Контекст: {context}

Предоставь:
1. Что именно является проблемой
2. Какие последствия это имеет
3. Как это можно исправить

Ответ должен быть понятен обычному гражданину, не юристу."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.5,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"Ошибка генерации объяснения: {str(e)}"


# Test function
if __name__ == "__main__":
    client = ClaudeClient()
    
    if client.is_available():
        print("✅ Claude API доступен!")
        
        # Test document
        test_doc = """
        Статья 1. О Министерстве связи и информации
        
        Министерство связи и информации Республики Казахстан осуществляет 
        регулирование в сфере телекоммуникаций и информатизации.
        
        Примечание: Министерство связи и информации было упразднено в 2019 году.
        """
        
        result = client.detect_dead_regulations(test_doc, "Тестовый закон")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("ℹ️ Claude API не настроен")
        print("\nГде получить API ключ:")
        print("1. Anthropic: https://console.anthropic.com/")
        print("2. Antigravity: согласно вашей подписке")
        print("\nДобавьте ключ в файл .env:")
        print("CLAUDE_API_KEY=sk-ant-...")
