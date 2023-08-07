from pydantic.fields import Field
from typing import Any

from config.settings.base import Settings as BaseSettings


class Settings(BaseSettings):
    CORS_ALLOWED_ORIGINS: tuple[str, ...] = ()
    DEBUG = True

    SECRET_KEY = "test"
    SERVER_NAME = "testserver.localdomain"

    SQLALCHEMY_DATABASE_URI = Field(
        "postgresql://flipside:flipside@localhost/flipside_test",
        env=["TEST_DATABASE_URL"],
    )
