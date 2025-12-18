import asyncio
import logging
import time
from typing import Dict, Optional
from uuid import uuid4

import httpx
from app.core.config import settings
from app.core.db import SessionLocal
from fastapi import APIRouter, HTTPException, Request
from openai import AsyncOpenAI
from sqlalchemy import text

router = APIRouter(tags=["telegram"], prefix="/telegram")

logger = logging.getLogger(__name__)

# In-memory best-effort cache for threads (still persisted in DB)
user_threads_cache: Dict[int, str] = {}

TEXT_LIMIT = 4000
WEBHOOK_TIMEOUT = 25  # seconds

_webhook_status: Optional[str] = None


def _ensure_openai_client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")
    return AsyncOpenAI(api_key=settings.openai_api_key, timeout=20)


def _ensure_bot_token() -> str:
    token = settings.telegram_bot_token
    if not token:
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN is not set")
    return token


def _ensure_agent_id() -> str:
    agent_id = settings.hr_agent_id
    if not agent_id:
        raise HTTPException(status_code=500, detail="HR_AGENT_ID is not set")
    return agent_id


def _check_internal_token(request: Request) -> None:
    if not settings.internal_api_token:
        raise HTTPException(status_code=401, detail="INTERNAL_API_TOKEN not set")
    header = request.headers.get("x-internal-token")
    if not header or header != settings.internal_api_token:
        raise HTTPException(status_code=401, detail="unauthorized")


async def _get_or_create_thread(client: AsyncOpenAI, chat_id: int) -> str:
    cached = user_threads_cache.get(chat_id)
    if cached:
        return cached

    async with SessionLocal() as session, session.begin():
        res = await session.execute(
            text("SELECT thread_id FROM telegram_users WHERE chat_id = :cid"),
            {"cid": chat_id},
        )
        row = res.first()
        if row and row[0]:
            user_threads_cache[chat_id] = row[0]
            return row[0]

        thread = await client.beta.threads.create()
        thread_id = thread.id
        await session.execute(
            text(
                """
                INSERT INTO telegram_users (chat_id, thread_id, updated_at)
                VALUES (:cid, :tid, NOW())
                ON CONFLICT (chat_id) DO UPDATE
                SET thread_id = EXCLUDED.thread_id, updated_at = NOW()
                """
            ),
            {"cid": chat_id, "tid": thread_id},
        )
        user_threads_cache[chat_id] = thread_id
        return thread_id


async def _mark_processed(update_id: int) -> bool:
    """Return True if this update_id is new and marked, False if already processed."""
    async with SessionLocal() as session, session.begin():
        res = await session.execute(
            text(
                """
                INSERT INTO processed_updates (update_id)
                VALUES (:uid)
                ON CONFLICT DO NOTHING
                RETURNING update_id
                """
            ),
            {"uid": update_id},
        )
        row = res.first()
        return bool(row)


async def send_to_agent(client: AsyncOpenAI, chat_id: int, text_msg: str) -> str:
    thread_id = await _get_or_create_thread(client, chat_id)

    await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=text_msg,
    )

    run = await client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=_ensure_agent_id(),
    )

    max_iterations = 10  # Защита от бесконечных циклов
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run.id
        )
        
        if run.status == "completed":
            break
        elif run.status in {"failed", "cancelled", "expired"}:
            logger.warning(f"Run {run.id} ended with status: {run.status}")
            return "⚠️ Не удалось получить ответ от агента. Попробуйте позже."
        elif run.status == "requires_action":
            # Assistant пытается вызвать функции - НО у нас нет их реализации!
            # Это означает, что Assistant настроен неправильно
            logger.error(
                "Assistant requires_action but no tool handlers configured",
                extra={"run_id": run.id, "thread_id": thread_id}
            )
            # Отменяем run, чтобы не зависнуть
            await client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run.id)
            return (
                "⚠️ Бот пытается использовать инструменты, но они не настроены. "
                "Обратитесь к администратору для настройки интеграций."
            )
        
        await asyncio.sleep(0.5)

    if iteration >= max_iterations:
        logger.warning(f"Run {run.id} exceeded max iterations")
        return "⏳ Обработка занимает слишком много времени. Попробуйте позже."

    messages = await client.beta.threads.messages.list(
        thread_id=thread_id, order="desc", limit=5
    )
    for msg in messages.data:
        if msg.role == "assistant" and msg.content:
            parts = []
            for part in msg.content:
                if hasattr(part, "text") and part.text:
                    parts.append(part.text.value)
            if parts:
                return "\n".join(parts)
    return "⚠️ Агент не вернул текст ответа."


async def send_telegram_message(token: str, chat_id: int, text_msg: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text_msg},
            )
    except Exception as exc:  # pragma: no cover - optional log only
        logger.warning("Failed to send Telegram reply: %s", exc)


