#!/usr/bin/env bash
# ==============================================================================
# f9l3_53nd — WireGuard Tunnel Tear-Down Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "==> Tearing down WireGuard simulation..."

if [[ $EUID -eq 0 ]]; then
    ip netns del f9l3-branch-a 2>/dev/null || true
    ip netns del f9l3-branch-b 2>/dev/null || true
    echo "  Cleaned up namespaces: f9l3-branch-a, f9l3-branch-b"
fi

rm -f "${ROOT_DIR}/storage/wireguard_status.env"
echo "==> WireGuard simulation torn down successfully."
