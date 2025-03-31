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
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": request.app.state.yandex_client_id,
        "client_secret": request.app.state.yandex_client_secret,
        "redirect_uri": request.app.state.yandex_redirect_uri,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        # "Authorization": f"Basic {ba}",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, headers=headers, json=data) as response:
            print(await response.text())
            print(response.status)
            if response.status == 200:
                token_data = await response.json()
                print(json.dumps(token_data, indent=2))
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in")
                if access_token:
                    return {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_in": expires_in,
                        "token_type": "bearer"
                    }
            else:
                raise HTTPException(status_code=401, detail="Failed to retrieve access token")

