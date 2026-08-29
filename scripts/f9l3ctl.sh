#!/usr/bin/env bash
# ==============================================================================
# f9l3ctl — CLI Automation Wrapper
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PYTHONPATH="${ROOT_DIR}/backend/src"
exec "${ROOT_DIR}/backend/.venv/bin/python" -m app.cli.main "$@"
