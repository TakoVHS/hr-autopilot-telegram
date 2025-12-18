# HR Autopilot Telegram Bot

Проект автоматизации HR-процессов с использованием Telegram бота.

## Структура проекта

```
.
├── backend/          # FastAPI бэкенд
├── bot/             # Telegram бот (aiogram)
├── .env.example     # Пример конфигурации
├── docker-compose.yml
└── requirements.txt
```

## Технологии

- Python 3.11+
- FastAPI
- aiogram 3.x
- PostgreSQL
- SQLAlchemy (async)
- Alembic
- Docker & Docker Compose

## Установка и запуск

### Локальная разработка

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Заполните необходимые переменные окружения в `.env`

### Запуск с Docker

```bash
docker-compose up -d
```

Сервисы будут доступны:
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

## Переменные окружения

См. файл `.env.example` для списка всех необходимых переменных.

Ключевые:
- `APP_ENV`, `LOG_LEVEL`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`
- `OPENAI_API_KEY`, `HR_AGENT_ID`
- `BACKEND_URL`/`BACKEND_PUBLIC_URL`
- `DATABASE_URL`
- `WEBHOOK_SECRET`

## Разработка

- Backend разрабатывается в директории `backend/`
- Бот разрабатывается в директории `bot/`

## Миграции БД

```bash
# Создание миграции
alembic revision --autogenerate -m "description"

# Применение миграций
alembic upgrade head
```

### Render (один web-сервис)
- Миграции хранятся в backend/alembic. Для применения на Render (web service):
  1. Предпочтительно: Pre-deploy command в Render: `cd backend && alembic upgrade head`.
  2. Либо включить авто-применение на старте, установив env `RUN_MIGRATIONS_ON_START=1` (entrypoint запускает `alembic upgrade head` перед uvicorn).
  3. Локально: `make migrate` (использует `cd backend && alembic upgrade head`).
  4. При разработке миграцию создавайте командой `cd backend && alembic revision --autogenerate -m "..."`.

## Production checklist
- ENV: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`, `OPENAI_API_KEY`, `HR_AGENT_ID`, `DATABASE_URL`, `WEBHOOK_SECRET`, `BACKEND_PUBLIC_URL`, `INTERNAL_API_TOKEN` заданы и не dummy.
- Миграции: либо Render pre-deploy `cd backend && alembic upgrade head`, либо `RUN_MIGRATIONS_ON_START=1`.
- Webhook: POST /telegram/set-webhook (заголовок `x-internal-token: $INTERNAL_API_TOKEN`) или убедитесь, что авто setWebhook в проде с `BACKEND_PUBLIC_URL` отработал.
- Логи: structured в stdout/stderr (Render dashboard или `docker compose logs` локально).

## Troubleshooting
- Логи: Render → Logs; локально `docker compose logs -f backend`.
- Telegram ошибки:
  - 401/404 от Bot API → неверный токен или не подставлен env.
  - 400/403 sendMessage/getChat → бота нет в чате или чат_id неверен.
  - setWebhook fail → проверьте BACKEND_PUBLIC_URL доступен из интернета, WEBHOOK_SECRET.
- OpenAI ошибки/таймауты: в ответ пользователю уйдет краткий fallback; смотрите логи `outcome=openai_error` или `outcome=timeout`.

## Security notes
- Не коммитьте секреты (.env добавлен в .gitignore).
- Проверяйте, что в `.env`/Render env нет placeholder-значений.
- Ограничивайте доступ к /telegram/set-webhook и /jobs/followup заголовком `x-internal-token`.

## Deploy to Oracle Always Free (Docker + Caddy)
1) Создать VM, открыть ingress 80/443, получить public IP.
2) Привязать домен (A record) -> IP (Telegram требует HTTPS).
3) На VM выполнить `scripts/oracle_bootstrap.sh` (устанавливает Docker, готовит /opt/hr-autopilot).
4) Скопировать файлы в /opt/hr-autopilot:
  - infra/docker-compose.prod.yml -> docker-compose.yml
  - infra/Caddyfile -> Caddyfile
  - infra/.env.prod.example -> .env (заполнить секреты)
5) В GitHub Secrets добавить: `GHCR_PAT`, `ORACLE_HOST`, `ORACLE_USER`, `ORACLE_SSH_KEY` (private key), при необходимости TELEGRAM/OPENAI env в .env на VM.
6) Push в main триггерит workflow: билд образа в GHCR и деплой на VM (docker compose pull/up).
7) Проверка:
  - `https://<domain>/health`
  - `curl -H "x-internal-token: $INTERNAL_API_TOKEN" -X POST https://<domain>/telegram/set-webhook`
  - `https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo`
  - Написать боту /start и смотреть `docker compose logs -f`.

Troubleshooting Oracle
- 502/connection refused: проверьте, что docker compose запущен, caddy слушает 80/443, порты открыты в Oracle SG.
- TLS не выдался: DNS A-запись не указывает на IP или Caddy не видит домен.
- Telegram не принимает webhook: нужен HTTPS и доступность <domain>/telegram/webhook.
- OpenAI timeout: см. логи `outcome=openai_error`/`outcome=timeout`.

## Деплой (Render, один Web Service)

- Поднимите один Web Service (backend) и Postgres.
- Обязательные ENV: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `HR_AGENT_ID`, `DATABASE_URL`, `WEBHOOK_SECRET`, `BACKEND_PUBLIC_URL`, `INTERNAL_API_TOKEN`.
- Бот-обновления идут на `POST /telegram/webhook`. При старте в `production` с заданным `BACKEND_PUBLIC_URL` сервис сам вызывает `setWebhook`.
- Ручная установка вебхука: `POST /telegram/set-webhook` с заголовком `x-internal-token: $INTERNAL_API_TOKEN`.
- Follow-up без отдельного воркера: `POST /jobs/followup` c тем же токеном; есть планировщик `.github/workflows/followup.yml` (каждые 30 минут), требует secrets `BACKEND_PUBLIC_URL`, `INTERNAL_API_TOKEN`.

Проверка webhook локально/в проде:
```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=$BACKEND_PUBLIC_URL/telegram/webhook" \
  -d "secret_token=$WEBHOOK_SECRET"
```

GitHub Actions:
- `.github/workflows/ci.yml` — pytest + compileall.
- `.github/workflows/deploy.yml` — Render hooks (если заданы).
- `.github/workflows/followup.yml` — дергает followup-джоб.

## Удобные команды

Используйте `make` из корня:

- `make up` — сборка и запуск docker compose
- `make down` — остановка
- `make logs` — хвост логов
- `make test` — `pytest` для backend/tests (через `venv/bin/python`)
- `make test-strict` — те же тесты, но `PYTHONWARNINGS=error` (ловим новые предупреждения)
- `make smoke` — прогон `scripts/smoke_test.py`
- `make fmt` — `black` + `isort`
