import aiohttp
from fastapi import APIRouter, Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.responses import RedirectResponse

auth_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/yandex")

@auth_router.get("/yandex")
async def auth_yandex(request: Request):
    print(request.app.state.yandex_client_id)
    return RedirectResponse(url=(
        f"https://oauth.yandex.ru/authorize?response_type=code"
        f"&client_id={request.app.state.yandex_client_id}&redirect_uri={request.app.state.yandex_redirect_uri}"
    ))


@auth_router.get("/yandex/callback")
async def auth_yandex_callback(request: Request, code: str):
    token_url = "https://oauth.yandex.com/"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": request.app.state.yandex_client_id,
        "client_secret": request.app.state.yandex_client_secret,
        "redirect_uri": request.app.state.yandex_redirect_uri,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, data=data) as response:
            if response.status == 200:
                token_data = await response.json()
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

