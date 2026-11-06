# ==============================================================================
# Stage 1: Build Frontend Assets
# ==============================================================================
FROM oven/bun:1-alpine AS frontend-builder

WORKDIR /frontend

# Copy dependencies first for Docker layer caching
COPY frontend/package.json ./

# Install dependencies and build static distribution
RUN bun install --frozen-lockfile || bun install

COPY frontend/ ./
RUN bun run build

# ==============================================================================
# Stage 2: Production Python Runtime
# ==============================================================================
FROM python:3.12-slim-bookworm AS runtime

# Install system dependencies (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PORT=8000 \
    STATIC_DIR=/app/static \
    PATH="/app/.venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Install Python backend dependencies using uv
COPY backend/pyproject.toml ./
RUN chown -R appuser:appgroup /app

USER appuser
RUN uv sync --no-dev --no-install-project

# Copy backend application source
COPY --chown=appuser:appgroup backend/app ./app

# Copy compiled frontend from builder stage
COPY --from=frontend-builder --chown=appuser:appgroup /frontend/dist /app/static

EXPOSE 8000

# Container healthcheck against FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# Start Uvicorn bound to 0.0.0.0 and dynamic $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
