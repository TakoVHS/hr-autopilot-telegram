import hashlib
import hmac
import time

from app.tools.webhook import verify_signature


def _build_signature(secret: str, ts: str, body: bytes) -> str:
    payload = f"{ts}.{body.decode('utf-8')}".encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def test_verify_signature_success():
    secret = "topsecret"
    body = b"{}"
    ts = str(int(time.time()))
    sig = _build_signature(secret, ts, body)
    assert verify_signature(body, ts, f"v1={sig}", secret)


def test_verify_signature_invalid_signature():
    secret = "topsecret"
    body = b"{}"
    ts = str(int(time.time()))
    assert not verify_signature(body, ts, "v1=bad", secret)


def test_verify_signature_old_timestamp():
    secret = "topsecret"
    body = b"{}"
    ts = str(int(time.time()) - 1000)
    sig = _build_signature(secret, ts, body)
    assert not verify_signature(body, ts, f"v1={sig}", secret)
