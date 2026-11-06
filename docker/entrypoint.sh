#!/bin/bash
set -e

FRONTEND_PORT=${PORT:-5173}

# Update Nginx listen port dynamically if $PORT is provided
sed -i "s/listen [0-9]\+;/listen ${FRONTEND_PORT};/g" /etc/nginx/conf.d/default.conf

echo "Starting internal FastAPI backend on 127.0.0.1:8000 (isolated)..."
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend healthcheck
until curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; do
    sleep 0.2
done
echo "Internal backend is ready."

echo "Starting Nginx frontend server on port ${FRONTEND_PORT}..."
nginx -g "daemon off;" &
NGINX_PID=$!

# Trap shutdown signals to terminate both processes cleanly
trap "kill -TERM $BACKEND_PID $NGINX_PID" SIGTERM SIGINT
wait -n $BACKEND_PID $NGINX_PID
