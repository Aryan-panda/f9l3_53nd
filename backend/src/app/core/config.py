from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core Application Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    APP_NAME: str = "f9l3_53nd"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Cryptography & Secrets
    SECRET_KEY: str = Field(
        default="insecure-dev-key-must-be-replaced-in-production-minimum-32-chars",
        description="Session encryption and HMAC secret key",
    )
    MASTER_KEY_HEX: str = Field(
        default="000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
        description="256-bit AES Master Key for Key Wrapping (KEK) in Hex",
    )

    # Session Configuration
    SESSION_COOKIE_NAME: str = "f9l3_session"
    SESSION_EXPIRY_SECONDS: int = 86400  # 24 hours
    SESSION_COOKIE_SECURE: bool = False  # Set True in production over HTTPS
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://f9l3_user:f9l3_password_dev_only@localhost:5432/f9l3_db"
    )

    # Storage Paths and Limits
    STORAGE_BASE_DIR: str = "./storage"
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB default ceiling
    CHUNK_SIZE_BYTES: int = 1024 * 1024  # 1 MB chunk

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # WireGuard Coordinates
    WIREGUARD_BRANCH_A_ENDPOINT: str = "10.50.0.1:51820"
    WIREGUARD_BRANCH_B_ENDPOINT: str = "10.50.0.2:51820"
    WIREGUARD_ALLOWED_IPS: str = "10.50.0.0/24"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
