#!/usr/bin/env bash
# ==============================================================================
# f9l3_53nd Docker Compose Teardown Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "==> Tearing down f9l3_53nd multi-branch container topology..."
docker compose down -v --remove-orphans
echo "==> Clean teardown complete."
