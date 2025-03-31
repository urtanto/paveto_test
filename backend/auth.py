from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

api_router = APIRouter()


@api_router.get("/auth/yandex")
async def auth_yandex(request: Request):
    """
    Перенаправляет пользователя на страницу авторизации Яндекс
    """
    return RedirectResponse(url=(
        f"https://oauth.yandex.ru/authorize?response_type=code"
        f"&client_id={request.app.state.yandex_client_id}&redirect_uri={request.app.state.yandex_redirect_uri}"
    ))


@api_router.get("/auth/yandex/callback")
async def auth_yandex_callback(request: Request, code: str):
    # user_info = await yandex_oauth_callback(code)
    # print(f"user_info: {user_info}")
    return {"access_token": '', "token_type": "bearer"}
