import asyncio
import logging
from typing import Dict

import httpx
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from openai import AsyncOpenAI

from config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(
        "Привет! Я HR помощник. Напиши свой вопрос или опиши кандидата — передам в агент и верну ответ."
    )


@dp.message()
async def echo_handler(message: Message):
    await handle_message(message)


async def handle_message(message: Message):
    await message.answer_chat_action("typing")
    reply = await send_to_agent(user_id=message.from_user.id, text=message.text)
    await message.answer(reply)


async def send_startup_notify() -> None:
    token = settings.telegram_token
    chat_id = settings.telegram_admin_chat_id
    if not token or not chat_id:
        logger.info("Startup notify skipped: TELEGRAM_ADMIN_CHAT_ID not set")
        return

    text = "\n".join(
        [
            "✅ Bot started",
            f"env: {settings.app_env}",
            f"commit: {settings.commit_sha or 'unknown'}",
        ]
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client_http:
            await client_http.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
    except Exception as exc:  # pragma: no cover - notification failure should not crash
        logger.warning("Bot startup notify failed: %s", exc)


async def main():
    logger.info("Starting bot...")
    if settings.telegram_token.lower().startswith(("your_", "dummy")):
        logger.warning(
            "Bot token looks placeholder; skip polling. Set TELEGRAM_BOT_TOKEN to run."
        )
        await asyncio.Event().wait()

    await send_startup_notify()
    bot_instance = Bot(token=settings.telegram_token)
    await dp.start_polling(bot_instance)


if __name__ == "__main__":
    asyncio.run(main())

# In-memory mapping user -> OpenAI thread id
user_threads: Dict[int, str] = {}


async def ensure_thread(user_id: int) -> str:
    thread_id = user_threads.get(user_id)
    if thread_id:
        return thread_id
    thread = await client.beta.threads.create()
    user_threads[user_id] = thread.id
    return thread.id


async def send_to_agent(user_id: int, text: str) -> str:
    thread_id = await ensure_thread(user_id)

    await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=text,
    )

    run = await client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=settings.hr_agent_id,
    )

    while True:
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run.id
        )
        if run.status in {"completed", "failed", "cancelled", "expired"}:
            break
        await asyncio.sleep(0.5)

    if run.status != "completed":
        return "⚠️ Не удалось получить ответ от агента. Попробуйте позже."

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
