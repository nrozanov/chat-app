from pydantic import Field

from config.settings.base import Settings as BaseSettings


class Settings(BaseSettings):
    CORS_ALLOWED_ORIGINS: tuple[str, ...] = ("*",)
    SECRET_KEY = "flipside"
    DEBUG = True
