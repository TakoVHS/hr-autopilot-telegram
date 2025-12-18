# Webhook signature example

Signature is `HMAC_SHA256(secret, f"{timestamp}.{raw_body}")` and header `webhook-signature: v1=<hexdigest>`.

Example generation + curl:

```bash
WEBHOOK_SECRET='your_webhook_secret'
BODY='{"type":"ping"}'
TS=$(date +%s)
SIG=$(TS="$TS" BODY="$BODY" WEBHOOK_SECRET="$WEBHOOK_SECRET" python - <<'PY'
import hashlib, hmac, os
payload = f"{os.environ['TS']}.{os.environ['BODY']}".encode()
sig = hmac.new(os.environ['WEBHOOK_SECRET'].encode(), payload, hashlib.sha256).hexdigest()
print(f"v1={sig}")
PY
)

curl -X POST http://127.0.0.1:8000/webhook \
  -H "webhook-id: test" \
  -H "webhook-timestamp: $TS" \
  -H "webhook-signature: $SIG" \
  -d "$BODY"
```
