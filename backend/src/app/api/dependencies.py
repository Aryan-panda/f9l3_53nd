from app.core.config import Settings, get_settings


def get_app_settings() -> Settings:
    """Dependency injection provider for application settings."""
    return get_settings()
