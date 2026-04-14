"""Test OpenAI API key."""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment
load_dotenv()

def test_openai_key():
    """Test if OpenAI API key works."""
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    print("🔍 Проверка OpenAI API ключа...")
    print(f"API Key: {api_key[:20]}...{api_key[-4:] if len(api_key) > 24 else '❌ Не найден'}")
    print()
    
    if not api_key or api_key == "your-openai-key-here":
        print("❌ API ключ не настроен!")
        print("📝 Добавьте в .env файл:")
        print("   OPENAI_API_KEY=sk-...")
        return False
    
    try:
        # Initialize client
        client = OpenAI(api_key=api_key)
        
        # Test with simple request
        print("📡 Отправка тестового запроса...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API works!' in one word"}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ API работает! Ответ: {result}")
        print(f"📊 Model: {response.model}")
        print(f"💰 Tokens used: {response.usage.total_tokens}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print()
        print("💡 Возможные причины:")
        print("   - Неверный API ключ")
        print("   - Нет доступа к OpenAI API")
        print("   - Проблемы с сетью")
        print("   - Закончились credits")
        return False

if __name__ == "__main__":
    test_openai_key()
