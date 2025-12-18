import logging
from contextlib import asynccontextmanager

import httpx
from app.core.config import settings
from app.core.db import check_database, engine, ensure_telegram_tables
from app.tools.internal import router as jobs_router
from app.tools.router import router as tools_router
from app.tools.telegram_webhook import router as telegram_router
from app.tools.telegram_webhook import set_telegram_webhook
from app.tools.webhook import router as webhook_router
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", tags=["health"])
async def health() -> dict[str, object]:
    db_ok = True
    try:
        await check_database()
    except Exception as exc:  # pragma: no cover - log only
        db_ok = False
        logger.warning("Database health check failed: %s", exc)

    return {
        "ok": db_ok,
        "env": settings.app_env,
        "public_url": settings.backend_public_url,
        "commit_sha": settings.commit_sha,
        "db_ok": db_ok,
    }


@router.get("/ready", tags=["health"])
async def ready() -> dict[str, str]:
    try:
        await check_database()
    except Exception as exc:  # pragma: no cover
        logger.warning("Ready check failed: %s", exc)
        raise HTTPException(status_code=503, detail="db not ready")
    return {"status": "ok"}


async def send_startup_notify(webhook_status: str | None = None) -> None:
    token = settings.telegram_bot_token
    chat_id = settings.telegram_admin_chat_id

    if not token or not chat_id:
        logger.info(
            "Startup notify skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_ADMIN_CHAT_ID not set"
        )
        return

    if token.lower().startswith(("your_", "dummy")):
        logger.info("Startup notify skipped: TELEGRAM_BOT_TOKEN looks like placeholder")
        return

    text = "\n".join(
        [
            "✅ Backend deployed",
            f"env: {settings.app_env}",
            f"commit: {settings.commit_sha or 'unknown'}",
            f"url: {settings.backend_public_url or 'n/a'}",
            f"setWebhook: {webhook_status or 'n/a'}",
        ]
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
    except Exception as exc:  # pragma: no cover - log only
        logger.warning("Startup notify failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure DB reachable on startup
    await check_database()
    await ensure_telegram_tables()
    webhook_status: str | None = None
    # Set Telegram webhook automatically in production when public URL provided
    if settings.app_env == "production" and settings.backend_public_url:
        try:
            resp = await set_telegram_webhook(auto=True)
            webhook_status = resp.get("status") if isinstance(resp, dict) else None
        except Exception as exc:  # pragma: no cover - log only
            webhook_status = f"error:{exc}"
            logger.warning("Auto setWebhook failed: %s", exc)
        await send_startup_notify(webhook_status=webhook_status)
    yield
    await engine.dispose()


# Configure logging level from settings
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(tools_router)
app.include_router(webhook_router)
app.include_router(telegram_router)
app.include_router(jobs_router)
