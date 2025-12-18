# Деплой на Render.com (пошагово)

## 1. Зайди на Render
- Открой https://render.com
- Sign in with GitHub
- Авторизуй доступ к репозиторию `TakoVHS/hr-autopilot-telegram`

## 2. Создай сервис из Blueprint
- Dashboard → New → Blueprint
- Выбери репозиторий: `TakoVHS/hr-autopilot-telegram`
- Render прочитает `render.yaml` и создаст:
  - PostgreSQL Database (free)
  - Backend Web Service (free)
  - (Bot Worker можно отключить, если используешь webhook)

## 3. Добавь Environment Variables
В Settings → Environment для **hr-autopilot-backend** добавь:

```
TELEGRAM_BOT_TOKEN=<ваш_токен>
TELEGRAM_ADMIN_CHAT_ID=<ваш_chat_id>
OPENAI_API_KEY=<ваш_openai_ключ>
HR_AGENT_ID=asst_opxBoyF6dFugPJVvW8pXMEoX
INTERNAL_API_TOKEN=bwiQORS9/og2v1klOEN8L8HukQxmUDoUg67jdxFzj1k
WEBHOOK_SECRET=whsec_bwiQORS9/og2v1klOEN8L8HukQxmUDoUg67jdxFzj1k=
BACKEND_PUBLIC_URL=https://hr-autopilot-telegram-yx67.onrender.com
APP_ENV=production
RUN_MIGRATIONS_ON_START=1
BOT_TOKEN=8543601304:AAFRwLVFmi4Rv2TPp42h0mPtKGC57eJzv1U
```

⚠️ **ВАЖНО:** `DATABASE_URL` НЕ добавляй вручную — Render подставит автоматически из PostgreSQL DB.

## 4. Deploy
- Нажми "Create Blueprint" или "Deploy"
- Подожди 5-7 минут (первый деплой)
- Проверь логи: должно быть "Application startup complete"

## 5. Проверь Health
```bash
curl -sk https://hr-autopilot-telegram-yx67.onrender.com/health
```
Ожидаешь: `{"ok":true,"env":"production","public_url":"https://hr-autopilot-telegram-yx67.onrender.com",...}`

## 6. Поставь Telegram Webhook
```bash
curl -s -H "x-internal-token: <ваш_INTERNAL_API_TOKEN>" \
  -X POST "https://hr-autopilot-telegram-yx67.onrender.com/telegram/set-webhook"
```

## 7. Проверь Webhook у Telegram
```bash
curl -s "https://api.telegram.org/bot<ваш_TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```
Должно быть:
- `"url": "https://hr-autopilot-telegram-yx67.onrender.com/telegram/webhook"`
- `"last_error_message"` пустой или отсутствует

## 8. E2E Тест
- Напиши боту в Telegram: `/start`
- Должен прийти ответ от OpenAI агента
- В логах Render должна быть запись с `outcome=ok`

## 9. Автодеплой
- При пуше в `main` Render автоматически пересобирает сервис
- Если настроишь `RENDER_BACKEND_HOOK` в GitHub Secrets, GitHub Actions тоже будет триггерить деплой

---

## Troubleshooting

### "Free instance will spin down with inactivity"
- Это норма для Render Free Tier
- Первый запрос разбудит сервис за ~30 сек
- Для Telegram webhook это приемлемо

### "Database connection failed"
- Проверь, что PostgreSQL DB создалась
- DATABASE_URL должен быть автоматически подставлен Render

### "Webhook not receiving updates"
- Проверь `getWebhookInfo` — url должен быть на `.onrender.com`
- Если там старый URL — заново выполни шаг 6

### "OpenAI error"
- Проверь в OpenAI Platform → Assistants → скопируй правильный ID
- Должен быть `asst_opxBoyF6dFugPJVvW8pXMEoX`
- Обнови переменную в Render Settings
