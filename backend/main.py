import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.datastructures import State

from backend.api import api_router
from backend.auth import auth_router
from backend.files import file_router
from database import Database

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app, "state"):
        app.state = State()

    app.state.yandex_client_id = os.getenv("YANDEX_CLIENT_ID")
    app.state.yandex_client_secret = os.getenv("YANDEX_CLIENT_SECRET")
    app.state.yandex_redirect_uri = os.getenv("YANDEX_REDIRECT_URI")
    app.state.jwt_secret = os.getenv("JWT_SECRET")
    app.state.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    app.state.jwt_exp_delta_seconds = int(os.getenv("JWT_EXP_DELTA_SECONDS"))

    await Database().init()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(api_router)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
