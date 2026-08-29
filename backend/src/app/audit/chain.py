import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings

GENESIS_HASH: str = "0000000000000000000000000000000000000000000000000000000000000000"


def normalize_timestamp_str(ts: datetime | str) -> str:
    """Normalize datetime or ISO string to standardized UTC ISO format."""
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        return ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    if isinstance(ts, str):
        try:
            parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        except Exception:
            return ts.strip()

    return str(ts)


def canonicalize_details(details: dict[str, Any] | None) -> str:
    """Produce deterministic, sorted JSON representation of event details."""
    if not details:
        return "{}"
    return json.dumps(details, sort_keys=True, separators=(",", ":"))


def compute_record_hash(
    event_id: str,
    timestamp: datetime | str,
    event_type: str,
    actor_id: str | None,
    target_resource: str | None,
    details: dict[str, Any] | None,
    prev_record_hash: str,
    secret_key: str | None = None,
) -> str:
    """Compute HMAC-SHA256 digest over audit record attributes and previous record hash.

    Format:
        event_id|timestamp_normalized|event_type|actor_id|target_resource|details_json|prev_record_hash
    """
    key = (secret_key or get_settings().SECRET_KEY).encode("utf-8")
    ts_norm = normalize_timestamp_str(timestamp)
    actor_str = str(actor_id).strip() if actor_id else "system"
    target_str = str(target_resource).strip() if target_resource else "none"
    details_str = canonicalize_details(details)

    payload = "|".join(
        [
            str(event_id).strip(),
            ts_norm,
            str(event_type).strip(),
            actor_str,
            target_str,
            details_str,
            str(prev_record_hash).strip().lower(),
        ]
    ).encode("utf-8")

    return hmac.new(key, payload, hashlib.sha256).hexdigest().lower()


def verify_chain_records(
    records: list[Any],
    secret_key: str | None = None,
) -> tuple[bool, int | None, str]:
    """Verify cryptographic integrity of an audit event chain from genesis to tail.

    Args:
        records: List of AuditEvent instances or dictionaries sorted chronologically.
        secret_key: Secret key used for HMAC calculation.

    Returns:
        tuple[bool, int | None, str]: (is_valid, broken_index, reason_description)
    """
    if not records:
        return True, None, "Audit log is empty (valid genesis state)."

    expected_prev = GENESIS_HASH

    for idx, record in enumerate(records):
        r_id = str(getattr(record, "id", None) or record.get("id"))
        ts = getattr(record, "timestamp", None) or record.get("timestamp")
        ev_type = str(getattr(record, "event_type", None) or record.get("event_type"))
        actor_id = getattr(record, "actor_id", None) or (
            record.get("actor_id") if isinstance(record, dict) else None
        )
        target = getattr(record, "target_resource", None) or (
            record.get("target_resource") if isinstance(record, dict) else None
        )
        details = getattr(record, "details", None) or (
            record.get("details") if isinstance(record, dict) else None
        )
        prev_hash = str(
            getattr(record, "prev_record_hash", None) or record.get("prev_record_hash")
        ).lower()
        rec_hash = str(getattr(record, "record_hash", None) or record.get("record_hash")).lower()

        # 1. Verify link to previous record hash
        if prev_hash != expected_prev.lower():
            return (
                False,
                idx,
                f"Broken chain link at index {idx}: expected prev_hash '{expected_prev}', "
                f"got '{prev_hash}'.",
            )

        # 2. Recompute current record hash
        computed = compute_record_hash(
            event_id=r_id,
            timestamp=ts,
            event_type=ev_type,
            actor_id=str(actor_id) if actor_id else None,
            target_resource=str(target) if target else None,
            details=details,
            prev_record_hash=prev_hash,
            secret_key=secret_key,
        )

        if not hmac.compare_digest(computed, rec_hash):
            return (
                False,
                idx,
                f"Tampered record content at index {idx}: computed '{computed}', "
                f"stored '{rec_hash}'.",
            )

        expected_prev = rec_hash

    return True, None, f"Audit chain verified successfully across {len(records)} records."
