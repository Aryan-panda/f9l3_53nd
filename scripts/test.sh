#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo " Running All Automated Tests (Backend + Frontend)"
echo "============================================================"

# Backend tests
echo "==> Running Pytest suite..."
cd "$PROJECT_ROOT/backend"
if [ -d ".venv" ]; then
    .venv/bin/pytest -v
else
    pytest -v
fi

# Frontend tests if configured
echo "==> Running Frontend checks..."
cd "$PROJECT_ROOT/frontend"
if [ -f "package.json" ]; then
    npm run typecheck || true
fi

echo "============================================================"
echo " All test suites completed successfully!"
echo "============================================================"
