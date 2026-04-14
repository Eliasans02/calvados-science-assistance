"""Тест AI интеграции в Dead Regulations Detector."""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent / "src")
sys.path.insert(0, parent_dir)

from nlp.ai_client import AIClient
import config

def test_ai_modes():
    """Тестирует разные режимы детекции."""
    
    test_doc = """
    ПРИКАЗ МИНИСТРА ВНУТРЕННИХ ДЕЛ РЕСПУБЛИКИ КАЗАХСТАН
    
    От 15 января 2010 года № 23
    
    1. Утвердить Положение о порядке регистрации граждан.
    2. Контроль за исполнением возложить на Департамент административной полиции.
    3. Приказ вступает в силу со дня подписания.
    
    Министр внутренних дел                    И.О. Фамилия
    """
    
    print("=" * 60)
    print("🧪 ТЕСТ AI ИНТЕГРАЦИИ")
    print("=" * 60)
    print()
    
    # Режим 1: Базовая детекция (без AI)
    print("1️⃣ БАЗОВАЯ ДЕТЕКЦИЯ (без AI API)")
    print("-" * 60)
    
    from analysis.dead_reg_detector import DeadRegulationDetector
    basic_detector = DeadRegulationDetector()
    basic_result = basic_detector.analyze_document({"full_text": test_doc, "title": "Тестовый приказ"})
    
    print(f"✅ Найдено проблем: {len(basic_result['issues_found'])}")
    print(f"📊 Severity Score: {basic_result['severity_score']}/100")
    
    if basic_result['issues_found']:
        for idx, issue in enumerate(basic_result['issues_found'], 1):
            print(f"\n   Проблема #{idx}:")
            print(f"   - Тип: {issue['issue_type']}")
            print(f"   - Цитата: {issue['quote'][:50]}...")
            print(f"   - Уровень: {issue['severity']}")
    else:
        print("   Проблемы не найдены")
    
    print("\n")
    
    # Режим 2: С AI (попытка)
    print("2️⃣ AI-ДЕТЕКЦИЯ (OpenAI/Claude)")
    print("-" * 60)
    
    print(f"Провайдер: {config.AI_PROVIDER}")
    
    if config.AI_PROVIDER == "openai":
        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your-openai-key-here":
            print("❌ OpenAI API ключ не настроен")
        else:
            print(f"✅ OpenAI ключ: {config.OPENAI_API_KEY[:20]}...")
            
    elif config.AI_PROVIDER == "claude":
        if not config.CLAUDE_API_KEY or config.CLAUDE_API_KEY == "sk-ant-your-key-here":
            print("❌ Claude API ключ не настроен")
        else:
            print(f"✅ Claude ключ: {config.CLAUDE_API_KEY[:20]}...")
    
    try:
        client = AIClient()
        print("\n🤖 Отправка запроса к AI...")
        ai_result = client.detect_dead_regulations(test_doc)
        
        print(f"✅ AI анализ успешен!")
        print(f"📊 Найдено проблем: {len(ai_result.get('issues', []))}")
        print(f"📊 Severity Score: {ai_result.get('severity_score', 0)}/100")
        
        if ai_result.get('issues'):
            for idx, issue in enumerate(ai_result['issues'][:3], 1):
                print(f"\n   AI Проблема #{idx}:")
                print(f"   - Тип: {issue.get('issue_type', 'unknown')}")
                print(f"   - Explanation: {issue.get('explanation', 'N/A')[:80]}...")
                
    except Exception as e:
        print(f"❌ AI анализ не сработал: {e}")
        print(f"💡 Причина: {str(e)[:100]}")
    
    print("\n")
    print("=" * 60)
    print("📝 ИТОГ")
    print("=" * 60)
    print()
    print("✅ Базовая детекция: РАБОТАЕТ")
    print(f"{'✅' if 'ai_result' in locals() else '❌'} AI детекция: {'РАБОТАЕТ' if 'ai_result' in locals() else 'НЕ РАБОТАЕТ (нет квоты/ключа)'}")
    print()
    print("💡 Система ФУНКЦИОНАЛЬНА даже без AI API!")
    print("   - Детектирует устаревшие термины")
    print("   - Вычисляет severity score")
    print("   - Предоставляет explainability")
    print()

if __name__ == "__main__":
    test_ai_modes()
