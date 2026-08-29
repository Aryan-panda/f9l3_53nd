from enum import StrEnum
from typing import ClassVar

from app.core.exceptions import TransferStateError


class TransferState(StrEnum):
    """15 Formal lifecycle states for secure file transfer."""

    INITIALIZED = "INITIALIZED"
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    ENCRYPTING = "ENCRYPTING"
    ENCRYPTED = "ENCRYPTED"
    TRANSFERRING = "TRANSFERRING"
    RECEIVED = "RECEIVED"
    DECRYPTING = "DECRYPTING"
    DECRYPTED = "DECRYPTED"
    INTEGRITY_CHECKING = "INTEGRITY_CHECKING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


# Terminal states from which no further transitions are permitted
TERMINAL_STATES: set[TransferState] = {
    TransferState.COMPLETED,
    TransferState.FAILED,
    TransferState.QUARANTINED,
    TransferState.REJECTED,
    TransferState.EXPIRED,
}


class TransferStateMachine:
    """State transition validation and lifecycle coordinator."""

    # Explicit allowed state transition graph
    VALID_TRANSITIONS: ClassVar[dict[TransferState, set[TransferState]]] = {
        TransferState.INITIALIZED: {
            TransferState.UPLOADING,
            TransferState.FAILED,
            TransferState.REJECTED,
        },
        TransferState.UPLOADING: {
            TransferState.UPLOADED,
            TransferState.FAILED,
            TransferState.REJECTED,
        },
        TransferState.UPLOADED: {
            TransferState.ENCRYPTING,
            TransferState.FAILED,
            TransferState.REJECTED,
        },
        TransferState.ENCRYPTING: {
            TransferState.ENCRYPTED,
            TransferState.FAILED,
            TransferState.QUARANTINED,
        },
        TransferState.ENCRYPTED: {
            TransferState.TRANSFERRING,
            TransferState.FAILED,
            TransferState.EXPIRED,
        },
        TransferState.TRANSFERRING: {
            TransferState.RECEIVED,
            TransferState.FAILED,
            TransferState.REJECTED,
        },
        TransferState.RECEIVED: {
            TransferState.DECRYPTING,
            TransferState.FAILED,
            TransferState.QUARANTINED,
        },
        TransferState.DECRYPTING: {
            TransferState.DECRYPTED,
            TransferState.FAILED,
            TransferState.QUARANTINED,
        },
        TransferState.DECRYPTED: {
            TransferState.INTEGRITY_CHECKING,
            TransferState.FAILED,
            TransferState.QUARANTINED,
        },
        TransferState.INTEGRITY_CHECKING: {
            TransferState.COMPLETED,
            TransferState.QUARANTINED,
            TransferState.FAILED,
        },
        # Terminal states have empty target transition sets
        TransferState.COMPLETED: set(),
        TransferState.FAILED: set(),
        TransferState.QUARANTINED: set(),
        TransferState.REJECTED: set(),
        TransferState.EXPIRED: set(),
    }

    @classmethod
    def validate_transition(
        cls,
        current_state: TransferState | str,
        target_state: TransferState | str,
    ) -> None:
        """Validate that a requested state transition is legally permissible.

        Args:
            current_state: Existing state of the transfer.
            target_state: Proposed target state.

        Raises:
            TransferStateError: If the transition is illegal or attempted from a terminal state.
        """
        curr = TransferState(current_state)
        target = TransferState(target_state)

        if curr in TERMINAL_STATES:
            raise TransferStateError(
                f"Cannot transition from terminal state '{curr}' to '{target}'.",
                details={"current_state": curr, "target_state": target},
            )

        allowed_targets = cls.VALID_TRANSITIONS.get(curr, set())
        if target not in allowed_targets:
            raise TransferStateError(
                f"Illegal state transition from '{curr}' to '{target}'. "
                f"Allowed target states: {[s.value for s in allowed_targets]}.",
                details={"current_state": curr, "target_state": target},
            )

    @classmethod
    def is_terminal(cls, state: TransferState | str) -> bool:
        """Check if a state is terminal."""
        return TransferState(state) in TERMINAL_STATES
