import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from backend.auth import get_admin, get_user
from database import Database
from database.models import User

user_router = APIRouter(prefix="/user", tags=["user"])


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


@user_router.get("/me")
async def get_me(user: User = Depends(get_user)):
    return {
        "id": str(user.id),
        "yandex_id": user.yandex_id,
        "name": user.name,
        "email": user.email
    }


@user_router.patch("/me")
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


@user_router.get("/all")
async def patch_me(_: User = Depends(get_user)):
    async with await Database().get_session() as session:
        async with session.begin():
            users: list[User] = list(
                (
                    await session.execute(
                        select(User)
                    )
                ).scalars().all()
            )
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


@user_router.get("/{user_id}")
async def get_user_req(user_id: str, _: User = Depends(get_user)):
    async with await Database().get_session() as session:
        user: User = (
            await session.execute(
                select(User).where(User.id == uuid.UUID(user_id))
            )
        ).unique().scalar_one_or_none()
        return {
            "id": str(user.id),
            "yandex_id": user.yandex_id,
            "name": user.name,
            "email": user.email
        }


@user_router.delete("/{user_id}")
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
