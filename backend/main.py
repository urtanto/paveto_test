import os
from contextlib import asynccontextmanager
from fastapi.datastructures import State

from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app, "state"):
        app.state = State()

    app.state.yandex_client_id = os.getenv("YANDEX_CLIENT_ID")
    app.state.yandex_redirect_uri = os.getenv("YANDEX_REDIRECT_URI")
    print(f"Start...")
    yield
    print("Shutdown...")
app = FastAPI(lifespan=lifespan)



# Callback от Яндекс

