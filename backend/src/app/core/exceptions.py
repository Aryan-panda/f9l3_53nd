from typing import Any


class AppError(Exception):
    """Base domain exception for f9l3_53nd application."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(AppError):
    """Raised when authentication credentials or session verification fails."""

    def __init__(
        self,
        message: str = "Authentication failed.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code="AUTHENTICATION_FAILED", status_code=401, details=details)


class AuthorizationError(AppError):
    """Raised when an authenticated actor lacks permission for an entity or action."""

    def __init__(
        self,
        message: str = "Access denied.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code="AUTHORIZATION_DENIED", status_code=403, details=details)


class ValidationError(AppError):
    """Raised when client input fails syntactic or security policy checks."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="VALIDATION_FAILED", status_code=422, details=details)


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


class ConflictError(AppError):
    """Raised when an operation conflicts with existing resource state or uniqueness."""

    def __init__(
        self,
        message: str = "Resource conflict.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code="CONFLICT", status_code=409, details=details)


class TransferNotFoundError(AppError):
    """Raised when a requested transfer record cannot be located."""

    def __init__(self, transfer_id: str) -> None:
        super().__init__(
            f"Transfer with ID '{transfer_id}' not found.",
            code="TRANSFER_NOT_FOUND",
            status_code=404,
            details={"transfer_id": transfer_id},
        )


class TransferStateError(AppError):
    """Raised when an invalid state transition is attempted on a transfer."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="INVALID_STATE_TRANSITION", status_code=409, details=details)


class CryptoError(AppError):
    """Base exception for cryptographic operations."""

    def __init__(self, message: str = "Cryptographic operation failed.") -> None:
        super().__init__(message, code="CRYPTO_ERROR", status_code=500)


class DecryptionError(CryptoError):
    """Raised when AEAD tag authentication or decryption fails."""

    def __init__(self, message: str = "Ciphertext authentication or decryption failed.") -> None:
        super().__init__(message)
        self.code = "DECRYPTION_FAILED"
        self.status_code = 400


class IntegrityError(AppError):
    """Raised when SHA-256 digest comparison mismatches."""

    def __init__(
        self,
        message: str = "File integrity verification failed (SHA-256 mismatch).",
    ) -> None:
        super().__init__(message, code="INTEGRITY_MISMATCH", status_code=400)


class ReplayError(AppError):
    """Raised when duplicate or expired transfer execution is detected."""

    def __init__(self, message: str = "Replay detected for transfer token or sequence.") -> None:
        super().__init__(message, code="REPLAY_DETECTED", status_code=409)


class StorageError(AppError):
    """Raised when file storage operations or path containment fail."""

    def __init__(self, message: str = "Storage operation failed.") -> None:
        super().__init__(message, code="STORAGE_ERROR", status_code=500)


class RateLimitError(AppError):
    """Raised when client exceeds rate quotas."""

    def __init__(self, message: str = "Rate limit exceeded. Please retry later.") -> None:
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", status_code=429)
