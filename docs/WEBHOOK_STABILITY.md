# Решение проблемы с постоянным падением webhook

## Проблема
Telegram webhook сбрасывается после каждого деплоя/перезапуска Render.

## Причины
1. **Render Free Tier засыпает** → при пробуждении webhook не восстанавливается
2. **WEBHOOK_SECRET** может вызывать ошибки в Telegram API (некоторые символы не поддерживаются)
3. **Автоустановка при старте** работает, но может фейлить по разным причинам

## Решения

### ✅ Решение 1: Автоматическая проверка (реализовано)

**Новый endpoint для проверки:**
```bash
curl -s https://hr-autopilot-backend-yx67.onrender.com/telegram/webhook-status | jq
```

**Автоматический скрипт:**
```bash
./scripts/check_webhook.sh
```

Скрипт:
- ✅ Проверяет статус webhook
- ✅ Автоматически восстанавливает если сброшен
- ✅ Можно добавить в cron для регулярной проверки

### ✅ Решение 2: Улучшенная автоустановка (реализовано)

**Изменения в коде:**
1. Удалён `WEBHOOK_SECRET` (вызывал проблемы)
2. Добавлена дополнительная проверка после установки
3. Улучшено логирование ошибок

### ✅ Решение 3: Render Cron Job (рекомендуется)

**Настрой в Render Dashboard:**

1. Открой: https://dashboard.render.com
2. Создай новый **Cron Job** (или используй существующий сервис)
3. Команда:
   ```bash
   curl -s -H "x-internal-token: $INTERNAL_API_TOKEN" \
     -X POST "$BACKEND_PUBLIC_URL/telegram/set-webhook"
   ```
4. Расписание: `*/15 * * * *` (каждые 15 минут)

**Переменные окружения для Cron Job:**
- `BACKEND_PUBLIC_URL`: `https://hr-autopilot-backend-yx67.onrender.com`
- `INTERNAL_API_TOKEN`: `03e20ae0ba966762a89f247ebe889d871ffa7241a6959ad2cb37b0f4752ce544`

### ✅ Решение 4: Вручную при проблемах

**Быстрое восстановление:**
```bash
# Способ 1: Через наш API
curl -s -H "x-internal-token: 03e20ae0ba966762a89f247ebe889d871ffa7241a6959ad2cb37b0f4752ce544" \
  -X POST "https://hr-autopilot-backend-yx67.onrender.com/telegram/set-webhook" | jq

# Способ 2: Напрямую через Telegram API
curl -s -X POST "https://api.telegram.org/bot8543601304:AAFRwLVFmi4Rv2TPp42h0mPtKGC57eJzv1U/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://hr-autopilot-backend-yx67.onrender.com/telegram/webhook"}' | jq
```

**Проверка статуса:**
```bash
# Через наш API (рекомендуется)
curl -s https://hr-autopilot-backend-yx67.onrender.com/telegram/webhook-status | jq

# Напрямую через Telegram API
curl -s "https://api.telegram.org/bot8543601304:AAFRwLVFmi4Rv2TPp42h0mPtKGC57eJzv1U/getWebhookInfo" | jq
```

## Что делать при падении

### Шаг 1: Проверь статус
```bash
./scripts/check_webhook.sh
```

### Шаг 2: Если скрипт не помог
1. Открой Render Logs: https://dashboard.render.com → hr-autopilot-backend-yx67 → Logs
2. Ищи строки с `setWebhook` или `Auto setWebhook failed`
3. Проверь ошибки

### Шаг 3: Ручное восстановление
```bash
curl -s -H "x-internal-token: 03e20ae0ba966762a89f247ebe889d871ffa7241a6959ad2cb37b0f4752ce544" \
  -X POST "https://hr-autopilot-backend-yx67.onrender.com/telegram/set-webhook" | jq
```

### Шаг 4: Если всё равно не работает
Возможные причины:
- Render Free Tier засыпает → подожди 30-60 сек и повтори
- BACKEND_PUBLIC_URL неправильный → проверь в Render Dashboard → Environment
- Telegram API недоступен → проверь https://status.telegram.org

## Предотвращение проблем

### Рекомендации:
1. ✅ **Используй Render Cron Job** (каждые 15 минут проверяет webhook)
2. ✅ **Мониторь webhook-status endpoint** регулярно
3. ✅ **Настрой UptimeRobot** или аналогичный сервис для пинга `/health`
4. ⚠️ **Free Tier спит через 15 мин** → первый запрос после сна займёт 30-60 сек

### Для продакшена:
- Апгрейдни на **Render Starter** ($7/мес) → не засыпает
- Webhook будет стабильно работать 24/7

## Проверка после деплоя

После каждого деплоя на Render:
```bash
# 1. Подожди 1-2 минуты пока сервис запустится
sleep 120

# 2. Проверь статус
curl -s https://hr-autopilot-backend-yx67.onrender.com/telegram/webhook-status | jq

# 3. Если url_matches = false, восстанови webhook
curl -s -H "x-internal-token: 03e20ae0ba966762a89f247ebe889d871ffa7241a6959ad2cb37b0f4752ce544" \
  -X POST "https://hr-autopilot-backend-yx67.onrender.com/telegram/set-webhook" | jq
```

## Итоговый чеклист

- [x] Удалён WEBHOOK_SECRET (вызывал проблемы)
- [x] Добавлен `/telegram/webhook-status` endpoint
- [x] Создан скрипт `scripts/check_webhook.sh`
- [x] Улучшена автоустановка при старте
- [ ] (Опционально) Настроить Render Cron Job для проверки каждые 15 мин
- [ ] (Опционально) Апгрейд на Render Starter для стабильности

## Команды для быстрого доступа

```bash
# Проверка статуса
curl -s https://hr-autopilot-backend-yx67.onrender.com/telegram/webhook-status | jq

# Восстановление webhook
./scripts/check_webhook.sh

# Или вручную
curl -s -H "x-internal-token: 03e20ae0ba966762a89f247ebe889d871ffa7241a6959ad2cb37b0f4752ce544" \
  -X POST "https://hr-autopilot-backend-yx67.onrender.com/telegram/set-webhook" | jq
```
