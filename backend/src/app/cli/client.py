import json
from pathlib import Path
from typing import Any

import httpx

SESSION_FILE_PATH = Path.home() / ".f9l3_session"


class F9l3CliError(Exception):
    """Exception raised for CLI interaction errors."""


class F9l3Client:
    """HTTP client wrapper for f9l3ctl automation CLI."""

    def __init__(self, server_url: str = "http://127.0.0.1:8000") -> None:
        self.server_url = server_url.rstrip("/")
        self.api_base = f"{self.server_url}/api/v1"
        self._session_cookie = self._load_session_cookie()

    def _load_session_cookie(self) -> str | None:
        """Load session token from local config file if present."""
        if SESSION_FILE_PATH.exists():
            try:
                data = json.loads(SESSION_FILE_PATH.read_text())
                return str(data.get("session_token", "")) or None
            except Exception:
                return None
        return None

    def _save_session_cookie(self, token: str) -> None:
        """Save session token securely to local config file."""
        SESSION_FILE_PATH.write_text(json.dumps({"session_token": token}))
        SESSION_FILE_PATH.chmod(0o600)
        self._session_cookie = token

    def _get_cookies(self) -> dict[str, str]:
        cookies = {}
        if self._session_cookie:
            cookies["f9l3_session"] = self._session_cookie
        return cookies

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate with backend and save session cookie."""
        url = f"{self.api_base}/auth/login"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    url,
                    json={"username": username, "password": password},
                )
                if res.status_code != 200:
                    err_msg = res.json().get("error", {}).get("message", res.text)
                    raise F9l3CliError(f"Login failed ({res.status_code}): {err_msg}")
                token = res.cookies.get("f9l3_session")
                if token:
                    self._save_session_cookie(token)
                return dict(res.json())
        except httpx.RequestError as e:
            raise F9l3CliError(f"Connection to server '{self.server_url}' failed: {e}") from e

    def list_transfers(self, offset: int = 0, limit: int = 50) -> dict[str, Any]:
        """List transfers visible to current session user."""
        url = f"{self.api_base}/transfers?offset={offset}&limit={limit}"
        with httpx.Client(timeout=10.0, cookies=self._get_cookies()) as client:
            res = client.get(url)
            if res.status_code != 200:
                err_msg = res.json().get("error", {}).get("message", res.text)
                raise F9l3CliError(f"List failed ({res.status_code}): {err_msg}")
            return dict(res.json())

    def get_transfer_status(self, transfer_id: str) -> dict[str, Any]:
        """Get transfer details and verification status."""
        url = f"{self.api_base}/transfers/{transfer_id}"
        with httpx.Client(timeout=10.0, cookies=self._get_cookies()) as client:
            res = client.get(url)
            if res.status_code != 200:
                err_msg = res.json().get("error", {}).get("message", res.text)
                raise F9l3CliError(f"Query failed ({res.status_code}): {err_msg}")
            return dict(res.json())

    def send_file(self, recipient_id: str, file_path: str) -> dict[str, Any]:
        """Upload and encrypt file through pipeline."""
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            raise F9l3CliError(f"File not found: '{file_path}'")

        url = f"{self.api_base}/transfers"
        with open(p, "rb") as f:
            files = {"file": (p.name, f, "application/octet-stream")}
            data = {"recipient_id": recipient_id}
            with httpx.Client(timeout=30.0, cookies=self._get_cookies()) as client:
                res = client.post(url, data=data, files=files)
                if res.status_code != 201:
                    err_msg = res.json().get("error", {}).get("message", res.text)
                    raise F9l3CliError(f"Send failed ({res.status_code}): {err_msg}")
                return dict(res.json())

    def receive_file(self, transfer_id: str, output_path: str | None = None) -> Path:
        """Download and verify transfer payload."""
        url = f"{self.api_base}/transfers/{transfer_id}/download"
        with httpx.Client(timeout=30.0, cookies=self._get_cookies()) as client:
            res = client.get(url)
            if res.status_code != 200:
                err_msg = res.json().get("error", {}).get("message", res.text)
                raise F9l3CliError(f"Download failed ({res.status_code}): {err_msg}")

            # Determine filename from Content-Disposition or fallback
            filename = f"downloaded_{transfer_id}.bin"
            cd = res.headers.get("content-disposition", "")
            if 'filename="' in cd:
                filename = cd.split('filename="')[1].split('"')[0]

            out_path = Path(output_path or filename)
            out_path.write_bytes(res.content)
            return out_path

    def verify_audit_chain(self) -> dict[str, Any]:
        """Trigger cryptographic verification of audit log chain."""
        url = f"{self.api_base}/admin/audit-events/verify"
        with httpx.Client(timeout=10.0, cookies=self._get_cookies()) as client:
            res = client.post(url)
            if res.status_code != 200:
                err_msg = res.json().get("error", {}).get("message", res.text)
                raise F9l3CliError(f"Verification failed ({res.status_code}): {err_msg}")
            return dict(res.json())

    def get_network_status(self) -> dict[str, Any]:
        """Get WireGuard tunnel status."""
        url = f"{self.api_base}/admin/network/status"
        with httpx.Client(timeout=10.0, cookies=self._get_cookies()) as client:
            res = client.get(url)
            if res.status_code != 200:
                err_msg = res.json().get("error", {}).get("message", res.text)
                raise F9l3CliError(f"Network query failed ({res.status_code}): {err_msg}")
            return dict(res.json())
