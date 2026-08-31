from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.transfer import TransferListResponse, TransferRead
from app.security.rate_limit import upload_limiter
from app.services.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post(
    "",
    response_model=TransferRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_transfer(
    recipient_id: UUID = Form(..., description="UUID of recipient user"),
    file: UploadFile = File(..., description="Payload file to encrypt and transfer"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TransferRead:
    """Initiate a secure file transfer: compute SHA-256, encrypt with AES-256-GCM,
    wrap key, and pack envelope.
    """
    upload_limiter.assert_allowed(str(current_user.id))

    service = TransferService()
    transfer = await service.create_and_process_upload(
        db=db,
        sender=current_user,
        recipient_id=recipient_id,
        file=file,
    )
    return TransferRead.model_validate(transfer)


@router.get("", response_model=TransferListResponse)
async def list_transfers(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TransferListResponse:
    """List transfers visible to caller (as sender or recipient, or all if admin)."""
    transfers, total = await TransferService.list_transfers_for_user(
        db=db,
        user=current_user,
        offset=offset,
        limit=limit,
    )
    return TransferListResponse(
        items=[TransferRead.model_validate(t) for t in transfers],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{transfer_id}", response_model=TransferRead)
async def get_transfer_details(
    transfer_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TransferRead:
    """Get metadata and verification status for a specific transfer
    (Complete Mediation enforced).
    """
    transfer = await TransferService.get_transfer_by_id(
        db=db,
        transfer_id=transfer_id,
        user=current_user,
    )
    return TransferRead.model_validate(transfer)


@router.get("/{transfer_id}/download")
async def download_transfer(
    transfer_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download decrypted and verified file payload (AEAD tag + SHA-256 verified)."""
    service = TransferService()
    plaintext, filename = await service.process_download_and_verify(
        db=db,
        transfer_id=transfer_id,
        user=current_user,
    )
    return Response(
        content=plaintext,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(plaintext)),
        },
    )
