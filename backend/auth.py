from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

auth_router = APIRouter()


@auth_router.get("/yandex")
async def auth_yandex(request: Request):
    print(request.app.state.yandex_client_id)
    return RedirectResponse(url=(
        f"https://oauth.yandex.ru/authorize?response_type=code"
        f"&client_id={request.app.state.yandex_client_id}&redirect_uri={request.app.state.yandex_redirect_uri}"
    ))


@auth_router.get("/yandex/callback")
async def auth_yandex_callback(request: Request, code: str):
    # user_info = await yandex_oauth_callback(code)
    # print(f"user_info: {user_info}")
    print(code)
    print(await request.json())
    return {"access_token": '', "token_type": "bearer"}
