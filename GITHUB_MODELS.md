# Настройка GitHub Models

Этот документ описывает подключение GitHub Models к проекту `dead-regulations-detector`.

## Когда использовать

GitHub Models можно использовать как альтернативный AI-провайдер для анализа документов.

## Получение токена

1. Откройте `https://github.com/settings/tokens`
2. Создайте `Personal Access Token`
3. Сохраните токен в безопасном месте

Права доступа и лимиты зависят от настроек аккаунта и текущих правил GitHub.

## Настройка в проекте

Добавьте в `.env`:

```bash
AI_PROVIDER=github
GITHUB_TOKEN=ghp_...
GITHUB_MODEL=gpt-4o-mini
```

## Проверка подключения

```bash
cd ~/dead-regulations-detector
source venv/bin/activate
python src/nlp/ai_client.py
```

Ожидаемый результат: сообщение об успешном доступе к API выбранного провайдера.

## Полезные ссылки

- GitHub Models: `https://github.com/marketplace/models`
- GitHub Tokens: `https://github.com/settings/tokens`
- Документация: `https://docs.github.com/en/github-models`
