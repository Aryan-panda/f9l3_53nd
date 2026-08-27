#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Generating cryptographically secure random secrets for development..."

DEV_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
DEV_MASTER_KEY_HEX=$(python3 -c "import secrets; print(secrets.token_hex(32))")

if [ ! -f ".env" ]; then
    cp .env.example .env
fi

# Replace SECRET_KEY and MASTER_KEY_HEX safely
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s|^SECRET_KEY=.*|SECRET_KEY=${DEV_SECRET_KEY}|" .env
    sed -i '' "s|^MASTER_KEY_HEX=.*|MASTER_KEY_HEX=${DEV_MASTER_KEY_HEX}|" .env
else
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${DEV_SECRET_KEY}|" .env
    sed -i "s|^MASTER_KEY_HEX=.*|MASTER_KEY_HEX=${DEV_MASTER_KEY_HEX}|" .env
fi

echo "Successfully generated dev secrets in .env"
echo "SECRET_KEY (length: ${#DEV_SECRET_KEY})"
echo "MASTER_KEY_HEX (256-bit AES KEK, hex length: ${#DEV_MASTER_KEY_HEX})"
