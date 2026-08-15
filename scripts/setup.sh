#!/usr/bin/env bash
# CyberBite one-shot setup (Docker path)
set -e
cd "$(dirname "$0")/.."

echo "=============================================="
echo " CyberBite - your local AI security copilot"
echo " AI + Knowledge + Tools + Isolation + Logging"
echo "=============================================="

if ! command -v docker >/dev/null 2>&1; then
  echo "[!] Docker is required. Install Docker Desktop first."
  exit 1
fi
docker info >/dev/null 2>&1 || { echo "[!] Docker daemon not running. Start Docker Desktop."; exit 1; }

[ -f .env ] || { cp .env.example .env; echo "[*] Created .env from template (edit passwords!)."; }

echo "[*] Building images (backend, frontend, lab sandbox)..."
docker compose build

echo "[*] Starting database + ollama..."
docker compose up -d db ollama

echo "[*] Pulling local AI models (first run downloads ~4-5 GB)..."
docker compose exec -T ollama ollama pull "${OLLAMA_MODEL:-llama3}" || true
docker compose exec -T ollama ollama pull "${EMBED_MODEL:-nomic-embed-text}" || true

echo "[*] Starting backend + frontend..."
docker compose up -d

echo ""
echo "[+] DONE"
echo "    Web UI:      http://localhost:8080"
echo "    API docs:    http://localhost:8000/docs"
echo "    Admin login: ADMIN_USERNAME / ADMIN_PASSWORD from .env"
echo ""
echo "    Next steps:"
echo "    1) Log in as admin -> ADMIN tab -> promote users to 'pro'"
echo "       (selected users get FREE & UNLIMITED access)"
echo "    2) Everyone else stays on the limited tier (CHAT only, 10/day)."
echo "    3) Add your own knowledge files under knowledge/ and restart backend."
