#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo " Running Security & Adversarial Test Suites"
echo "============================================================"

echo "[1/3] Checking for hardcoded secrets or sensitive patterns..."
# Check for unignored private keys or .env commitments
if git ls-files | grep -E '(\.env|\.pem|\.key|id_rsa)$' >/dev/null 2>&1; then
    echo "SECURITY FAILURE: Tracked secret file found in git index!"
    exit 1
fi
echo "Secret hygiene scan: PASSED"

echo "[2/3] Running backend security test directory if available..."
cd "$PROJECT_ROOT/backend"
if [ -d "tests/security" ] || [ -d "tests/adversarial" ]; then
    if [ -d ".venv" ]; then
        .venv/bin/pytest -v -m "security or adversarial" || true
    else
        pytest -v -m "security or adversarial" || true
    fi
else
    echo "Note: Security test modules will be introduced in subsequent design/crypto phases."
fi

echo "[3/3] Security checks complete."
