import datetime
import os
import uuid
from typing import Optional

import aiohttp
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import select
from starlette.responses import RedirectResponse

import database
from database import Database
from database.models import User
from backend.auth import get_user, get_admin

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
async def patch_me(user_update: UserUpdate, user: User = Depends(get_user)):
    async with await Database().get_session() as session:
        async with session.begin():
            # user: User = (
            #     await session.execute(
            #         select(User).where(User.id == user.id)
            #     )
            # ).unique().scalar_one_or_none()

            if user_update.name:
                user.name = user_update.username
            if user_update.email:
                user.email = user_update.email

            await session.commit()
    return {
        "id": str(user.id),
        "yandex_id": user.yandex_id,
        "name": user.name,
        "email": user.email
    }
