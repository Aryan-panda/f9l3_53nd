from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.schemas.user import UserCreate
from app.security.authorization import UserStatus
from app.security.password import hash_password


class UserService:
    """Application domain service for User lifecycle management."""

    @staticmethod
    async def create_user(
        db: AsyncSession,
        user_in: UserCreate,
    ) -> User:
        """Register a new user account with Argon2id hashed password.

        Args:
            db: AsyncSession instance.
            user_in: UserCreate schema with username, plaintext password, role.

        Returns:
            User: Created database user record.

        Raises:
            ConflictError: If username is already registered.
        """
        # 1. Check uniqueness
        stmt = select(User).where(func.lower(User.username) == user_in.username.lower())
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise ConflictError(f"Username '{user_in.username}' is already taken.")

        # 2. Hash password with Argon2id
        pwd_hash = hash_password(user_in.password)

        # 3. Create model
        user = User(
            username=user_in.username,
            password_hash=pwd_hash,
            role=user_in.role.value,
            status=UserStatus.ACTIVE.value,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: UUID) -> User | None:
        """Fetch user by primary UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        """Fetch user by case-insensitive username."""
        stmt = select(User).where(func.lower(User.username) == username.lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_users(
        db: AsyncSession,
        offset: int = 0,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> tuple[list[User], int]:
        """List users with pagination and optional status filtering."""
        base_query = select(User)
        count_query = select(func.count(User.id))

        if status_filter:
            base_query = base_query.where(User.status == status_filter)
            count_query = count_query.where(User.status == status_filter)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one() or 0

        stmt = base_query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        users = list(result.scalars().all())

        return users, total

    @staticmethod
    async def update_status(
        db: AsyncSession,
        user_id: UUID,
        new_status: str,
    ) -> User:
        """Update a user's account state (ACTIVE, SUSPENDED, DISABLED)."""
        user = await UserService.get_by_id(db, user_id)
        if user is None:
            raise NotFoundError(f"User with ID '{user_id}' not found.")

        user.status = new_status
        await db.flush()
        await db.refresh(user)
        return user
