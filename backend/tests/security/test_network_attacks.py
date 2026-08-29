import ipaddress

import pytest

from app.crypto.wireguard import generate_wireguard_config, generate_wireguard_keypair


@pytest.mark.security
def test_wireguard_allowed_ips_containment() -> None:
    """Security Test: AllowedIPs must strictly isolate traffic to designated point-to-point peer."""
    kp_a = generate_wireguard_keypair()
    kp_b = generate_wireguard_keypair()

    # AllowedIPs set to /32 for exact single-host routing
    conf = generate_wireguard_config(
        interface_address="10.13.37.1/24",
        listen_port=51820,
        private_key=kp_a.private_key,
        peer_public_key=kp_b.public_key,
        peer_allowed_ips="10.13.37.2/32",
        peer_endpoint="127.0.0.1:51821",
    )

    assert "AllowedIPs = 10.13.37.2/32" in conf

    # Ensure unassigned IP (e.g. 10.13.37.55 or 192.168.1.1) is not within the /32 peer mask
    peer_net = ipaddress.ip_network("10.13.37.2/32")
    attacker_ip = ipaddress.ip_address("10.13.37.55")
    assert attacker_ip not in peer_net


@pytest.mark.security
def test_wireguard_key_uniqueness() -> None:
    """Security Test: Consecutive key generations must produce unique Curve25519 keys."""
    keys = {generate_wireguard_keypair().private_key for _ in range(50)}
    assert len(keys) == 50
