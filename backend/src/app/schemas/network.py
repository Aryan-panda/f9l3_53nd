from pydantic import BaseModel


class TunnelStatusRead(BaseModel):
    """Schema representing WireGuard tunnel interface and connectivity status."""

    interface: str
    status: str
    local_ip: str
    peer_ip: str
    peer_endpoint: str | None = None
    latest_handshake_seconds_ago: int | None = None
    is_connected: bool
    mode: str
