# 🚨 СРОЧНО: Бот не отвечает — инструкция по исправлению

## Проблема
Бот выдаёт ошибки:
- `⏳ Ответ занимает дольше обычного. Попробуйте ещё раз.` — таймаут OpenAI (>25 сек)
- `⚠️ Сейчас не получается ответить. Попробуйте позже.` — ошибка OpenAI API

## Причина
**OpenAI Assistant не настроен или не имеет доступа к инструментам (tools).**

## ✅ Решение (5 минут)

### Шаг 1: Открой OpenAI Platform
```
https://platform.openai.com/assistants
```

### Шаг 2: Найди ассистента
```
ID: asst_opxBoyF6dFugPJVvW8pXMEoX
```

### Шаг 3: Проверь наличие TOOLS (критично!)

В разделе **Functions** должно быть **4 инструмента**:

#### 1. create_candidate_in_crm
```json
{
  "name": "create_candidate_in_crm",
  "description": "Создать карточку кандидата в CRM",
  "parameters": {
    "type": "object",
    "properties": {
      "full_name": {"type": "string", "description": "Полное имя кандидата"},
      "phone": {"type": "string", "description": "Телефон"},
      "email": {"type": "string", "description": "Email (опционально)"},
      "source": {
        "type": "string",
        "enum": ["telegram", "avito", "yandex", "other"],
        "description": "Источник кандидата"
      },
      "vacancy_key": {
        "type": "string",
        "enum": ["courier_walk_bike", "courier_auto", "picker_darkstore", "seamstress_factory", "callcenter_operator"],
        "description": "Ключ вакансии"
      },
      "city": {"type": "string", "description": "Город кандидата"},
      "notes": {"type": "string", "description": "Дополнительные заметки"}
    },
    "required": ["full_name", "source", "vacancy_key", "city"]
  }
}
```

#### 2. update_candidate_status
```json
{
  "name": "update_candidate_status",
  "description": "Обновить статус кандидата",
  "parameters": {
    "type": "object",
    "properties": {
      "candidate_id": {"type": "integer", "description": "ID кандидата"},
      "new_status": {
        "type": "string",
        "enum": ["new", "screening", "qualified", "rejected", "scheduled", "escalated"],
        "description": "Новый статус"
      },
      "reason_code": {
        "type": "string",
        "enum": ["wrong_city", "underage", "no_smartphone", "no_work_docs", "no_drivers_license", "no_required_experience", "schedule_mismatch", "candidate_declined", "vip_or_risk", "tool_error"],
        "description": "Код причины (для rejected/escalated)"
      },
      "notes": {"type": "string", "description": "Примечание к статусу"}
    },
    "required": ["candidate_id", "new_status"]
  }
}
```

#### 3. schedule_interview
```json
{
  "name": "schedule_interview",
  "description": "Назначить интервью с кандидатом",
  "parameters": {
    "type": "object",
    "properties": {
      "candidate_id": {"type": "integer", "description": "ID кандидата"},
      "vacancy_key": {"type": "string", "description": "Ключ вакансии"},
      "scheduled_at": {"type": "string", "description": "Дата и время в ISO формате"},
      "duration_minutes": {"type": "integer", "description": "Длительность в минутах"},
      "location": {"type": "string", "description": "Место проведения"},
      "notes": {"type": "string", "description": "Заметки к интервью"}
    },
    "required": ["candidate_id"]
  }
}
```

#### 4. escalate_to_human
```json
{
  "name": "escalate_to_human",
  "description": "Эскалировать случай живому HR",
  "parameters": {
    "type": "object",
    "properties": {
      "candidate_id": {"type": "integer", "description": "ID кандидата"},
      "reason": {"type": "string", "description": "Причина эскалации"},
      "priority": {
        "type": "string",
        "enum": ["low", "normal", "high", "urgent"],
        "description": "Приоритет"
      }
    },
    "required": ["reason"]
  }
}
```

### Шаг 4: Укажи базовый URL для tools
В разделе **Actions** → **Base URL**:
```
https://hr-autopilot-backend-yx67.onrender.com/tools
```

