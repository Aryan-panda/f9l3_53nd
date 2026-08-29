from enum import StrEnum
from uuid import UUID

from app.core.exceptions import AuthorizationError


class UserRole(StrEnum):
    """Role definition for Role-Based Access Control (RBAC)."""

    ADMIN = "ADMIN"
    USER = "USER"


class UserStatus(StrEnum):
    """Account status for state management."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"


def assert_active_status(status: str) -> None:
    """Assert user account status is ACTIVE, raising AuthorizationError otherwise."""
    if status != UserStatus.ACTIVE:
        raise AuthorizationError(f"Account is {status.lower()}. Please contact the administrator.")


def assert_admin_role(role: str) -> None:
    """Assert caller has ADMIN role, raising AuthorizationError otherwise."""
    if role != UserRole.ADMIN:
        raise AuthorizationError("Administrative privileges required for this operation.")


def can_access_transfer(
    user_id: UUID,
    user_role: str,
    sender_id: UUID,
    recipient_id: UUID,
) -> bool:
    """Evaluate if a user is authorized to view or download a transfer.

    Complete Mediation Rule:
        User is SENDER OR User is RECIPIENT OR User is ADMIN

    Args:
        user_id: UUID of caller.
        user_role: Role of caller ('USER' or 'ADMIN').
        sender_id: UUID of transfer sender.
        recipient_id: UUID of transfer recipient.

    Returns:
        bool: True if authorized, False otherwise.
    """
    if user_role == UserRole.ADMIN:
        return True
    return user_id == sender_id or user_id == recipient_id
