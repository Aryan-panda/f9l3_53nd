import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519


@dataclass(frozen=True)
class WireGuardKeypair:
    """Represents a base64-encoded Curve25519 WireGuard keypair."""

    private_key: str
    public_key: str


def generate_wireguard_keypair() -> WireGuardKeypair:
    """Generate a cryptographically secure Curve25519 keypair for WireGuard.

    Returns:
        WireGuardKeypair: Base64-encoded private and public keys.
    """
    private_key = x25519.X25519PrivateKey.generate()
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return WireGuardKeypair(
        private_key=base64.b64encode(priv_bytes).decode("ascii"),
        public_key=base64.b64encode(pub_bytes).decode("ascii"),
    )


def generate_preshared_key() -> str:
    """Generate a 256-bit symmetric pre-shared key (PSK) for post-quantum WireGuard security."""
    return base64.b64encode(os.urandom(32)).decode("ascii")


def generate_wireguard_config(
    interface_address: str,
    listen_port: int,
    private_key: str,
    peer_public_key: str,
    peer_allowed_ips: str,
    peer_endpoint: str | None = None,
    preshared_key: str | None = None,
    persistent_keepalive: int = 25,
) -> str:
    """Generate standardized WireGuard INI-style configuration string."""
    config_lines = [
        "[Interface]",
        f"Address = {interface_address}",
        f"ListenPort = {listen_port}",
        f"PrivateKey = {private_key}",
        "SaveConfig = false",
        "",
        "[Peer]",
        f"PublicKey = {peer_public_key}",
    ]

    if preshared_key:
        config_lines.append(f"PresharedKey = {preshared_key}")

    config_lines.append(f"AllowedIPs = {peer_allowed_ips}")

    if peer_endpoint:
        config_lines.append(f"Endpoint = {peer_endpoint}")

    config_lines.append(f"PersistentKeepalive = {persistent_keepalive}")
    return "\n".join(config_lines) + "\n"
