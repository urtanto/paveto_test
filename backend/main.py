import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.datastructures import State

from auth import auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app, "state"):
        app.state = State()

    app.state.yandex_client_id = os.getenv("YANDEX_CLIENT_ID")
    app.state.yandex_client_secret = os.getenv("YANDEX_CLIENT_SECRET")
    app.state.yandex_redirect_uri = os.getenv("YANDEX_REDIRECT_URI")
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, prefix="/auth", tags=["auth"])

if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
