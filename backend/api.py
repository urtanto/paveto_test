import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from backend.auth import get_user, get_admin
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
async def patch_me(_: User = Depends(get_user)):
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

@api_router.delete("/user/{user_id}")
async def delete_user(user_id: str, _: User = Depends(get_admin)):
    async with await Database().get_session() as session:
        async with session.begin():
            user_to_delete: User = (
                await session.execute(
                    select(User).where(User.id == uuid.UUID(user_id))
                )
            ).unique().scalar_one_or_none()

            if not user_to_delete:
                return {"message": "User not found"}

            await session.delete(user_to_delete)
            await session.commit()
    return {"message": "User deleted"}
