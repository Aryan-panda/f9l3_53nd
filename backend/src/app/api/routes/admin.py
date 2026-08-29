from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin_user, get_db
from app.models.user import User
from app.schemas.audit import (
    AuditChainVerificationResponse,
    AuditEventListResponse,
    AuditEventRead,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Administration & Audit"])


@router.get("/audit-events", response_model=AuditEventListResponse)
async def list_audit_events(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    event_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    actor_id: UUID | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    _: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AuditEventListResponse:
    """Retrieve structured audit event logs with forensic filtering (Admin only)."""
    events, total = await AuditService.list_events(
        db=db,
        offset=offset,
        limit=limit,
        event_type=event_type,
        severity=severity,
        actor_id=actor_id,
        start_time=start_time,
        end_time=end_time,
    )
    return AuditEventListResponse(
        items=[AuditEventRead.model_validate(e) for e in events],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/audit-events/verify", response_model=AuditChainVerificationResponse)
async def verify_audit_chain(
    _: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AuditChainVerificationResponse:
    """Perform on-demand cryptographic verification of the complete audit event
    chain (Admin only).
    """
    is_valid, count, broken_idx, msg = await AuditService.verify_chain_integrity(db)

    return AuditChainVerificationResponse(
        is_valid=is_valid,
        total_records=count,
        broken_record_index=broken_idx,
        message=msg,
    )
