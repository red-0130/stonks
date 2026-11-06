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
# Stage 2: Production Runtime (Frontend Server & Internal API Backend)
# ==============================================================================
FROM python:3.12-slim-bookworm AS runtime

# Install system dependencies:
# - nginx: Dedicated frontend server & API reverse proxy
# - curl, ca-certificates: Healthchecks and HTTPS requests
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    nginx \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

# Install uv from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PORT=5173 \
    STATIC_DIR=/app/static \
    PATH="/app/.venv/bin:$PATH"

# Create non-root user for backend execution
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Install Python backend dependencies using uv
COPY backend/pyproject.toml ./
RUN uv sync --no-dev --no-install-project

# Copy backend application source
COPY backend/app ./app

# Copy compiled frontend from builder stage to Nginx static root
COPY --from=frontend-builder /frontend/dist /app/static

# Copy Nginx configuration and entrypoint script
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && chown -R appuser:appgroup /app

# Expose ONLY the frontend port (5173) - Backend (8000) is internal only
EXPOSE 5173

# Container healthcheck against Nginx frontend reverse proxy
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5173}/api/health || exit 1

# Start internal backend & frontend server
ENTRYPOINT ["/app/entrypoint.sh"]
