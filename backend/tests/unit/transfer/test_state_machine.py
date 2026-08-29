import pytest

from app.core.exceptions import TransferStateError
from app.transfer.state_machine import (
    TERMINAL_STATES,
    TransferState,
    TransferStateMachine,
)


@pytest.mark.unit
def test_state_machine_valid_happy_path() -> None:
    """Verify standard happy path transition sequence from INITIALIZED to COMPLETED."""
    sequence = [
        (TransferState.INITIALIZED, TransferState.UPLOADING),
        (TransferState.UPLOADING, TransferState.UPLOADED),
        (TransferState.UPLOADED, TransferState.ENCRYPTING),
        (TransferState.ENCRYPTING, TransferState.ENCRYPTED),
        (TransferState.ENCRYPTED, TransferState.TRANSFERRING),
        (TransferState.TRANSFERRING, TransferState.RECEIVED),
        (TransferState.RECEIVED, TransferState.DECRYPTING),
        (TransferState.DECRYPTING, TransferState.DECRYPTED),
        (TransferState.DECRYPTED, TransferState.INTEGRITY_CHECKING),
        (TransferState.INTEGRITY_CHECKING, TransferState.COMPLETED),
    ]
    for curr, nxt in sequence:
        TransferStateMachine.validate_transition(curr, nxt)


@pytest.mark.unit
def test_state_machine_invalid_skipping_transitions() -> None:
    """Attempting to skip mandatory states must raise TransferStateError."""
    with pytest.raises(TransferStateError, match="Illegal state transition"):
        TransferStateMachine.validate_transition(
            TransferState.INITIALIZED,
            TransferState.COMPLETED,
        )

    with pytest.raises(TransferStateError, match="Illegal state transition"):
        TransferStateMachine.validate_transition(
            TransferState.UPLOADING,
            TransferState.ENCRYPTED,
        )


@pytest.mark.unit
def test_state_machine_terminal_state_immutability() -> None:
    """Transitions from terminal states MUST be rejected."""
    for term_state in TERMINAL_STATES:
        assert TransferStateMachine.is_terminal(term_state) is True
        with pytest.raises(TransferStateError, match="Cannot transition from terminal state"):
            TransferStateMachine.validate_transition(term_state, TransferState.UPLOADING)
