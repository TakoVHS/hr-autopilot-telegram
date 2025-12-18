import httpx
import pytest

from app import main


@pytest.mark.anyio
async def test_health_returns_minimal_fields(monkeypatch):
    async def _no_check():
        return None

    monkeypatch.setattr(main, "check_database", _no_check)
    monkeypatch.setattr(main, "ensure_telegram_tables", _no_check)
    class _DummyEngine:
        async def dispose(self):
            return None

    monkeypatch.setattr(main, "engine", _DummyEngine())

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    body = resp.json()
    for key in ["ok", "env", "public_url", "commit_sha", "db_ok"]:
        assert key in body
    assert isinstance(body["db_ok"], bool)
