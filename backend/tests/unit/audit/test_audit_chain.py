import uuid
from datetime import UTC, datetime

import pytest

from app.audit.chain import (
    GENESIS_HASH,
    compute_record_hash,
    verify_chain_records,
)
from app.audit.events import AuditEventType


@pytest.mark.unit
def test_genesis_chain_verification_empty() -> None:
    """An empty audit log is a valid genesis state."""
    is_valid, broken_idx, _ = verify_chain_records([])
    assert is_valid is True
    assert broken_idx is None


@pytest.mark.unit
def test_valid_audit_chain_three_records() -> None:
    """Verify standard valid 3-record cryptographic hash chain."""
    records = []
    prev = GENESIS_HASH

    for i in range(3):
        r_id = str(uuid.uuid4())
        ts = datetime.now(UTC)
        ev_type = AuditEventType.AUTH_LOGIN_SUCCESS.value
        details = {"attempt": i}

        rec_hash = compute_record_hash(
            event_id=r_id,
            timestamp=ts,
            event_type=ev_type,
            actor_id="user-123",
            target_resource="auth",
            details=details,
            prev_record_hash=prev,
        )
        record = {
            "id": r_id,
            "timestamp": ts,
            "event_type": ev_type,
            "actor_id": "user-123",
            "target_resource": "auth",
            "details": details,
            "prev_record_hash": prev,
            "record_hash": rec_hash,
        }
        records.append(record)
        prev = rec_hash

    is_valid, broken_idx, _ = verify_chain_records(records)
    assert is_valid is True
    assert broken_idx is None


@pytest.mark.unit
def test_tampered_details_detected_at_exact_index() -> None:
    """Mutating record details at index 1 must cause verification failure at index 1."""
    records = []
    prev = GENESIS_HASH

    for i in range(4):
        r_id = str(uuid.uuid4())
        ts = datetime.now(UTC)
        ev_type = AuditEventType.TRANSFER_UPLOADED.value
        details = {"sequence": i}

        rec_hash = compute_record_hash(
            event_id=r_id,
            timestamp=ts,
            event_type=ev_type,
            actor_id="alice",
            target_resource="transfer",
            details=details,
            prev_record_hash=prev,
        )
        record = {
            "id": r_id,
            "timestamp": ts,
            "event_type": ev_type,
            "actor_id": "alice",
            "target_resource": "transfer",
            "details": details,
            "prev_record_hash": prev,
            "record_hash": rec_hash,
        }
        records.append(record)
        prev = rec_hash

    # Adversary modifies details of record at index 1
    records[1]["details"] = {"sequence": 99999}

    is_valid, broken_idx, reason = verify_chain_records(records)
    assert is_valid is False
    assert broken_idx == 1
    assert "Tampered record content" in reason


@pytest.mark.unit
def test_broken_prev_hash_link_detected() -> None:
    """Modifying prev_record_hash breaks link and fails verification."""
    records = []
    prev = GENESIS_HASH

    for _i in range(3):
        r_id = str(uuid.uuid4())
        ts = datetime.now(UTC)
        ev_type = AuditEventType.AUTH_LOGOUT.value

        rec_hash = compute_record_hash(
            event_id=r_id,
            timestamp=ts,
            event_type=ev_type,
            actor_id="bob",
            target_resource="session",
            details={},
            prev_record_hash=prev,
        )
        record = {
            "id": r_id,
            "timestamp": ts,
            "event_type": ev_type,
            "actor_id": "bob",
            "target_resource": "session",
            "details": {},
            "prev_record_hash": prev,
            "record_hash": rec_hash,
        }
        records.append(record)
        prev = rec_hash

    # Corrupt prev_record_hash at index 2
    records[2]["prev_record_hash"] = "deadbeef" * 8

    is_valid, broken_idx, reason = verify_chain_records(records)
    assert is_valid is False
    assert broken_idx == 2
    assert "Broken chain link" in reason
