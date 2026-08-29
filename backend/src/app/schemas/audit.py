from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.audit.events import AuditEventType, AuditSeverity


class AuditEventRead(BaseModel):
    """Schema representing an immutable audit log record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    actor_id: UUID | None = None
    ip_address: str | None = None
    target_resource: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    prev_record_hash: str
    record_hash: str


class AuditEventListResponse(BaseModel):
    """Paginated list of audit events."""

    items: list[AuditEventRead]
    total: int
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class AuditChainVerificationResponse(BaseModel):
    """Result of cryptographic audit log chain verification."""

    is_valid: bool
    total_records: int
    broken_record_index: int | None = None
    message: str
