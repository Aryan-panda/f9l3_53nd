from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.session import Session
from app.models.user import User
from app.security.authorization import UserStatus
from app.security.password import verify_password
from app.security.sessions import (
    compute_session_expiry,
    generate_session_token,
    hash_session_token,
)

# Constant dummy hash for timing attack mitigation when username is not found
DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQxNnNldXJl$"
    "fK4z3o+4Yp07W0c4F7c5f8g9h1j2k3l4m5n6o7p8q9r="
)


class AuthService:
    """Authentication and session lifecycle service."""

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> tuple[User, str]:
        """Authenticate user credentials and establish a new server-side session.

        Mitigates username enumeration and timing attacks by performing
        a dummy verification pass if the username is not found.

        Args:
            db: AsyncSession instance.
            username: Plaintext username.
            password: User-provided plaintext password.

        Returns:
            tuple[User, str]: (User_model, raw_session_token_for_cookie)

        Raises:
            AuthenticationError: On invalid credentials.
            AuthorizationError: If user account is suspended or disabled.
        """
        # 1. Look up user
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        # 2. Timing-safe verification
        if user is None:
            # Execute dummy verify to ensure constant time execution
            verify_password(password, DUMMY_HASH)
            raise AuthenticationError("Invalid username or password.")

        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username or password.")

        # 3. Check account status
        if user.status != UserStatus.ACTIVE.value:
            raise AuthorizationError(
                f"Account is {user.status.lower()}. Please contact the administrator."
            )

        # 4. Generate 256-bit session token
        raw_token = generate_session_token()
        token_hash = hash_session_token(raw_token)
        expiry = compute_session_expiry()

        session = Session(
            user_id=user.id,
            session_token_hash=token_hash,
            expires_at=expiry,
        )
        db.add(session)

        # Update last login timestamp
        user.last_login_at = datetime.now(UTC)
        await db.flush()

        return user, raw_token

    @staticmethod
    async def validate_session(
        db: AsyncSession,
        raw_token: str,
    ) -> tuple[User, Session] | None:
        """Validate a raw session token and return the associated user and session record.

        Args:
            db: AsyncSession instance.
            raw_token: Raw session token from cookie.

        Returns:
            tuple[User, Session] | None: Active User and Session if valid, None otherwise.
        """
        if not raw_token:
            return None

        token_hash = hash_session_token(raw_token)
        now = datetime.now(UTC)

        stmt = (
            select(Session, User)
            .join(User, Session.user_id == User.id)
            .where(
                Session.session_token_hash == token_hash,
                Session.revoked_at.is_(None),
                Session.expires_at > now,
            )
        )
        result = await db.execute(stmt)
        row = result.first()

        if row is None:
            return None

        session, user = row
        # Update last seen timestamp
        session.last_seen_at = now
        await db.flush()

        return user, session

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        raw_token: str,
    ) -> bool:
        """Revoke an active session token on server logout.

        Args:
            db: AsyncSession instance.
            raw_token: Raw session token string.

        Returns:
            bool: True if session was found and revoked, False otherwise.
        """
        if not raw_token:
            return False

        token_hash = hash_session_token(raw_token)
        stmt = select(Session).where(
            Session.session_token_hash == token_hash,
            Session.revoked_at.is_(None),
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if session is None:
            return False

        session.revoked_at = datetime.now(UTC)
        await db.flush()
        return True
