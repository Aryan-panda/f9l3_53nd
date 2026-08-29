import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class KeyReference(Base):
    """SQLAlchemy model for storing wrapped Data Encryption Keys (DEKs)
    associated with transfers.
    """

    __tablename__ = "key_references"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    transfer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
    )
    wrapped_dek: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )
    key_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="v1",
    )
    algorithm: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="AES-KW-256",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    rotated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
