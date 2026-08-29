import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.audit.chain import GENESIS_HASH
from app.audit.events import AuditEventType, AuditSeverity
from app.models.base import Base


class AuditEvent(Base):
    """SQLAlchemy model for tamper-evident chained security audit events."""

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=AuditEventType.AUTH_LOGIN_SUCCESS.value,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AuditSeverity.INFO.value,
        index=True,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    target_resource: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    prev_record_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=GENESIS_HASH,
    )
    record_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
