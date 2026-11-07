#!/usr/bin/env bash
set -e

# Stonks v2 - Unified Startup Script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

echo "Starting Stonks v2 Backend (FastAPI on port 8000)..."
cd "$SCRIPT_DIR/backend"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Stonks v2 Frontend (Vite on port 5173)..."
cd "$SCRIPT_DIR/frontend"
bun run dev --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

cleanup() {
  trap - EXIT INT TERM
  echo ""
  echo "Shutting down Stonks v2 services..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "Stonks v2 is running!"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"

wait
