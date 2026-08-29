from fastapi import APIRouter

from app.api.routes import auth, transfers, users

api_router = APIRouter()

# Plug in feature routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(transfers.router)
