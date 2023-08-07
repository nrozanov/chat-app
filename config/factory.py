import pathlib

from fastapi import FastAPI

from fastapi_pagination import add_pagination

from config import routers
from config.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(
        debug=settings.DEBUG,
        title="Flipside backend API",
    )

    routers.init_app(app)
    add_pagination(app)

    return app
