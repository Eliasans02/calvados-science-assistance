# calvados-science-assistance

Backend-платформа для AI-анализа технических заданий (ТЗ), где:

- **n8n** управляет оркестрацией шагов и агентов;
- **backend** предоставляет независимые API-эндпоинты, хранение данных, отчеты и UI-интеграцию.

Проект не переписан с нуля: существующие блоки загрузки, истории и базового анализа сохранены, а поверх добавлен модульный backend-слой.

## Архитектура (после рефакторинга)

```text
src/
├── core/        # app factory, DI контейнер, middleware
├── api/         # FastAPI entrypoint + роуты
│   └── routes/
├── modules/     # бизнес-логика (анализ, генерация, комплаенс, отчёт)
├── agents/      # независимые agent handlers для n8n/UI
├── data/        # SQLite и репозитории (users/files/results/reports/logs)
├── auth/        # регистрация/логин/сессии/token dependencies
├── ui/          # текущий Streamlit UI (сохранен)
├── utils/       # схемы и вспомогательные адаптеры
├── extraction/  # существующая нормализация PDF/Word/TXT (сохранена)
├── analysis/    # существующий анализатор (сохранен)
├── nlp/         # AI-клиенты (сохранены)
└── metrics/     # статистика (сохранена)
```

## Что перенесено и как сопоставляется

| Было | Стало |
|---|---|
| Монолитный сценарий в UI | UI + отдельные API/agents |
| Встроенная логика анализа | `src/modules/*` + `src/agents/*` |
| Разрозненное хранение | `src/data/db.py` + `src/data/repository.py` (единый слой) |
| Локальный флоу | Внешняя оркестрация через n8n (любой порядок вызовов) |

Сохраненные компоненты:

- `src/extraction/text_extractor.py` — используется для нормализации файлов в `/api/upload`
- `src/ui/app.py` — не удален и не ломался
- существующие тесты по extraction/stats/AI fallback остаются релевантными

## API endpoints

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Данные и пользовательские сценарии
- `POST /api/upload` — загрузка PDF/Word/TXT, сохранение и нормализация, возврат `file_id`
- `GET /api/history` — история загруженных документов
- `GET /api/history/{file_id}` — детали + промежуточные результаты агентов
- `GET /api/report/{file_id}/download?format=md|json|xlsx` — скачивание отчета (включая XLSX по шаблону)
- `GET /api/generation/{file_id}/download` — скачать сгенерированное ТЗ в формате DOCX
- `POST /api/chat` — чат, который вызывает те же agents, что и n8n
- `GET /api/chat/history` — история чата

### Независимые agents endpoints
- `POST /agent/text-analysis`
- `POST /agent/requirement-analysis`
- `POST /agent/structure`
- `POST /agent/generation`
- `POST /agent/recommendation`
- `POST /agent/scoring`
- `POST /agent/compliance`
- `POST /agent/report`

Каждый endpoint может быть вызван отдельно, без жестко заданного backend-pipeline.

## Агенты

- `text_analysis_agent` — размытые формулировки, дубли, логические конфликты
- `requirement_analysis_agent` — отсутствующие разделы и KPI
- `structure_agent` — проверка/построение структуры по шаблону ПЦФ
- `generation_agent` — генерация ТЗ на основе исходного текста (faithful mode) + DOCX export
- `recommendation_agent` — рекомендации + AI-обогащение (executive summary, приоритетные действия)
- `scoring_agent` — scoring по агрегированным результатам агентов
- `compliance_agent` — проверка соответствия грантам/НИОКР
- `report_agent` — финальная сборка отчета из промежуточных результатов

## Взаимодействие backend и n8n

Рекомендуемый поток:

1. `POST /api/upload` → получить `file_id`
2. n8n вызывает нужные `/agent/*` в любом порядке
3. backend сохраняет каждый результат как промежуточный (`agent_results`)
4. `POST /agent/report` формирует итоговый отчёт
5. UI/N8N скачивает отчет через `/api/report/{file_id}/download`

## Данные и логирование

- Файлы: `data/files/`
- Отчеты: `data/reports/`
- XLSX-шаблон оценки ТЗ: `templates/Оценка_ТЗ_шаблон.xlsx`
  - при экспорте заполняются не только баллы (E:K), но и текстовые AI-комментарии/действия (M:W) + прозрачность анализа (X)
- БД: `data/backend.db`
- Логи вызовов API: таблица `api_logs` (request_id, latency, status, user_id)

Все результаты привязаны к `user_id` и при наличии к `file_id`.

## Точки расширения

1. **ML-рекомендации**: `modules/recommendation.py` уже имеет ML-ready контракт.
2. **Scoring model**: заменить stub в `modules/scoring.py` на обучаемую модель.
3. **Domain-specific compliance**: расширить правила в `modules/compliance.py`.
4. **n8n workflows**: собирать разные сценарии (грант, НИОКР, внутренний аудит) без изменений backend.

## AI-рекомендации: включение

Для AI-обогащения рекомендаций настройте любой provider в `.env`:

- `AI_PROVIDER=github` + `GITHUB_TOKEN=...`, или
- `AI_PROVIDER=openai` + `OPENAI_API_KEY=...`, или
- `AI_PROVIDER=openrouter` + `OPENROUTER_API_KEY=...`, или
- `AI_PROVIDER=claude` + `CLAUDE_API_KEY=...`

Если ключ не задан, система продолжает работать в rule-based режиме.

## Запуск

### API backend
```bash
source venv/bin/activate
./run_api.sh
```

Swagger: `http://localhost:8000/docs`

### n8n workflows
Workflow JSON files are in `n8n_workflows/`:

- `full_analysis_workflow.json`
- `quick_analysis_workflow.json`
- `error_notification_workflow.json`

Webhook routes are documented in `n8n_workflows/README.md`.

### Streamlit UI (legacy/preserved)
```bash
source venv/bin/activate
./run.sh
```

В UI (sidebar) можно подключить AI key прямо в веб-интерфейсе:
- выбрать provider (`github/openai/openrouter/claude`);
- вставить API key (действует в текущей web-сессии);
- запускать `recommendation`/`chat` с AI-обогащением без ручного редактирования `.env`.

### Telegram bot
Bot sources and deployment configs are in `bots/`:

- `bots/telegram_bot.py`
- `bots/deploy/telegram-bot.service`
- `bots/Dockerfile`
- `bots/docker-compose.yml`
- `bots/README.md`
