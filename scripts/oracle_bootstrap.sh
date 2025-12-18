#!/usr/bin/env bash
set -euo pipefail

# Install Docker and Compose plugin on Oracle Linux/Ubuntu
if ! command -v docker >/dev/null 2>&1; then
  echo "[bootstrap] Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "[bootstrap] Docker Compose plugin not found. Please install manually (package docker-compose-plugin)."
fi

echo "[bootstrap] Preparing /opt/hr-autopilot"
sudo mkdir -p /opt/hr-autopilot
sudo chown "$USER":"$USER" /opt/hr-autopilot

# Placeholders: copy files after cloning repo or scp
#   docker-compose.prod.yml -> /opt/hr-autopilot/docker-compose.yml
#   Caddyfile -> /opt/hr-autopilot/Caddyfile
#   .env -> /opt/hr-autopilot/.env

echo "[bootstrap] Remember to open ports 80 and 443 in Oracle Cloud Security Lists."