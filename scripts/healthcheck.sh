#!/usr/bin/env bash
# ==============================================================================
# f9l3_53nd Healthcheck Script
# ==============================================================================
set -euo pipefail

SERVER_URL="${1:-http://127.0.0.1:8000}"

echo "==> Running health check against ${SERVER_URL}..."

# 1. Liveness check
LIVENESS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVER_URL}/health/live" || echo "000")
if [[ "${LIVENESS}" -ne 200 ]]; then
    echo "[-] Liveness check failed (HTTP ${LIVENESS})"
    exit 1
fi
echo "[+] Liveness check OK (HTTP 200)"

# 2. Readiness check
READINESS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVER_URL}/health/ready" || echo "000")
if [[ "${READINESS}" -ne 200 ]]; then
    echo "[-] Readiness check failed (HTTP ${READINESS})"
    exit 1
fi
echo "[+] Readiness check OK (HTTP 200)"

echo "==> All application health probes passed successfully."
