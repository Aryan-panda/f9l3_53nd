from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging

logger = setup_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown management."""
    logger.info("Initializing f9l3_53nd application backend...")
    yield
    logger.info("Shutting down f9l3_53nd application backend...")


app = FastAPI(
    title="f9l3_53nd — Secure Authenticated File Transfer Platform",
    description=(
        "Application-layer AES-256-GCM encrypted, SHA-256 verified, "
        "WireGuard network-isolated file transfer system."
    ),
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Standardized Error Handling (No stack trace or secret leakage)
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle custom application and security exceptions."""
    logger.warning(
        "Application error: code=%s, status=%s, msg=%s",
        exc.code,
        exc.status_code,
        exc.message,
    )
    return JSONResponse(

        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler to prevent unhandled internal server errors from leaking details."""
    logger.error("Unhandled internal error: %s", str(exc), exc_info=False)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please contact the administrator.",
            }
        },
    )


# Health & Observability Endpoints
@app.get("/health/live", tags=["Observability"])
async def liveness_probe() -> dict[str, Any]:
    """Liveness probe indicating the HTTP service is running."""
    return {
        "status": "alive",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health/ready", tags=["Observability"])
async def readiness_probe() -> dict[str, Any]:
    """Readiness probe indicating core application dependencies are operational."""
    return {
        "status": "ready",
        "app": settings.APP_NAME,
        "storage": "available",
    }


# Mount API version 1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
