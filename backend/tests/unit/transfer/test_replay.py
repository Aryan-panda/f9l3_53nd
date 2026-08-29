import uuid

import pytest

from app.core.exceptions import ReplayError
from app.crypto.nonce import generate_nonce
from app.transfer.replay import ReplayDetector


@pytest.mark.unit
def test_replay_detector_allows_unique_transfers() -> None:
    """Verify unique transfers and nonces are recorded cleanly."""
    detector = ReplayDetector(ttl_seconds=3600.0)
    t1 = uuid.uuid4()
    n1 = generate_nonce()

    detector.check_and_record(t1, n1)

    t2 = uuid.uuid4()
    n2 = generate_nonce()
    detector.check_and_record(t2, n2)


@pytest.mark.unit
def test_replay_detector_blocks_duplicate_transfer_id() -> None:
    """Replaying an existing transfer ID must raise ReplayError."""
    detector = ReplayDetector(ttl_seconds=3600.0)
    t_id = uuid.uuid4()

    detector.check_and_record(t_id)

    with pytest.raises(ReplayError, match="Replay detected"):
        detector.check_and_record(t_id)


@pytest.mark.unit
def test_replay_detector_blocks_reused_nonce() -> None:
    """Reusing the same cryptographic nonce must raise ReplayError."""
    detector = ReplayDetector(ttl_seconds=3600.0)
    nonce = generate_nonce()

    detector.check_and_record(uuid.uuid4(), nonce)

    with pytest.raises(ReplayError, match="Cryptographic nonce reuse"):
        detector.check_and_record(uuid.uuid4(), nonce)
