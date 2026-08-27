#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " Bootstrapping f9l3_53nd Development Environment"
echo "============================================================"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 1. Check Python version
echo "[1/5] Checking Python installation..."
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "ERROR: Python 3 is not installed or not in PATH."
    exit 1
fi
echo "Found: $($PYTHON_BIN --version)"

# 2. Check Node & npm
echo "[2/5] Checking Node.js and npm..."
if ! command -v node >/dev/null 2>&1; then
    echo "ERROR: Node.js is not installed."
    exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm is not installed."
    exit 1
fi
echo "Node: $(node -v), npm: $(npm -v)"

# 3. Setup Python Virtual Environment
echo "[3/5] Setting up Python virtual environment in backend/.venv..."
cd "$PROJECT_ROOT/backend"
if [ ! -d ".venv" ]; then
    $PYTHON_BIN -m venv .venv
fi
VENV_PYTHON="$PROJECT_ROOT/backend/.venv/bin/python"
VENV_PIP="$PROJECT_ROOT/backend/.venv/bin/pip"

$VENV_PIP install --upgrade pip setuptools wheel
$VENV_PIP install -e ".[dev]" || $VENV_PIP install fastapi uvicorn pydantic pydantic-settings sqlalchemy alembic asyncpg psycopg2-binary cryptography argon2-cffi python-multipart pytest pytest-asyncio httpx ruff mypy

# 4. Setup Frontend Dependencies
echo "[4/5] Installing Frontend npm packages..."
cd "$PROJECT_ROOT/frontend"
if [ -f "package.json" ]; then
    npm install
fi

# 5. Setup Local Secrets & Storage Directories
echo "[5/5] Initializing local storage and dev secrets..."
cd "$PROJECT_ROOT"
mkdir -p storage/encrypted storage/temporary storage/quarantine

if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    bash scripts/generate-dev-secrets.sh
fi

echo "============================================================"
echo " Bootstrap complete! Run 'make test' or 'make dev'"
echo "============================================================"
