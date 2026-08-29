from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_active_user,
    get_current_admin_user,
    get_db,
)
from app.models.user import User
from app.schemas.user import UserRead, UserUpdateStatus
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserRead:
    """Retrieve profile of currently authenticated user."""
    return UserRead.model_validate(current_user)


@router.get("", response_model=dict[str, Any])
async def list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status: str | None = Query(default=None),
    _: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List all registered user accounts with pagination (Admin only)."""
    users, total = await UserService.list_users(
        db=db,
        offset=offset,
        limit=limit,
        status_filter=status,
    )
    return {
        "items": [UserRead.model_validate(u) for u in users],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.patch("/{user_id}/status", response_model=UserRead)
async def update_user_status(
    user_id: UUID,
    status_update: UserUpdateStatus,
    _: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Update user account status (ACTIVE, SUSPENDED, DISABLED) (Admin only)."""
    updated_user = await UserService.update_status(
        db=db,
        user_id=user_id,
        new_status=status_update.status.value,
    )
    return UserRead.model_validate(updated_user)
