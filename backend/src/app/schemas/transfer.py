from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.transfer.state_machine import TransferState


class TransferBase(BaseModel):
    """Base transfer schema."""

    recipient_id: UUID


class TransferCreate(TransferBase):
    """Schema for transfer creation."""

    pass


class TransferRead(TransferBase):
    """Schema for transfer metadata response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sender_id: UUID
    filename: str
    file_size: int
    original_sha256: str
    decrypted_sha256: str | None = None
    state: TransferState
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class TransferListResponse(BaseModel):
    """Paginated list of transfers."""

    items: list[TransferRead]
    total: int
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
