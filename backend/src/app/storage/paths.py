import os
import re
from pathlib import Path
from uuid import UUID

from app.core.config import get_settings
from app.core.exceptions import StorageError


def sanitize_filename(raw_filename: str) -> str:
    """Sanitize client-provided filename to eliminate path traversal characters.

    Args:
        raw_filename: Untrusted filename provided by user/client.

    Returns:
        str: Safe, normalized base filename.
    """
    if not raw_filename or not raw_filename.strip():
        return "unnamed_payload.bin"

    # 1. Normalize backslashes to forward slashes to handle Windows paths on Linux
    normalized = raw_filename.strip().replace("\\", "/")

    # 2. Extract base component
    base_name = os.path.basename(normalized.rstrip("/"))
    if not base_name:
        parts = [p for p in normalized.split("/") if p]
        base_name = parts[-1] if parts else "unnamed_payload.bin"

    # 3. Strip null bytes and non-printable chars
    cleaned = base_name.replace("\x00", "")

    # 4. Remove traversal dots sequences
    while ".." in cleaned:
        cleaned = cleaned.replace("..", "_")

    # 5. Remove any dangerous non-alphanumeric chars (keep dot, dash, underscore)
    safe_name = re.sub(r"[^\w\.\-\_]", "_", cleaned)
    safe_name = safe_name.strip("._- ")

    if not safe_name:
        safe_name = "sanitized_payload.bin"

    if len(safe_name) > 200:
        safe_name = safe_name[:200]

    return safe_name


def get_encrypted_payload_path(transfer_id: UUID | str) -> Path:
    """Resolve and ensure absolute path containment for an encrypted transfer payload.

    Format: <STORAGE_BASE_DIR>/encrypted/<transfer_id>/payload.enc

    Args:
        transfer_id: UUID of the transfer.

    Returns:
        Path: Absolute path inside encrypted storage.

    Raises:
        StorageError: If path escapes the configured base directory.
    """
    settings = get_settings()
    base_dir = Path(settings.STORAGE_BASE_DIR).resolve()
    encrypted_base = (base_dir / "encrypted").resolve()

    target_dir = (encrypted_base / str(transfer_id)).resolve()
    # Path containment check (CWE-22)
    if not target_dir.is_relative_to(encrypted_base):
        raise StorageError("Path traversal detected in encrypted storage resolver.")

    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / "payload.enc"


def get_quarantine_payload_path(transfer_id: UUID | str) -> Path:
    """Resolve and ensure path containment for quarantined tampered payloads.

    Format: <STORAGE_BASE_DIR>/quarantine/<transfer_id>/quarantined.bin
    """
    settings = get_settings()
    base_dir = Path(settings.STORAGE_BASE_DIR).resolve()
    quarantine_base = (base_dir / "quarantine").resolve()

    target_dir = (quarantine_base / str(transfer_id)).resolve()
    if not target_dir.is_relative_to(quarantine_base):
        raise StorageError("Path traversal detected in quarantine storage resolver.")

    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / "quarantined.bin"
