from fastapi.applications import FastAPI

import auth.api.routes
import chat.api.routes


def init_app(app: FastAPI) -> None:
    app.include_router(
        auth.api.routes.router,
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        chat.api.routes.router,
        prefix="/chat",
        tags=["chat"],
    )
