import datetime
import os
import uuid

import aiohttp
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from starlette.responses import RedirectResponse

from database import Database
from database.models import User

auth_router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/yandex")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT токен для доступа")
    token_type: str = Field("bearer", description="Тип токена (обычно 'bearer')")


@auth_router.get("/yandex")
async def auth_yandex(request: Request):
    """
    Перенаправляет пользователя для авторизации через Яндекс OAuth.
    """
    return RedirectResponse(url=(
        f"https://oauth.yandex.ru/authorize?response_type=code"
        f"&client_id={request.app.state.yandex_client_id}&redirect_uri={request.app.state.yandex_redirect_uri}"
    ))


@auth_router.get("/yandex/callback", response_model=TokenResponse)
async def auth_yandex_callback(request: Request, code: str):
    """
    Обрабатывает callback от Яндекс OAuth.

    После получения кода авторизации происходит обмен этого кода на access_token через API Яндекса.
    Затем с помощью полученного токена запрашивается информация о пользователе.
    Если пользователь с таким Yandex ID отсутствует в базе, он создается.
    В конце генерируется и возвращается внутренний JWT токен для дальнейшей аутентификации.
    """
    token_url = "https://oauth.yandex.com/token"

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": request.app.state.yandex_client_id,
        "client_secret": request.app.state.yandex_client_secret,
        "redirect_uri": request.app.state.yandex_redirect_uri,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, headers=headers, data=data) as response:
            if response.status == 200:
                token_data = await response.json()
                access_token = token_data.get("access_token")
            else:
                raise HTTPException(status_code=401, detail="Yandex token exchange failed")

        user_info_url = "https://login.yandex.ru/info"
        headers = {"Authorization": f"OAuth {access_token}"}
        async with session.get(user_info_url, headers=headers) as response:
            if response.status == 200:
                user_info = await response.json()
            else:
                raise HTTPException(status_code=401, detail="Yandex user info retrieval failed")

    async with await Database().get_session() as session:
        async with session.begin():
            user: User = (
                await session.execute(
                    select(User).where(User.yandex_id == user_info.get("id"))
                )
            ).unique().scalar_one_or_none()

            if not user:
                user = User(
                    yandex_id=user_info.get("id"),
                    email=user_info.get("default_email"),
                    name=user_info.get("display_name"),
                )
                session.add(user)
                await session.commit()

    payload = {
        "sub": str(user.id),
        "exp": datetime.datetime.now(datetime.timezone.utc) +
               datetime.timedelta(seconds=request.app.state.jwt_exp_delta_seconds),
    }
    internal_token = jwt.encode(payload, request.app.state.jwt_secret, algorithm=request.app.state.jwt_algorithm)
    return TokenResponse(access_token=internal_token, token_type="bearer")


async def get_user(token: str = Depends(oauth2_scheme)):
    """
    Зависимость для получения текущего пользователя на основе JWT токена.

    Декодирует токен, проверяет его валидность и срок действия, а затем извлекает пользователя из базы данных.
    Если токен недействителен, просрочен или пользователь не найден, выбрасывается HTTPException.
    """
    jwt_secret = os.getenv("JWT_SECRET")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        user_id = uuid.UUID(payload.get("sub"))
        exp = payload.get("exp")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        if datetime.datetime.fromtimestamp(exp, tz=datetime.timezone.utc) < datetime.datetime.now(
                datetime.timezone.utc):
            raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    async with await Database().get_session() as session:
        async with session.begin():
            user: User = (
                await session.execute(
                    select(User).where(User.id == user_id)
                )
            ).unique().scalar_one_or_none()
            if user is None:
                raise HTTPException(status_code=401, detail="Unauthorized")
    return user


async def get_admin(user: User = Depends(get_user)):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return user


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, user: User = Depends(get_user)):
    """
    Обновляет JWT токен для авторизованного пользователя.
    """
    payload = {
        "sub": str(user.id),
        "exp": datetime.datetime.now(datetime.timezone.utc) +
               datetime.timedelta(seconds=request.app.state.jwt_exp_delta_seconds),
    }
    new_token = jwt.encode(payload, request.app.state.jwt_secret, algorithm=request.app.state.jwt_algorithm)
    return TokenResponse(access_token=new_token, token_type="bearer")