async def set_telegram_webhook(auto: bool = False) -> dict[str, object]:
    token = _ensure_bot_token()
    if not settings.backend_public_url:
        raise HTTPException(status_code=400, detail="BACKEND_PUBLIC_URL is not set")

    url = settings.backend_public_url.rstrip("/") + "/telegram/webhook"
    payload = {"url": url}
    
    # ВАЖНО: НЕ используем webhook_secret - Telegram иногда падает с ним
    # if settings.webhook_secret:
    #     payload["secret_token"] = settings.webhook_secret

    status = "error"
    response_json: dict[str, object] = {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/setWebhook", json=payload
            )
            response_json = resp.json() if resp.content else {}
            ok = resp.status_code == 200 and response_json.get("ok")
            status = "ok" if ok else f"fail:{resp.status_code}"
            
            # Дополнительная проверка что webhook реально установлен
            if ok:
                verify_resp = await client.get(
                    f"https://api.telegram.org/bot{token}/getWebhookInfo"
                )
                verify_data = verify_resp.json() if verify_resp.content else {}
                actual_url = verify_data.get("result", {}).get("url")
                if actual_url != url:
                    status = f"fail:url_mismatch"
                    logger.warning(f"Webhook URL mismatch: expected {url}, got {actual_url}")
    except Exception as exc:  # pragma: no cover - log only
        response_json = {"ok": False, "description": str(exc)}
        status = f"error:{exc}"

    global _webhook_status
    _webhook_status = status

    if auto:
        if status != "ok":
            logger.warning("Auto setWebhook failed: %s", status)
        else:
            logger.info("Auto setWebhook succeeded")
        return {"status": status, "telegram_response": response_json}

    if status != "ok":
        raise HTTPException(status_code=500, detail=response_json)
    return response_json


def get_webhook_status() -> Optional[str]:
    return _webhook_status


@router.post("/set-webhook")
async def set_webhook_endpoint(request: Request):
    _check_internal_token(request)
    return await set_telegram_webhook(auto=False)


@router.get("/webhook-status")
async def webhook_status_endpoint():
    """Публичный endpoint для проверки статуса webhook."""
    token = _ensure_bot_token()
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.telegram.org/bot{token}/getWebhookInfo"
            )
            data = resp.json() if resp.content else {}
            result = data.get("result", {})
            
            expected_url = (
                settings.backend_public_url.rstrip("/") + "/telegram/webhook"
                if settings.backend_public_url
                else None
            )
            
            return {
                "webhook_set": bool(result.get("url")),
                "webhook_url": result.get("url"),
                "expected_url": expected_url,
                "url_matches": result.get("url") == expected_url,
                "pending_updates": result.get("pending_update_count", 0),
                "last_error_message": result.get("last_error_message"),
                "status": get_webhook_status(),
            }
    except Exception as exc:
        return {
            "webhook_set": False,
            "error": str(exc),
            "status": "error",
        }


@router.post("/webhook")
async def telegram_webhook(request: Request):
    request_id = str(uuid4())
    started = time.perf_counter()
    chat_id: Optional[int] = None
    thread_id: Optional[str] = None
    update_id: Optional[int] = None
    outcome = "ok"

    try:
        token = _ensure_bot_token()
        client = _ensure_openai_client()

        update = await request.json()
        update_id = update.get("update_id")
        if update_id is None:
            return {"ok": True}

        # Idempotency check
        is_new = await _mark_processed(update_id)
        if not is_new:
            outcome = "duplicate"
            return {"ok": True}

        message = update.get("message") or update.get("edited_message")
        if not message:
            outcome = "no_message"
            return {"ok": True}

        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text_msg = message.get("text") or ""

        if not chat_id or not text_msg:
            outcome = "no_chat_or_text"
            return {"ok": True}

        if len(text_msg) > TEXT_LIMIT:
            await send_telegram_message(
                token,
                chat_id,
                "Сообщение слишком длинное. Пожалуйста, разделите на части.",
            )
            outcome = "too_long"
            return {"ok": True}

        async def process() -> str:
            nonlocal thread_id
            thread_id = await _get_or_create_thread(client, chat_id=chat_id)
            return await send_to_agent(client, chat_id=chat_id, text_msg=text_msg)

        try:
            reply = await asyncio.wait_for(process(), timeout=WEBHOOK_TIMEOUT)
        except asyncio.TimeoutError:
            outcome = "timeout"
            reply = "⏳ Ответ занимает дольше обычного. Попробуйте ещё раз."
        except Exception as exc:  # pragma: no cover
            outcome = "openai_error"
            logger.warning(
                "Telegram processing error",
                extra={
                    "event": "telegram_webhook",
                    "request_id": request_id,
                    "update_id": update_id,
                    "chat_id": chat_id,
                    "thread_id": thread_id,
                    "outcome": outcome,
                    "error": str(exc),
                },
            )
            reply = "⚠️ Сейчас не получается ответить. Попробуйте позже."

        await send_telegram_message(token, chat_id, reply)
    except Exception as exc:  # pragma: no cover - always ack
        outcome = "error"
        logger.warning(
            "Telegram webhook handling error",
            extra={
                "event": "telegram_webhook",
                "request_id": request_id,
                "update_id": update_id,
                "chat_id": chat_id,
                "thread_id": thread_id,
                "outcome": outcome,
                "error": str(exc),
            },
        )
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "webhook handled",
            extra={
                "event": "telegram_webhook",
                "request_id": request_id,
                "update_id": update_id,
                "chat_id": chat_id,
                "thread_id": thread_id,
                "duration_ms": duration_ms,
                "outcome": outcome,
            },
        )
    return {"ok": True}
