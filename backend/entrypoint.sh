#!/usr/bin/env bash
set -e

if [[ "${RUN_MIGRATIONS_ON_START:-0}" == "1" ]]; then
  echo "[entrypoint] Running migrations..."
  alembic upgrade head
else
  echo "[entrypoint] Skipping migrations (RUN_MIGRATIONS_ON_START!=1)"
fi

PORT="${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
