#!/usr/bin/env bash
# ==============================================================================
# f9l3_53nd Docker Compose Orchestration Launcher
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "==> Building and launching f9l3_53nd multi-branch container topology..."
docker compose build
docker compose up -d

echo "==> Waiting for services to become healthy..."
docker compose ps
echo "==> Cluster is ready."
