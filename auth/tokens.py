import secrets
from datetime import datetime

from core.token import ClaimsDict, Token
from models import User


class JWTToken(Token):
    is_abstract: bool = True
    user: User
    algorithm_options = {"require_jti": True}

    @classmethod
    def get_claims(cls, user: User, from_time: datetime) -> ClaimsDict:
        """
        Customize this to populate your custom claims
        """
        return {"email": user.email, "jti": secrets.token_hex()}
