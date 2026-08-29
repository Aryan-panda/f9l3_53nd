import uuid
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    AuthorizationError,
    NotFoundError,
    TransferNotFoundError,
    ValidationError,
)
from app.crypto.aead import AES256GCMCipher, build_canonical_aad
from app.crypto.envelope import (
    ALGORITHM_AES_256_GCM,
    CURRENT_PROTOCOL_VERSION,
    TransferEnvelope,
    pack_envelope,
)
from app.crypto.hashing import compute_buffer_sha256
from app.crypto.nonce import generate_nonce
from app.models.key_reference import KeyReference
from app.models.transfer import Transfer
from app.models.user import User
from app.security.authorization import UserRole, UserStatus, can_access_transfer
from app.services.key_service import KeyService
from app.storage.paths import get_encrypted_payload_path, sanitize_filename
from app.transfer.replay import transfer_replay_detector
from app.transfer.state_machine import TransferState


class TransferService:
    """Orchestrates end-to-end secure file transfer ingestion, encryption, and queries."""

    def __init__(self, key_service: KeyService | None = None) -> None:
        self._key_service = key_service or KeyService()

    async def create_and_process_upload(
        self,
        db: AsyncSession,
        sender: User,
        recipient_id: UUID,
        file: UploadFile,
    ) -> Transfer:
        """Process file upload: sanitize, hash, encrypt with AES-256-GCM, wrap key, and store.

        Args:
            db: AsyncSession instance.
            sender: Authenticated User uploading the file.
            recipient_id: UUID of designated recipient.
            file: UploadFile instance.

        Returns:
            Transfer: Persisted transfer record in ENCRYPTED state.

        Raises:
            ValidationError: On missing file or size limit violation.
            NotFoundError: If recipient user does not exist.
        """
        settings = get_settings()

        # 1. Validate Recipient
        stmt = select(User).where(User.id == recipient_id)
        res = await db.execute(stmt)
        recipient = res.scalar_one_or_none()
        if recipient is None:
            raise NotFoundError(f"Recipient user with ID '{recipient_id}' not found.")
        if recipient.status != UserStatus.ACTIVE.value:
            raise ValidationError(f"Recipient account is {recipient.status.lower()}.")

        # 2. Sanitize Filename
        safe_filename = sanitize_filename(file.filename or "unnamed_payload.bin")

        # 3. Read Plaintext & Validate Size
        plaintext = await file.read()
        file_size = len(plaintext)

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValidationError(
                f"File size ({file_size} bytes) exceeds maximum limit "
                f"({settings.MAX_UPLOAD_SIZE_BYTES} bytes)."
            )

        # 4. Generate Transfer UUID
        transfer_id = uuid.uuid4()

        # 5. Compute Pre-transfer SHA-256 Digest
        original_sha256 = compute_buffer_sha256(plaintext)

        # 6. Generate DEK and Wrapped Key Reference
        plaintext_dek, key_ref_create = self._key_service.create_transfer_key(transfer_id)

        # 7. Generate Nonce & Check Replay Detector
        nonce = generate_nonce()
        transfer_replay_detector.check_and_record(transfer_id=transfer_id, nonce=nonce)

        # 8. Build Canonical AAD
        aad = build_canonical_aad(
            protocol_version="f9l3_v1",
            transfer_id=str(transfer_id),
            sender_id=str(sender.id),
            recipient_id=str(recipient_id),
            file_size=file_size,
        )

        # 9. Encrypt Payload with AES-256-GCM
        cipher = AES256GCMCipher(plaintext_dek)
        ciphertext, tag = cipher.encrypt(plaintext=plaintext, nonce=nonce, aad=aad)

        # 10. Pack Binary Transfer Envelope
        envelope = TransferEnvelope(
            protocol_version=CURRENT_PROTOCOL_VERSION,
            algorithm_id=ALGORITHM_AES_256_GCM,
            nonce=nonce,
            tag=tag,
            aad=aad,
            ciphertext=ciphertext,
        )
        packed_payload = pack_envelope(envelope)

        # 11. Write Encrypted Envelope to Path-Traversal Safe Storage
        storage_file_path = get_encrypted_payload_path(transfer_id)
        with open(storage_file_path, "wb") as f:
            f.write(packed_payload)

        # 12. Persist KeyReference in DB
        db_key_ref = KeyReference(
            transfer_id=transfer_id,
            wrapped_dek=key_ref_create.wrapped_dek,
            key_version=key_ref_create.key_version,
            algorithm=key_ref_create.algorithm,
        )
        db.add(db_key_ref)

        # 13. Persist Transfer in DB
        transfer = Transfer(
            id=transfer_id,
            sender_id=sender.id,
            recipient_id=recipient_id,
            filename=safe_filename,
            file_size=file_size,
            original_sha256=original_sha256,
            state=TransferState.ENCRYPTED.value,
            storage_path=str(storage_file_path),
        )
        db.add(transfer)
        await db.flush()
        await db.refresh(transfer)

        return transfer

    @staticmethod
    async def list_transfers_for_user(
        db: AsyncSession,
        user: User,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Transfer], int]:
        """List transfers where user is sender or recipient (or all if admin)."""
        base_query = select(Transfer)
        count_query = select(func.count(Transfer.id))

        if user.role != UserRole.ADMIN.value:
            filter_condition = or_(
                Transfer.sender_id == user.id,
                Transfer.recipient_id == user.id,
            )
            base_query = base_query.where(filter_condition)
            count_query = count_query.where(filter_condition)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one() or 0

        stmt = base_query.order_by(Transfer.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        transfers = list(result.scalars().all())

        return transfers, total

    @staticmethod
    async def get_transfer_by_id(
        db: AsyncSession,
        transfer_id: UUID,
        user: User,
    ) -> Transfer:
        """Fetch transfer details with Complete Mediation authorization check."""
        stmt = select(Transfer).where(Transfer.id == transfer_id)
        result = await db.execute(stmt)
        transfer = result.scalar_one_or_none()

        if transfer is None:
            raise TransferNotFoundError(str(transfer_id))

        # Complete Mediation check (SENDER, RECIPIENT, or ADMIN)
        if not can_access_transfer(
            user_id=user.id,
            user_role=user.role,
            sender_id=transfer.sender_id,
            recipient_id=transfer.recipient_id,
        ):
            raise AuthorizationError("Access denied: You are not authorized to view this transfer.")

        return transfer
