from app.core.config import settings
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _check_internal_token(request: Request) -> None:
    token = settings.internal_api_token
    if not token:
        raise HTTPException(status_code=401, detail="INTERNAL_API_TOKEN not set")
    provided = request.headers.get("x-internal-token")
    if not provided or provided != token:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.post("/followup")
async def run_followup(request: Request):
    _check_internal_token(request)
    # Placeholder: integrate actual follow-up logic here.
    return {"status": "ok", "processed": 0}
