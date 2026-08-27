#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Cleaning build artifacts, caches, and temporary payloads..."

# Remove python caches
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Clean temporary and quarantine storage files (preserve .gitkeep)
find storage/temporary -type f ! -name ".gitkeep" -delete 2>/dev/null || true
find storage/quarantine -type f ! -name ".gitkeep" -delete 2>/dev/null || true

echo "Environment cleaned successfully."
