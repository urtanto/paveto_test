from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from backend.auth import get_user
from database import Database
from database.models import User

api_router = APIRouter()


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


@api_router.get("/me")
async def get_me(user: User = Depends(get_user)):
    return {
        "id": str(user.id),
        "yandex_id": user.yandex_id,
        "name": user.name,
        "email": user.email
    }


@api_router.patch("/me")
async def patch_me(update: UserUpdate, user: User = Depends(get_user)):
    async with await Database().get_session() as session:
        async with session.begin():
            if update.name:
                user.name = update.name
            if update.email:
                user.email = update.email

            await session.commit()
    return {
        "id": str(user.id),
        "yandex_id": user.yandex_id,
        "name": user.name,
        "email": user.email
    }


@api_router.get("/users")
async def patch_me(user: User = Depends(get_user)):
    async with await Database().get_session() as session:
        async with session.begin():
            users: list[User] = list((
                await session.execute(
                    select(User)
                )
            ).scalars().all())
    return {
        "users": [
            {
                "id": str(user.id),
                "yandex_id": user.yandex_id,
                "name": user.name,
                "email": user.email
            } for user in users
        ]
    }
