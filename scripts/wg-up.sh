#!/usr/bin/env bash
# ==============================================================================
# f9l3_53nd — WireGuard Tunnel Bring-Up / Network Namespace Simulation
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "==> Initializing WireGuard Simulation Network..."

# Generate keys and configs if missing
if [[ ! -f "${ROOT_DIR}/infra/wireguard/branch-a/wg0.conf" ]]; then
    bash "${SCRIPT_DIR}/generate-wg-keys.sh"
fi

# Check if running with root / sudo permissions for kernel WireGuard namespace setup
if [[ $EUID -ne 0 ]]; then
    echo "[!] Non-root environment detected. Running in user-space / mock tunnel mode."
    echo "[+] Mock WireGuard tunnel initialized: Branch A (10.13.37.1) <===> Branch B (10.13.37.2)"
    echo "F9L3_WG_MODE=MOCK" > "${ROOT_DIR}/storage/wireguard_status.env"
    exit 0
fi

echo "==> Setting up Linux Network Namespaces for Branch A & Branch B..."
# Tear down any existing namespaces
ip netns del f9l3-branch-a 2>/dev/null || true
ip netns del f9l3-branch-b 2>/dev/null || true

# 1. Create namespaces
ip netns add f9l3-branch-a
ip netns add f9l3-branch-b

# 2. Create interconnect veth pair
ip link add veth-a type veth peer name veth-b
ip link set veth-a netns f9l3-branch-a
ip link set veth-b netns f9l3-branch-b

# 3. Configure veth underlay network (192.168.100.0/24)
ip netns exec f9l3-branch-a ip addr add 192.168.100.1/24 dev veth-a
ip netns exec f9l3-branch-a ip link set veth-a up
ip netns exec f9l3-branch-a ip link set lo up

ip netns exec f9l3-branch-b ip addr add 192.168.100.2/24 dev veth-b
ip netns exec f9l3-branch-b ip link set veth-b up
ip netns exec f9l3-branch-b ip link set lo up

# 4. Check if wireguard module is supported
if ip netns exec f9l3-branch-a ip link add dev wg0 type wireguard 2>/dev/null; then
    echo "==> WireGuard kernel module detected. Configuring wg0 interfaces..."
    ip netns exec f9l3-branch-b ip link add dev wg0 type wireguard

    # Configure Branch A
    ip netns exec f9l3-branch-a wg setconf wg0 "${ROOT_DIR}/infra/wireguard/branch-a/wg0.conf"
    ip netns exec f9l3-branch-a ip addr add 10.13.37.1/24 dev wg0
    ip netns exec f9l3-branch-a ip link set wg0 up

    # Configure Branch B
    ip netns exec f9l3-branch-b wg setconf wg0 "${ROOT_DIR}/infra/wireguard/branch-b/wg0.conf"
    ip netns exec f9l3-branch-b ip addr add 10.13.37.2/24 dev wg0
    ip netns exec f9l3-branch-b ip link set wg0 up

    echo "F9L3_WG_MODE=KERNEL_NAMESPACES" > "${ROOT_DIR}/storage/wireguard_status.env"
    echo "==> WireGuard kernel tunnel successfully established between namespaces!"
else
    echo "[!] WireGuard kernel module not available in this container/kernel. Using veth underlay simulation."
    echo "F9L3_WG_MODE=VETH_SIMULATION" > "${ROOT_DIR}/storage/wireguard_status.env"
fi
