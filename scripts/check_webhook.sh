#!/bin/bash

# Автоматическая проверка и восстановление Telegram webhook
# Используй этот скрипт в cron или вручную при проблемах

set -e

BACKEND_URL="https://hr-autopilot-backend-yx67.onrender.com"
INTERNAL_TOKEN="03e20ae0ba966762a89f247ebe889d871ffa7241a6959ad2cb37b0f4752ce544"

echo "🔍 Проверка статуса webhook..."

# Проверяем статус через наш API
STATUS=$(curl -s "${BACKEND_URL}/telegram/webhook-status" | jq -r '.url_matches')

if [ "$STATUS" == "true" ]; then
    echo "✅ Webhook настроен правильно!"
    curl -s "${BACKEND_URL}/telegram/webhook-status" | jq '{webhook_url, pending_updates, last_error_message}'
    exit 0
fi

echo "⚠️ Webhook не установлен или неправильный URL"
echo ""
echo "🔧 Восстанавливаю webhook..."

# Устанавливаем webhook
RESULT=$(curl -s -H "x-internal-token: ${INTERNAL_TOKEN}" \
    -X POST "${BACKEND_URL}/telegram/set-webhook")

echo "$RESULT" | jq

# Проверяем результат
if echo "$RESULT" | jq -e '.ok == true' > /dev/null; then
    echo ""
    echo "✅ Webhook успешно восстановлен!"
    
    # Финальная проверка
    sleep 2
    curl -s "${BACKEND_URL}/telegram/webhook-status" | jq
else
    echo ""
    echo "❌ Не удалось установить webhook"
    echo "Проверь логи: https://dashboard.render.com → hr-autopilot-backend-yx67 → Logs"
    exit 1
fi
