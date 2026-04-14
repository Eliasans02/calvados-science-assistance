"""Test GitHub Models API."""

import os
from openai import OpenAI

def test_github_models():
    """Test GitHub Models API access."""
    
    # GitHub token from environment
    github_token = os.getenv("GITHUB_TOKEN", "")
    
    if not github_token:
        print("❌ GITHUB_TOKEN not set in environment")
        print("   Run: export GITHUB_TOKEN=$(gh auth token)")
        return False
    
    print("🔍 Проверка GitHub Models API...")
    print(f"GitHub Token: {github_token[:20]}...{github_token[-4:]}")
    print()
    
    # Initialize OpenAI client with GitHub endpoint
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=github_token,
    )
    
    try:
        print("📡 Отправка тестового запроса к GitHub Models...")
        print("Модель: gpt-4o-mini")
        print()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'GitHub Models работают!' in Russian"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        result = response.choices[0].message.content
        
        print("✅ УСПЕХ! GitHub Models работают!")
        print(f"📝 Ответ AI: {result}")
        print(f"📊 Model: {response.model}")
        print(f"💰 Tokens: {response.usage.total_tokens}")
        print()
        print("🎉 Можем использовать БЕСПЛАТНО:")
        print("   - gpt-4o, gpt-4o-mini")
        print("   - claude-3.5-sonnet")
        print("   - llama-3.1, mistral")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print()
        print("💡 Попробуем альтернативные модели...")
        
        # Try alternative models
        for model in ["gpt-4o-mini", "gpt-4o", "meta-llama-3-8b-instruct"]:
            try:
                print(f"\n🔄 Пробуем: {model}")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=10
                )
                print(f"✅ {model} работает!")
                return True
            except Exception as e2:
                print(f"❌ {model}: {str(e2)[:60]}...")
        
        return False

if __name__ == "__main__":
    test_github_models()
