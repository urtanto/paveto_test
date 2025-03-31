import datetime

import aiohttp
import jwt
from fastapi import APIRouter, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from starlette.responses import RedirectResponse

from database import Database
from database.models import User

auth_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/yandex")


@auth_router.get("/yandex")
async def auth_yandex(request: Request):
    return RedirectResponse(url=(
        f"https://oauth.yandex.ru/authorize?response_type=code"
        f"&client_id={request.app.state.yandex_client_id}&redirect_uri={request.app.state.yandex_redirect_uri}"
    ))


@auth_router.get("/yandex/callback")
async def auth_yandex_callback(request: Request, code: str):
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
                print(user_info)
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
        "sub": user.id,
        "exp": datetime.datetime.now(datetime.timezone.utc) +
               datetime.timedelta(seconds=request.app.state.yandex_exp_delta_seconds),
    }
    internal_token = jwt.encode(payload, request.app.state.jwt_secret, algorithm=request.app.state.jwt_algorithm)
    return {"access_token": internal_token, "token_type": "bearer"}
