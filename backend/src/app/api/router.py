from fastapi import APIRouter

api_router = APIRouter()

# Note: Route modules (auth, users, transfers, files, admin) will be plugged in
# sequentially in Phases 7, 8, 9, 10, 12 as defined in the architectural blueprint.
