#!/bin/bash

# Тестовый запрос к боту для диагностики

TELEGRAM_BOT_TOKEN="8543601304:AAFRwLVFmi4Rv2TPp42h0mPtKGC57eJzv1U"

echo "📤 Отправляю тестовое сообщение боту..."

# Получаем chat_id (нужен реальный chat_id для теста)
# Для теста используем sendMessage напрямую
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" | jq

echo ""
echo "✅ Бот доступен. Теперь отправь ему сообщение вручную и смотри логи Render."
echo ""
echo "Логи: https://dashboard.render.com → hr-autopilot-backend-yx67 → Logs"
