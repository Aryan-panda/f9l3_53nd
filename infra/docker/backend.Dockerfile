# ==============================================================================
# Stage 1: Build & Dependency Wheel Cache
# ==============================================================================
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml /build/backend/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install "/build/backend[dev]" || \
    pip install --no-cache-dir --prefix=/install fastapi uvicorn pydantic pydantic-settings sqlalchemy alembic asyncpg psycopg2-binary cryptography argon2-cffi python-multipart httpx

# ==============================================================================
# Stage 2: Hardened Minimal Runtime
# ==============================================================================
FROM python:3.12-slim-bookworm AS runtime

# Security: Create non-root system user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Install only minimal runtime shared libraries (curl for healthchecks, libpq for Postgres)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed python dependencies from builder
COPY --from=builder /install /usr/local

# Copy application source code and configurations
COPY backend /app/backend
COPY storage /app/storage

# Set permissions and switch to unprivileged user
RUN chown -R appuser:appgroup /app && \
    chmod -R 750 /app

USER appuser

EXPOSE 8000

WORKDIR /app/backend

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
