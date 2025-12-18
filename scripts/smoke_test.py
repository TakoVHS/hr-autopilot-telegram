#!/usr/bin/env python3
"""Simple smoke test for backend and webhook setup.

- Waits for /health to be ready
- Calls /telegram/set-webhook if INTERNAL_API_TOKEN is set
- Sends report to Telegram admin chat if TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_CHAT_ID are set
"""

import asyncio
import os
import sys
import time
from typing import Any, Tuple

import httpx

DEFAULT_BACKEND_URL = "http://localhost:8000"


def build_backend_url() -> str:
    public = os.getenv("BACKEND_PUBLIC_URL")
    if public:
        return public.rstrip("/")
    explicit = os.getenv("BACKEND_URL")
    if explicit:
        return explicit.rstrip("/")
    host = os.getenv("BACKEND_HOST", "localhost")
    port = os.getenv("BACKEND_PORT", "8000")
    return f"http://{host}:{port}"


async def wait_for_health(
    client: httpx.AsyncClient, url: str, timeout: int = 60
) -> Tuple[bool, Any]:
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            resp = await client.get(f"{url}/health", timeout=5)
            if resp.status_code == 200:
                return True, resp.json()
            last_error = f"status={resp.status_code}"
        except Exception as exc:  # pragma: no cover - diagnostic only
            last_error = str(exc)
        await asyncio.sleep(2)
    return False, last_error


async def call_set_webhook(
    client: httpx.AsyncClient, url: str, internal_token: str | None
) -> Tuple[bool, str]:
    if not internal_token:
        return False, "INTERNAL_API_TOKEN not set"

    headers = {"x-internal-token": internal_token}
    try:
        resp = await client.post(f"{url}/telegram/set-webhook", headers=headers, timeout=15)
        if resp.status_code == 200:
            return True, resp.text
        return False, f"status={resp.status_code}, body={resp.text}"
    except Exception as exc:  # pragma: no cover - diagnostic only
        return False, str(exc)


async def send_telegram_report(text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    if not token or not chat_id:
        print("[info] Telegram not configured; report not sent")
        print(text)
        return

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
            if resp.status_code == 200:
                print("[info] Report sent to Telegram")
            else:
                print(
                    f"[warn] Telegram responded with {resp.status_code}: {resp.text}"
                )
        except Exception as exc:  # pragma: no cover - optional
            print(f"[warn] Failed to send Telegram report: {exc}")


async def main() -> int:
    backend_url = build_backend_url()
    internal_token = os.getenv("INTERNAL_API_TOKEN")

    async with httpx.AsyncClient() as client:
        health_ok, health_info = await wait_for_health(client, backend_url)
        webhook_ok, webhook_info = await call_set_webhook(
            client, backend_url, internal_token
        )

    report_lines = [
        "🚦 Smoke test",
        f"backend: {backend_url}",
        f"health: {'✅' if health_ok else '❌'} {health_info}",
        f"set-webhook: {'✅' if webhook_ok else '❌'} {webhook_info}",
        "logs: docker compose logs -f --tail=200 backend",
    ]
    report_text = "\n".join(report_lines)
    print(report_text)
    await send_telegram_report(report_text)

    # Exit code signals failure if any critical check failed
    return 0 if health_ok and webhook_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
