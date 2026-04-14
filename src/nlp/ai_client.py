"""Unified AI client supporting OpenAI Codex and Claude."""

import os
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import config


class AIClient:
    """Unified client for AI analysis - supports GitHub Models, OpenAI and Claude."""
    
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize AI client with specified provider."""
        self.provider = provider or config.AI_PROVIDER
        self.client = None
        self.is_ready = False
        
        if self.provider == "github":
            self._init_github(api_key)
        elif self.provider == "openai":
            self._init_openai(api_key)
        elif self.provider == "openrouter":
            self._init_openrouter(api_key)
        elif self.provider == "claude":
            self._init_claude(api_key)
        else:
            print(f"⚠️ Unknown AI provider: {self.provider}")
    
    def _init_github(self, api_key: Optional[str] = None):
        """Initialize GitHub Models client."""
        self.api_key = api_key or config.GITHUB_TOKEN
        self.model = config.GITHUB_MODEL
        
        if self.api_key:
            try:
                from openai import OpenAI
                # GitHub Models uses Azure OpenAI endpoint
                self.client = OpenAI(
                    base_url="https://models.inference.ai.azure.com",
                    api_key=self.api_key,
                )
                self.is_ready = True
                print(f"✅ GitHub Models ({self.model}) инициализирован - БЕСПЛАТНО!")
            except Exception as e:
                print(f"⚠️ GitHub Models недоступен: {e}")
        else:
            print("ℹ️ GitHub Models не настроен (добавьте GITHUB_TOKEN в .env)")
    
    def _init_openai(self, api_key: Optional[str] = None):
        """Initialize OpenAI client."""
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = config.OPENAI_MODEL
        
        if self.api_key and self.api_key != "your-openai-key-here":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.is_ready = True
                print(f"✅ OpenAI ({self.model}) инициализирован")
            except Exception as e:
                print(f"⚠️ OpenAI API недоступен: {e}")
        else:
            print("ℹ️ OpenAI API не настроен (работает базовая детекция)")

    def _init_openrouter(self, api_key: Optional[str] = None):
        """Initialize OpenRouter client (OpenAI-compatible)."""
        self.api_key = api_key or config.OPENROUTER_API_KEY
        self.model = config.OPENROUTER_MODEL
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key,
                )
                self.is_ready = True
                print(f"✅ OpenRouter ({self.model}) инициализирован")
            except Exception as e:
                print(f"⚠️ OpenRouter недоступен: {e}")
        else:
            print("ℹ️ OpenRouter не настроен (добавьте OPENROUTER_API_KEY в .env)")
    
    def _init_claude(self, api_key: Optional[str] = None):
        """Initialize Claude client."""
        self.api_key = api_key or config.CLAUDE_API_KEY
        self.model = config.CLAUDE_MODEL
        
        if self.api_key and self.api_key != "sk-ant-your-key-here":
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
                self.is_ready = True
                print(f"✅ Claude ({self.model}) инициализирован")
            except Exception as e:
                print(f"⚠️ Claude API недоступен: {e}")
        else:
            print("ℹ️ Claude API не настроен (работает базовая детекция)")
    
    def is_available(self) -> bool:
        """Check if AI API is available."""
        return self.is_ready
    
    def detect_dead_regulations(self, document_text: str, document_title: str = "") -> Dict:
        """
        Detect dead regulations in a legal document using AI.
        
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
                "summary": f"{self.provider.upper()} API не настроен. Используйте базовую детекцию.",
                "error": "NO_API_KEY"
            }
        
        # Chunking strategy for long documents.
        # Keep conservative size because prompt instructions add many tokens.
        MAX_CHUNK_SIZE = 3000
        chunks = []
        
        if len(document_text) <= MAX_CHUNK_SIZE:
            # Single chunk - analyze as is
            chunks = [document_text]
        else:
            # Split into overlapping chunks by paragraphs/sentences
            paragraphs = document_text.split('\n\n')
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) < MAX_CHUNK_SIZE:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para + "\n\n"
            
            if current_chunk:
                chunks.append(current_chunk)
        
        # Analyze each chunk and aggregate results
        all_issues = []
        all_summaries = []
        had_chunk_error = False
        
        idx = 0
        while idx < len(chunks):
            chunk = chunks[idx]
            chunk_label = f" (Часть {idx+1}/{len(chunks)})" if len(chunks) > 1 else ""
            
            prompt = f"""Проанализируй следующий нормативный акт Казахстана на наличие "мёртвых регуляций".

Название документа: {document_title}{chunk_label}

Текст документа:
{chunk}

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

Ответ предоставь СТРОГО в формате JSON:
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
                if self.provider in ["openai", "github"]:
                    result = self._call_openai(prompt)
                elif self.provider == "claude":
                    result = self._call_claude(prompt)
                else:
                    result = {"has_issues": False, "issues": [], "summary": ""}
                
                if result.get("issues"):
                    all_issues.extend(result["issues"])
                if result.get("summary"):
                    all_summaries.append(result["summary"])
                    
            except Exception as e:
                print(f"❌ Error analyzing chunk {idx+1}: {e}")
                err_text = str(e)
                # If request is still too large, split this chunk and retry both halves.
                if (
                    ("tokens_limit_reached" in err_text)
                    or ("Request body too large" in err_text)
                    or ("413" in err_text)
                ) and len(chunk) > 1200:
                    mid = len(chunk) // 2
                    left = chunk[:mid].strip()
                    right = chunk[mid:].strip()
                    if left and right:
                        chunks[idx:idx + 1] = [left, right]
                        all_summaries.append(
                            f"AI: часть {idx+1} была слишком большой, автоматически разделена."
                        )
                        continue
                all_summaries.append(f"Ошибка AI в части {idx+1}: {str(e)}")
                had_chunk_error = True
                idx += 1
                continue
            idx += 1
        
        # Aggregate results from all chunks
        combined_summary = " | ".join(all_summaries) if all_summaries else ""
        if "RateLimitReached" in combined_summary or "429" in combined_summary:
            return {
                "has_issues": False,
                "issues": [],
                "summary": combined_summary or "AI лимит запросов исчерпан",
                "chunks_analyzed": len(chunks),
                "error": "AI_RATE_LIMIT",
            }
        if not all_issues:
            payload = {
                "has_issues": False,
                "issues": [],
                "summary": "Проблем не найдено" if not all_summaries else combined_summary,
                "chunks_analyzed": len(chunks),
            }
            if had_chunk_error:
                payload["error"] = "AI_NO_ISSUES_OR_FAILED"
            return payload
        
        # Deduplicate issues by quote similarity
        unique_issues = []
        seen_quotes = set()
        
        for issue in all_issues:
            quote_key = issue.get("quote", "")[:100].lower().strip()
            if quote_key and quote_key not in seen_quotes:
                unique_issues.append(issue)
                seen_quotes.add(quote_key)
        
        return {
            "has_issues": True,
            "issues": unique_issues,
            "summary": f"Найдено {len(unique_issues)} проблем в {len(chunks)} частях документа. " + " ".join(all_summaries),
            "chunks_analyzed": len(chunks),
            "total_length": len(document_text)
        }
    
    def _call_openai(self, prompt: str) -> Dict:
        """Call OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу законодательства Казахстана. Отвечай ТОЛЬКО в формате JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON (with fallback for markdown/code-fenced responses)
        import json
        try:
            return json.loads(content)
        except Exception:
            cleaned = (content or "").strip()
            if "```json" in cleaned:
                json_start = cleaned.find("```json") + 7
                json_end = cleaned.find("```", json_start)
                cleaned = cleaned[json_start:json_end].strip()
            elif "```" in cleaned:
                json_start = cleaned.find("```") + 3
                json_end = cleaned.find("```", json_start)
                cleaned = cleaned[json_start:json_end].strip()
            # Extract first JSON object if model added extra prose
            first = cleaned.find("{")
            last = cleaned.rfind("}")
            if first != -1 and last != -1 and last > first:
                cleaned = cleaned[first:last + 1]
            return json.loads(cleaned)
    
    def _call_claude(self, prompt: str) -> Dict:
        """Call Claude API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        
        # Extract JSON from response
        import json
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
            return f"{self.provider.upper()} API не настроен для генерации объяснений."
        
        prompt = f"""Объясни простым языком, почему следующий фрагмент закона является проблемным:

