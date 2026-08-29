import hashlib
import time
from threading import Lock
from uuid import UUID

from app.core.exceptions import ReplayError


class ReplayDetector:
    """Detects and prevents payload envelope or transfer token replay attacks."""

    def __init__(self, ttl_seconds: float = 86400.0) -> None:
        """Initialize ReplayDetector with TTL for cached identifiers.

        Args:
            ttl_seconds: How long to retain seen nonces/transfers (default 24 hours).
        """
        self.ttl_seconds = ttl_seconds
        self._seen_transfers: dict[str, float] = {}
        self._seen_nonces: dict[str, float] = {}
        self._lock = Lock()

    def check_and_record(
        self,
        transfer_id: UUID | str,
        nonce: bytes | None = None,
    ) -> None:
        """Check if a transfer ID or cryptographic nonce was previously processed.

        Args:
            transfer_id: UUID or canonical identifier of the transfer.
            nonce: Optional 12-byte AEAD nonce.

        Raises:
            ReplayError: If transfer_id or nonce has been seen within the TTL window.
        """
        now = time.monotonic()
        t_key = str(transfer_id).strip().lower()

        with self._lock:
            # 1. Purge expired entries
            self._cleanup_expired(now)

            # 2. Check transfer ID uniqueness
            if t_key in self._seen_transfers:
                raise ReplayError(
                    f"Replay detected: Transfer '{transfer_id}' was already processed."
                )

            # 3. Check nonce uniqueness if provided
            n_key: str | None = None
            if nonce is not None:
                n_key = hashlib.sha256(nonce).hexdigest()
                if n_key in self._seen_nonces:
                    raise ReplayError("Replay detected: Cryptographic nonce reuse detected.")

            # 4. Record new entries
            self._seen_transfers[t_key] = now
            if n_key is not None:
                self._seen_nonces[n_key] = now

    def _cleanup_expired(self, now: float) -> None:
        cutoff = now - self.ttl_seconds
        expired_transfers = [k for k, ts in self._seen_transfers.items() if ts < cutoff]
        for k in expired_transfers:
            del self._seen_transfers[k]

        expired_nonces = [k for k, ts in self._seen_nonces.items() if ts < cutoff]
        for k in expired_nonces:
            del self._seen_nonces[k]

    def reset(self) -> None:
        """Clear all stored history (useful for test isolation)."""
        with self._lock:
            self._seen_transfers.clear()
            self._seen_nonces.clear()


# Global singleton replay detector
transfer_replay_detector = ReplayDetector()
