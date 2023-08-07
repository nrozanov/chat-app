from sqlalchemy.orm import joinedload
from sqlmodel import select

from auth.tokens import JWTToken
from config.settings import settings
from core.token import ClaimsDict, Token, UserSelect
from models import User


class UserAccessToken(JWTToken):
    token_type = "user_access"
    lifetime = settings.USER_ACCESS_TOKEN_LIFETIME

    @classmethod
    def get_user_query(cls, claims: ClaimsDict) -> UserSelect:
        return (
            select(User)
            .where(User.email == claims["email"])
        )


class UserRefreshToken(JWTToken):  # TODO: Blacklist
    token_type = "user_refresh"
    lifetime = settings.USER_REFRESH_TOKEN_LIFETIME
