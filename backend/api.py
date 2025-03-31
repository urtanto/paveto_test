from fastapi import APIRouter

from backend.user import user_router
from backend.files import file_router

api_router = APIRouter(prefix="/api", tags=["api"])

api_router.include_router(user_router)
api_router.include_router(file_router)
