#!/usr/bin/env bash
# Builds the dashboard frontend and starts the FastAPI backend (no hot reload).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-9000}"

echo "==> Building frontend"
(cd "$SCRIPT_DIR/frontend" && npm install && npm run build)

echo "==> Starting backend on http://localhost:$PORT"
cd "$SCRIPT_DIR"
source venv/bin/activate
exec uvicorn server:app --host 0.0.0.0 --port "$PORT"