Фрагмент: {issue_text}

Контекст: {context}

Предоставь:
1. Что именно является проблемой
2. Какие последствия это имеет
3. Как это можно исправить

Ответ должен быть понятен обычному гражданину, не юристу."""

        try:
            if self.provider in ["openai", "github"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Ты эксперт по законодательству. Объясняй просто и понятно."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1024,
                    temperature=0.5
                )
                return response.choices[0].message.content
            
            elif self.provider == "claude":
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


# Backward compatibility - keep ClaudeClient name
class ClaudeClient(AIClient):
    """Backward compatibility wrapper."""
    def __init__(self, api_key: Optional[str] = None):
        # Use configured provider instead of forcing claude
        super().__init__(provider=config.AI_PROVIDER, api_key=api_key)


# Test function
if __name__ == "__main__":
    print(f"🤖 Testing AI Client (Provider: {config.AI_PROVIDER})")
    print("=" * 60)
    
    client = AIClient()
    
    if client.is_available():
        print(f"✅ {config.AI_PROVIDER.upper()} API доступен!")
        
        # Test document
        test_doc = """
        Статья 1. О Министерстве связи и информации
        
        Министерство связи и информации Республики Казахстан осуществляет 
        регулирование в сфере телекоммуникаций и информатизации.
        
        Примечание: Министерство связи и информации было упразднено в 2019 году.
        """
        
        print("\n📄 Тестирование анализа документа...")
        result = client.detect_dead_regulations(test_doc, "Тестовый закон")
        
        import json
        print("\n📊 Результат:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ℹ️ {config.AI_PROVIDER.upper()} API не настроен")
        print("\n📝 Как добавить API ключ:")
        
        if config.AI_PROVIDER == "openai":
            print("\n1. Получите OpenAI API ключ:")
            print("   https://platform.openai.com/api-keys")
            print("\n2. Добавьте в .env файл:")
            print("   OPENAI_API_KEY=sk-...")
        else:
            print("\n1. Получите Claude API ключ:")
            print("   https://console.anthropic.com/")
            print("\n2. Добавьте в .env файл:")
            print("   CLAUDE_API_KEY=sk-ant-...")
        
        print("\n✅ Базовая детекция работает без API ключа!")
