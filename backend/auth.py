import json

import aiohttp
from fastapi import APIRouter, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.responses import RedirectResponse

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


