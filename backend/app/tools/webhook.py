import hashlib
import hmac
import time

from app.core.config import settings
from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(tags=["webhook"])


def _extract_signature(signature: str) -> str | None:
    """Return hex signature value; require scheme v1."""
    for part in signature.split(","):
        part = part.strip()
        if part.startswith("v1="):
            return part.split("=", 1)[1]
    return None


def verify_signature(body: bytes, timestamp: str, signature: str, secret: str) -> bool:
    sig = _extract_signature(signature)
    if not sig:
        return False

    # replay protection: 5 minutes
    try:
        if abs(time.time() - int(timestamp)) > 300:
            return False
    except ValueError:
        return False

    payload = f"{timestamp}.{body.decode('utf-8')}".encode()
    computed = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, sig)


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    webhook_id: str = Header(..., alias="webhook-id"),
    webhook_timestamp: str = Header(..., alias="webhook-timestamp"),
    webhook_signature: str = Header(..., alias="webhook-signature"),
):
    secret = settings.webhook_secret
    if not secret:
        raise HTTPException(status_code=500, detail="WEBHOOK_SECRET is not set")

    raw_body = await request.body()

    if not verify_signature(raw_body, webhook_timestamp, webhook_signature, secret):
        raise HTTPException(status_code=400, detail="invalid signature")

    event = await request.json()
    event_type = event.get("type")
    # TODO: route specific event types to business logic / persistence
    return {"received": True, "event_type": event_type, "webhook_id": webhook_id}
