# syntax=docker/dockerfile:1

# ==============================================================================
# Builder stage: Install dependencies and compile virtual environment
# ==============================================================================
FROM python:3.13-slim AS builder

# Install uv binary from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Configure uv: compile bytecode to speed up container startup, copy instead of hardlink
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Copy dependency specifications first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install external dependencies into /app/.venv without installing the project itself
RUN uv sync --frozen --no-install-project --no-dev

# Copy application source code and files
COPY . .

# Install the application itself into the virtual environment
RUN uv sync --frozen --no-dev


# ==============================================================================
# Runtime stage: Lean and secure production image
# ==============================================================================
FROM python:3.13-slim AS runner

# Environment variables:
# - PYTHONUNBUFFERED=1: Stream logs directly to stdout/stderr
# - PYTHONDONTWRITEBYTECODE=1: Prevent Python from writing .pyc files at runtime
# - PATH: Prioritize virtualenv binaries (stonks, streamlit)
# - STREAMLIT_*: Configure Streamlit for containerized execution
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Install ca-certificates (HTTPS for yfinance) and curl (healthcheck),
# then create a non-root system user for secure container execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser \
    && useradd -r -g appuser -d /home/appuser -m -s /sbin/nologin appuser

# Copy virtual environment and application from builder with non-root ownership
COPY --from=builder --chown=appuser:appuser /app /app

# Run as non-privileged user
USER appuser

# Expose Streamlit's default port
EXPOSE 8501

# Healthcheck to verify the dashboard is ready and responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Launch the Stonks dashboard
CMD ["stonks"]

