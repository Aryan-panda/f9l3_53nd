import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.chain import GENESIS_HASH, compute_record_hash, verify_chain_records
from app.audit.events import AuditEventType, AuditSeverity
from app.models.audit_event import AuditEvent


class AuditService:
    """Application domain service for tamper-evident audit logging and verification."""

    @staticmethod
    async def emit_event(
        db: AsyncSession,
        event_type: AuditEventType | str,
        severity: AuditSeverity | str = AuditSeverity.INFO,
        actor_id: UUID | None = None,
        ip_address: str | None = None,
        target_resource: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Create and chain a new cryptographic audit event record in PostgreSQL.

        Args:
            db: AsyncSession instance.
            event_type: AuditEventType.
            severity: AuditSeverity.
            actor_id: UUID of caller or None for system events.
            ip_address: Client IP address string.
            target_resource: Entity identifier acted upon.
            details: Contextual details dictionary.

        Returns:
            AuditEvent: Persisted chained audit record.
        """
        # 1. Fetch latest existing record from DB or in-memory session pending objects
        prev_hash: str = GENESIS_HASH

        # Check pending uncommitted objects in current session
        for obj in reversed(list(db.new)):
            if isinstance(obj, AuditEvent) and obj.record_hash:
                prev_hash = obj.record_hash
                break

        if prev_hash == GENESIS_HASH:
            latest_stmt = (
                select(AuditEvent.record_hash)
                .order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc())
                .limit(1)
            )
            latest_res = await db.execute(latest_stmt)
            db_prev = latest_res.scalar_one_or_none()
            if db_prev:
                prev_hash = db_prev

        # 2. Assign immutable identifiers and timestamp
        event_id = uuid.uuid4()
        timestamp = datetime.now(UTC)
        ev_type_str = str(event_type.value if hasattr(event_type, "value") else event_type)
        severity_str = str(severity.value if hasattr(severity, "value") else severity)
        clean_details = details or {}

        # 3. Compute HMAC-SHA256 Record Hash
        rec_hash = compute_record_hash(
            event_id=str(event_id),
            timestamp=timestamp,
            event_type=ev_type_str,
            actor_id=str(actor_id) if actor_id else None,
            target_resource=str(target_resource) if target_resource else None,
            details=clean_details,
            prev_record_hash=prev_hash,
        )

        # 4. Create and persist model
        audit_event = AuditEvent(
            id=event_id,
            timestamp=timestamp,
            event_type=ev_type_str,
            severity=severity_str,
            actor_id=actor_id,
            ip_address=ip_address,
            target_resource=target_resource,
            details=clean_details,
            prev_record_hash=prev_hash,
            record_hash=rec_hash,
        )
        db.add(audit_event)
        await db.flush()
        await db.refresh(audit_event)

        return audit_event

    @staticmethod
    async def list_events(
        db: AsyncSession,
        offset: int = 0,
        limit: int = 50,
        event_type: str | None = None,
        severity: str | None = None,
        actor_id: UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[AuditEvent], int]:
        """List audit events with forensic filtering and pagination."""
        base_query = select(AuditEvent)
        count_query = select(func.count(AuditEvent.id))

        if event_type:
            base_query = base_query.where(AuditEvent.event_type == event_type)
            count_query = count_query.where(AuditEvent.event_type == event_type)

        if severity:
            base_query = base_query.where(AuditEvent.severity == severity)
            count_query = count_query.where(AuditEvent.severity == severity)

        if actor_id:
            base_query = base_query.where(AuditEvent.actor_id == actor_id)
            count_query = count_query.where(AuditEvent.actor_id == actor_id)

        if start_time:
            base_query = base_query.where(AuditEvent.timestamp >= start_time)
            count_query = count_query.where(AuditEvent.timestamp >= start_time)

        if end_time:
            base_query = base_query.where(AuditEvent.timestamp <= end_time)
            count_query = count_query.where(AuditEvent.timestamp <= end_time)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one() or 0

        stmt = base_query.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        events = list(result.scalars().all())

        return events, total

    @staticmethod
    async def verify_chain_integrity(
        db: AsyncSession,
    ) -> tuple[bool, int, int | None, str]:
        """Perform on-demand verification of the complete audit log chain.

        Returns:
            tuple[bool, int, int | None, str]: (is_valid, total_records, broken_index, message)
        """
        stmt = select(AuditEvent).order_by(AuditEvent.timestamp.asc(), AuditEvent.id.asc())
        result = await db.execute(stmt)
        records = list(result.scalars().all())

        is_valid, broken_idx, msg = verify_chain_records(records)
        return is_valid, len(records), broken_idx, msg
