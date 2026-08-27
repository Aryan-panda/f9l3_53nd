FROM python:3.12-slim-bookworm

# Security: Create non-root system user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/pyproject.toml /app/backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "/app/backend[dev]" || \
    pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings sqlalchemy alembic asyncpg psycopg2-binary cryptography argon2-cffi python-multipart

# Copy source code and configuration
COPY backend /app/backend
COPY storage /app/storage

RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

WORKDIR /app/backend
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
