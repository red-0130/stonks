#!/usr/bin/env bash
set -e

# Stonks v2 - Unified Startup Script
echo "Starting Stonks v2 Backend (FastAPI on port 8000)..."
cd /workspaces/stonks2/backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Stonks v2 Frontend (Vite on port 5173)..."
cd /workspaces/stonks2/frontend
bun run dev --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

echo "Stonks v2 is running!"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"

wait
