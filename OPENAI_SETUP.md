# Настройка OpenAI

Этот документ описывает подключение OpenAI к проекту `dead-regulations-detector`.

## Когда это нужно

OpenAI API требуется для AI-анализа и дополнительных объяснений в результатах.

Без `OPENAI_API_KEY` система продолжает работать в режиме rule-based детекции.

## Получение API-ключа

1. Откройте `https://platform.openai.com/api-keys`
2. Войдите в аккаунт OpenAI
3. Создайте новый ключ
4. Сохраните ключ в безопасном месте

## Настройка через `.env`

```bash
cd ~/dead-regulations-detector
nano .env
```

Укажите параметры:

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-ваш-ключ
OPENAI_MODEL=gpt-4
```

Допустимо использовать и другие модели, поддерживаемые вашим аккаунтом.

## Настройка через UI

1. Откройте `http://localhost:8501`
2. В боковой панели выберите `AI Provider = openai`
3. Введите `OpenAI API Key` при необходимости

## Проверка подключения

```bash
cd ~/dead-regulations-detector
source venv/bin/activate
python src/nlp/ai_client.py
```

Ожидаемый результат: сообщение об успешном доступе к API выбранного провайдера.

## Переключение провайдера

Через `.env`:

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

или:

```bash
AI_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-...
```

или:

```bash
AI_PROVIDER=none
```

## Частые проблемы

`401 Unauthorized`

- Неверный или отозванный ключ
- Неправильный формат значения в `.env`

`429 Too Many Requests`

- Превышен лимит по запросам/квоте
- Требуется повторная попытка позже

`413 Payload Too Large`

- Запрос слишком большой
- Уменьшите объем входного текста
