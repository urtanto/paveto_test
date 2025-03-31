from fastapi import APIRouter

from backend.user import user_router

api_router = APIRouter(prefix="/api", tags=["api"])

api_router.include_router(user_router)
