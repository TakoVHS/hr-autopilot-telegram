#!/usr/bin/env bash
set -euo pipefail

ORACLE_HOST=${ORACLE_HOST:?set ORACLE_HOST}
ORACLE_USER=${ORACLE_USER:?set ORACLE_USER}
ORACLE_SSH_KEY=${ORACLE_SSH_KEY:-$HOME/.ssh/id_rsa}
GHCR_PAT=${GHCR_PAT:?set GHCR_PAT}
GHCR_USER=${GHCR_USER:-${ORACLE_USER}}

ssh -i "$ORACLE_SSH_KEY" "$ORACLE_USER@$ORACLE_HOST" <<'EOF'
set -euo pipefail
if ! command -v docker >/dev/null 2>&1; then
  echo "docker not installed" && exit 1
fi
cd /opt/hr-autopilot
echo "$GHCR_PAT" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
docker compose pull
docker compose up -d
curl -fsS http://localhost/health || (echo "health check failed" && exit 1)
EOF
