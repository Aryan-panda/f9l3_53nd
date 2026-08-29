from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.security.authorization import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\.\-]+$")
    role: UserRole = Field(default=UserRole.USER)


class UserCreate(UserBase):
    """Schema for user account registration/creation."""

    password: str = Field(min_length=12, max_length=128)


class UserUpdateStatus(BaseModel):
    """Schema for updating user account status (Admin only)."""

    status: UserStatus


class UserRead(UserBase):
    """Schema for returning user account profile."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