### Шаг 5: Добавь аутентификацию (если требуется)
**Authentication:** None (публичный endpoint)

### Шаг 6: Обнови Instructions
Скопируй весь текст из: `docs/prompts/hr_agent_system.md`

Вставь в поле **Instructions** и сохрани.

---

## 🧪 Тестирование после исправления

### 1. Базовый тест
```
Ты → /start
Бот → [приветствие на русском]
```

### 2. Тест создания кандидата
```
Ты → Хочу курьером, Москва, мне 20, есть iPhone и паспорт
Бот → [создаст кандидата и предложит интервью]
```

### 3. Проверь логи Render
```
https://dashboard.render.com → hr-autopilot-backend-yx67 → Logs
```

Ищи:
```json
{
  "event": "telegram_webhook",
  "outcome": "ok",
  "duration_ms": <5000
}
```

Если `outcome: "timeout"` или `outcome: "openai_error"` — проблема осталась.

---

## 📊 Диагностика

### Проверь статус сервиса:
```bash
curl -sk https://hr-autopilot-backend-yx67.onrender.com/health | jq
```

**Ожидается:**
```json
{"ok": true, "db_ok": true}
```

### Проверь webhook:
```bash
curl -s "https://api.telegram.org/bot8543601304:AAFRwLVFmi4Rv2TPp42h0mPtKGC57eJzv1U/getWebhookInfo" | jq '.result.url'
```

**Ожидается:**
```
"https://hr-autopilot-backend-yx67.onrender.com/telegram/webhook"
```

---

## ⚠️ Если проблема не решается

### 1. OpenAI Assistant висит (requires_action)
Если агент застревает в статусе `requires_action`:
- Проверь, что все 4 инструмента добавлены
- Проверь Base URL: `https://hr-autopilot-backend-yx67.onrender.com/tools`
- Проверь, что endpoints доступны:
  ```bash
  curl -X POST https://hr-autopilot-backend-yx67.onrender.com/tools/create_candidate_in_crm \
    -H "Content-Type: application/json" \
    -d '{"full_name":"Test","source":"telegram","vacancy_key":"courier_walk_bike","city":"Москва"}'
  ```

### 2. Таймаут 25 секунд
Причины:
- OpenAI Assistant долго обрабатывает (модель gpt-4o может быть медленной)
- Render Free Tier просыпается (первые 30-60 сек)
- Ассистент застрял в цикле вызовов tools

**Решение:**
- Используй модель `gpt-4o-mini` для быстрого ответа
- Увеличь таймаут в коде (не рекомендуется, Telegram ждёт <30 сек)

### 3. Ошибка "openai_error"
Проверь логи Render на наличие:
```
openai.RateLimitError
openai.APIConnectionError
openai.AuthenticationError
```

**Решение:**
- Проверь баланс OpenAI: https://platform.openai.com/usage
- Проверь OPENAI_API_KEY в Render Dashboard → Environment

---

## 🎯 Быстрый чеклист

- [ ] OpenAI Platform → Assistants → `asst_opxBoyF6dFugPJVvW8pXMEoX`
- [ ] Проверил наличие 4 функций (create_candidate, update_status, schedule_interview, escalate)
- [ ] Base URL: `https://hr-autopilot-backend-yx67.onrender.com/tools`
- [ ] Instructions обновлены из `hr_agent_system.md`
- [ ] Webhook установлен (getWebhookInfo показывает URL)
- [ ] Протестировал `/start` → получил ответ на русском
- [ ] Логи Render показывают `outcome: "ok"`

---

## 📞 Контакты и ссылки

- **OpenAI Platform:** https://platform.openai.com/assistants
- **Render Dashboard:** https://dashboard.render.com
- **Assistant ID:** `asst_opxBoyF6dFugPJVvW8pXMEoX`
- **Системный промпт:** `docs/prompts/hr_agent_system.md`
- **Tools docs:** `docs/OPENAI_ASSISTANT_SETUP.md`
