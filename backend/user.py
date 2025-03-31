import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.auth import get_admin, get_user
from database import Database
from database.models import User

user_router = APIRouter(prefix="/user", tags=["user"])


class UserUpdate(BaseModel):
    """
    Модель для обновления данных пользователя.
    """
    name: Optional[str] = Field(None, description="Новое имя пользователя")
    email: Optional[str] = Field(None, description="Новый email пользователя")


class UserResponse(BaseModel):
    """
    Модель ответа с данными пользователя.
    """
    id: str = Field(..., description="Идентификатор пользователя")
    yandex_id: str = Field(..., description="Идентификатор пользователя в Яндекс")
    name: str = Field(..., description="Имя пользователя")
    email: str = Field(..., description="Email пользователя")


class UsersListResponse(BaseModel):
    """
    Модель ответа для списка пользователей.
    """
    users: list[UserResponse] = Field(..., description="Список пользователей")


@user_router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_user)):
    """
    Возвращает данные текущего авторизованного пользователя.
    """
    return UserResponse(
        id=str(user.id),
        yandex_id=user.yandex_id,
        name=user.name,
        email=user.email
    )


@user_router.patch("/me", response_model=UserResponse)
async def patch_me(update: UserUpdate, user: User = Depends(get_user)):
    """
    Обновляет данные текущего пользователя и возвращает обновлённую информацию.
    """
    async with await Database().get_session() as session:
        async with session.begin():
            if update.name:
                user.name = update.name
            if update.email:
                user.email = update.email

            await session.commit()
    return UserResponse(
        id=str(user.id),
        yandex_id=user.yandex_id,
        name=user.name,
        email=user.email
    )


@user_router.get("/all", response_model=UsersListResponse)
async def patch_me(_: User = Depends(get_user)):
    """
    Возвращает список всех пользователей.
    """
    async with await Database().get_session() as session:
        async with session.begin():
            users: list[User] = list(
                (
                    await session.execute(
                        select(User)
                    )
                ).scalars().all()
            )
    return UsersListResponse(
        users=[
            UserResponse(
                id=str(user.id),
                yandex_id=user.yandex_id,
                name=user.name,
                email=user.email
            )
            for user in users
        ]
    )


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user_req(user_id: uuid.UUID, _: User = Depends(get_user)):
    """
    Возвращает данные пользователя по его идентификатору.
    """
    async with await Database().get_session() as session:
        user: User = (
            await session.execute(
                select(User).where(User.id == user_id)
            )
        ).unique().scalar_one_or_none()
        return UserResponse(
            id=str(user.id),
            yandex_id=user.yandex_id,
            name=user.name,
            email=user.email
        )


@user_router.delete("/{user_id}")
async def delete_user(user_id: uuid.UUID, _: User = Depends(get_admin)):
    """
    Удаляет пользователя по его идентификатору. Для выполнения операции требуется статус администратора.
    """
    async with await Database().get_session() as session:
        async with session.begin():
            user_to_delete: User = (
                await session.execute(
                    select(User).where(User.id == user_id)
                )
            ).unique().scalar_one_or_none()

            if not user_to_delete:
                return {"message": "User not found"}

            await session.delete(user_to_delete)
            await session.commit()
    return {"message": "User deleted"}
