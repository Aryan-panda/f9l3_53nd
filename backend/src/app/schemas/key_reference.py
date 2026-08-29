from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class KeyReferenceBase(BaseModel):
    """Base schema for key references."""

    key_version: str = Field(default="v1", description="Identifier of the KEK version used")
    algorithm: str = Field(default="AES-KW-256", description="Key wrapping algorithm")


class KeyReferenceCreate(KeyReferenceBase):
    """Schema for creating a key reference."""

    transfer_id: UUID
    wrapped_dek: bytes


class KeyReferenceRead(KeyReferenceBase):
    """Schema for reading key reference metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    transfer_id: UUID
    created_at: datetime
    rotated_at: datetime | None = None
