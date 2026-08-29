#!/usr/bin/env bash
# ==============================================================================
# f9l3_53nd — WireGuard Keypair & Configuration Generator
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WG_DIR="${ROOT_DIR}/infra/wireguard"

echo "==> Generating WireGuard Curve25519 Keypairs and PSKs..."

# Use Python with cryptography library for 100% portable Curve25519 generation
python3 - << 'EOF'
import os
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

def gen_x25519_keypair():
    priv = x25519.X25519PrivateKey.generate()
    priv_bytes = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_bytes = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return base64.b64encode(priv_bytes).decode("ascii"), base64.b64encode(pub_bytes).decode("ascii")

def gen_psk():
    return base64.b64encode(os.urandom(32)).decode("ascii")

branch_a_priv, branch_a_pub = gen_x25519_keypair()
branch_b_priv, branch_b_pub = gen_x25519_keypair()
preshared_key = gen_psk()

wg_dir = Path("infra/wireguard")
branch_a_dir = wg_dir / "branch-a"
branch_b_dir = wg_dir / "branch-b"
branch_a_dir.mkdir(parents=True, exist_ok=True)
branch_b_dir.mkdir(parents=True, exist_ok=True)

# Generate Branch A wg0.conf
branch_a_conf = f"""# WireGuard Configuration — Branch A (Point-to-Point)
[Interface]
Address = 10.13.37.1/24
ListenPort = 51820
PrivateKey = {branch_a_priv}
SaveConfig = false

[Peer]
# Branch B Peer
PublicKey = {branch_b_pub}
PresharedKey = {preshared_key}
AllowedIPs = 10.13.37.2/32
Endpoint = 127.0.0.1:51821
PersistentKeepalive = 25
"""

# Generate Branch B wg0.conf
branch_b_conf = f"""# WireGuard Configuration — Branch B (Point-to-Point)
[Interface]
Address = 10.13.37.2/24
ListenPort = 51821
PrivateKey = {branch_b_priv}
SaveConfig = false

[Peer]
# Branch A Peer
PublicKey = {branch_a_pub}
PresharedKey = {preshared_key}
AllowedIPs = 10.13.37.1/32
Endpoint = 127.0.0.1:51820
PersistentKeepalive = 25
"""

with open(branch_a_dir / "wg0.conf", "w") as f:
    f.write(branch_a_conf)
os.chmod(branch_a_dir / "wg0.conf", 0o600)

with open(branch_b_dir / "wg0.conf", "w") as f:
    f.write(branch_b_conf)
os.chmod(branch_b_dir / "wg0.conf", 0o600)

print(f"  Branch A Public Key: {branch_a_pub}")
print(f"  Branch B Public Key: {branch_b_pub}")
print("  Generated infra/wireguard/branch-a/wg0.conf (mode 0600)")
print("  Generated infra/wireguard/branch-b/wg0.conf (mode 0600)")
EOF

echo "==> WireGuard keys and configuration generated successfully!"
