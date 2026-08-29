import base64

import pytest

from app.crypto.wireguard import (
    generate_preshared_key,
    generate_wireguard_config,
    generate_wireguard_keypair,
)


@pytest.mark.unit
def test_generate_wireguard_keypair() -> None:
    """Validate Curve25519 keypair generation produces valid 32-byte Base64 keys."""
    keypair = generate_wireguard_keypair()
    assert keypair.private_key is not None
    assert keypair.public_key is not None

    priv_raw = base64.b64decode(keypair.private_key)
    pub_raw = base64.b64decode(keypair.public_key)

    assert len(priv_raw) == 32
    assert len(pub_raw) == 32


@pytest.mark.unit
def test_generate_preshared_key() -> None:
    """Validate 256-bit PSK generation produces 32-byte Base64 string."""
    psk = generate_preshared_key()
    psk_raw = base64.b64decode(psk)
    assert len(psk_raw) == 32


@pytest.mark.unit
def test_generate_wireguard_config_structure() -> None:
    """Validate WireGuard INI config builder generates compliant sections and parameters."""
    kp_a = generate_wireguard_keypair()
    kp_b = generate_wireguard_keypair()
    psk = generate_preshared_key()

    conf = generate_wireguard_config(
        interface_address="10.13.37.1/24",
        listen_port=51820,
        private_key=kp_a.private_key,
        peer_public_key=kp_b.public_key,
        peer_allowed_ips="10.13.37.2/32",
        peer_endpoint="127.0.0.1:51821",
        preshared_key=psk,
        persistent_keepalive=25,
    )

    assert "[Interface]" in conf
    assert "Address = 10.13.37.1/24" in conf
    assert "ListenPort = 51820" in conf
    assert f"PrivateKey = {kp_a.private_key}" in conf
    assert "[Peer]" in conf
    assert f"PublicKey = {kp_b.public_key}" in conf
    assert f"PresharedKey = {psk}" in conf
    assert "AllowedIPs = 10.13.37.2/32" in conf
    assert "Endpoint = 127.0.0.1:51821" in conf
    assert "PersistentKeepalive = 25" in conf
