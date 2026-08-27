import pytest
from httpx import AsyncClient

from app.core.config import get_settings
from app.core.exceptions import ValidationError


@pytest.mark.unit
async def test_liveness_probe(async_client: AsyncClient) -> None:
    """Verify that the /health/live endpoint returns 200 and expected status."""
    response = await async_client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert data["app"] == "f9l3_53nd"


@pytest.mark.unit
async def test_readiness_probe(async_client: AsyncClient) -> None:
    """Verify that the /health/ready endpoint returns 200 and expected status."""
    response = await async_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.unit
def test_settings_configuration() -> None:
    """Verify that application settings load properly from environment."""
    settings = get_settings()
    assert settings.APP_NAME == "f9l3_53nd"
    assert len(settings.MASTER_KEY_HEX) == 64
    assert len(settings.SECRET_KEY) >= 32


@pytest.mark.unit
def test_app_error_structure() -> None:
    """Verify custom exception representation and metadata mapping."""
    err = ValidationError("Invalid file extension", details={"ext": ".exe"})
    assert err.code == "VALIDATION_FAILED"
    assert err.status_code == 422
    assert err.details["ext"] == ".exe"
