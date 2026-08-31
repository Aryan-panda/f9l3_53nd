import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.security.authorization import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\.\-]+$")
    role: UserRole = Field(default=UserRole.USER)


class UserCreate(UserBase):
    """Schema for user account registration/creation."""

    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Enforce password complexity: uppercase, lowercase, digit, and special character."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+/\\~`]", v):
            raise ValueError("Password must contain at least one special character.")
        return v



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
