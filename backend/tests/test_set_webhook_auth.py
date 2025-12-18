import httpx
import pytest

from app import main


@pytest.mark.anyio
async def test_set_webhook_requires_internal_token(monkeypatch):
    monkeypatch.setattr(main.settings, "internal_api_token", "secret")
    async def _noop():
        return None
    monkeypatch.setattr(main, "check_database", _noop)
    monkeypatch.setattr(main, "ensure_telegram_tables", _noop)
    class _DummyEngine:
        async def dispose(self):
            return None

    monkeypatch.setattr(main, "engine", _DummyEngine())

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/telegram/set-webhook")

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_set_webhook_with_token_and_mocked_telegram(monkeypatch):
    monkeypatch.setattr(main.settings, "internal_api_token", "secret")
    monkeypatch.setattr(main.settings, "backend_public_url", "https://example.com")
    monkeypatch.setattr(main.settings, "telegram_bot_token", "123:ABC")
    async def _noop():
        return None
    monkeypatch.setattr(main, "check_database", _noop)
    monkeypatch.setattr(main, "ensure_telegram_tables", _noop)
    class _DummyEngine:
        async def dispose(self):
            return None

    monkeypatch.setattr(main, "engine", _DummyEngine())

    # Mock outbound Telegram call
    def _handler(request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        return httpx.Response(200, json={"ok": True, "description": "set"})

    transport_mock = httpx.MockTransport(_handler)
    original_async_client = httpx.AsyncClient

    def _client_factory(*args, **kwargs):
        kwargs["transport"] = transport_mock
        return original_async_client(*args, **kwargs)

    monkeypatch.setattr("app.tools.telegram_webhook.httpx.AsyncClient", _client_factory)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/telegram/set-webhook",
            headers={"x-internal-token": "secret"},
        )

    assert resp.status_code == 200
    assert resp.json().get("ok") is True
