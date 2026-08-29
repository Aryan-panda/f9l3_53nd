import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Set testing environment variables before importing settings/app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-chars-long-testing-only"
os.environ["MASTER_KEY_HEX"] = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"

from app.api.dependencies import get_db
from app.core.database import create_all_tables, drop_all_tables
from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate, UserRole, UserStatus
from app.security.rate_limit import login_limiter
from app.services.user_service import UserService
from app.transfer.replay import transfer_replay_detector


@pytest_asyncio.fixture(autouse=True)
def reset_security_state() -> None:
    """Reset in-memory rate limiters and replay detectors before each test."""
    login_limiter.reset()
    transfer_replay_detector.reset()


@pytest_asyncio.fixture(scope="session")

async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Provide session-scoped SQLite in-memory async engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide function-scoped fresh database session with tables created and dropped."""
    await create_all_tables(test_engine)
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()

    await drop_all_tables(test_engine)


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client fixture with database dependency overridden to test DB session."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession) -> User:
    """Create and return standard test user."""
    return await UserService.create_user(
        db=db_session,
        user_in=UserCreate(
            username="alice_branch_a",
            password="StrongPassword123!",
            role=UserRole.USER,
        ),
    )


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create and return admin test user."""
    return await UserService.create_user(
        db=db_session,
        user_in=UserCreate(
            username="security_admin",
            password="AdminMasterPassword123!",
            role=UserRole.ADMIN,
        ),
    )


@pytest_asyncio.fixture
async def suspended_user(db_session: AsyncSession) -> User:
    """Create and return suspended test user."""
    user = await UserService.create_user(
        db=db_session,
        user_in=UserCreate(
            username="suspended_charlie",
            password="StrongPassword123!",
            role=UserRole.USER,
        ),
    )
    return await UserService.update_status(db_session, user.id, UserStatus.SUSPENDED.value)
