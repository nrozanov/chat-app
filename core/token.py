from __future__ import annotations

from calendar import timegm
from datetime import datetime, timedelta
from typing import Any, Sequence, Type, TypeVar

from jose import JWTError, jwt
from jose.constants import ALGORITHMS
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload
from sqlmodel import Session
from sqlmodel.sql.expression import Select, SelectOfScalar, select

from config.settings import settings
from models.user import User

T = TypeVar("T", bound="Token")
ClaimsDict = dict[str, Any]
UserSelect = Select[User] | SelectOfScalar[User]


class TokenError(Exception):
    pass


class TokenMetaClass(type):
    def __new__(mcls, name: str, bases: Any, attrs: dict[str, Any]) -> object:
        is_abstract = attrs.pop("is_abstract", False)
        if not is_abstract:
            if "token_type" not in attrs:
                raise RuntimeError(f"token_type is not specified for {name}")
            if "lifetime" not in attrs:
                raise RuntimeError(f"lifetime is not specified for {name}")
        new_class = super().__new__(mcls, name, bases, attrs)
        return new_class


class Token(metaclass=TokenMetaClass):
    """
    Base class for managing tokens with limited lifespan
    """

    is_abstract: bool = True

    token_type: str
    lifetime: timedelta

    algorithm: str = ALGORITHMS.HS256
    algorithm_options: dict[str, bool | int] = {}

    required_claims: Sequence[str] = ("email",)

    signing_key: str = settings.SECRET_KEY
    error_message = "Token is invalid or expired"

    _token_string: str
    _claims: dict[str, Any]
    user: User

    def __init__(
        self,
        *,
        user: User,
        token_string: str,
        claims: ClaimsDict,
    ):
        self.user = user
        self._token_string = token_string
        self._claims = claims

    def __getitem__(self, key: str) -> Any:
        return self._claims[key]

    def __contains__(self, key: str) -> bool:
        return key in self._claims

    def __str__(self) -> str:
        return self._token_string

    @property
    def claims(self) -> ClaimsDict:
        return self._claims

    @classmethod
    def _calculate_exp(cls, from_time: datetime) -> int:
        dt = from_time + cls.lifetime
        return timegm(dt.utctimetuple())

    @classmethod
    def _encode(cls, claims: ClaimsDict) -> str:
        """
        Return signed JWT token with claims from the instance
        """
        return jwt.encode(claims, cls.signing_key, algorithm=cls.algorithm)

    @classmethod
    def _decode(cls, token_string: str) -> ClaimsDict:
        """
        Decode claims from raw token_string
        """
        try:
            return jwt.decode(
                token_string,
                cls.signing_key,
                algorithms=cls.algorithm,
                options={"require_exp": True} | cls.algorithm_options,
            )
        except JWTError:
            raise TokenError(cls.error_message)

    @classmethod
    def _verify_claims(cls, claims: ClaimsDict) -> None:
        """
        Ensures all necessary claims are present and have correct values
        """
        try:
            token_type = claims["token_type"]
        except KeyError:
            raise TokenError(cls.error_message)

        if token_type != cls.token_type:
            raise TokenError(cls.error_message)

        required_claims = cls.required_claims or []
        for claim in required_claims:
            if claim not in claims:
                raise TokenError(cls.error_message)

        cls.verify_claims(claims)

    @classmethod
    def verify_claims(cls, claims: ClaimsDict) -> None:
        """
        Implement your custom verification for token claims obtained from token string
        """
        pass

    @classmethod
    def _get_user(cls, claims: ClaimsDict, session: Session) -> User:
        query = cls.get_user_query(claims)
        try:
            return session.exec(query).one()
        except NoResultFound:
            raise TokenError(cls.error_message)

    @classmethod
    def _get_claims(cls, *, user: User, from_time: datetime) -> ClaimsDict:
        claims = {
            "token_type": cls.token_type,
            "exp": cls._calculate_exp(from_time),
        }
        claims.update(cls.get_claims(user, from_time))
        return claims

    @classmethod
    def get_claims(cls, user: User, from_time: datetime) -> ClaimsDict:
        """
        Customize this to populate your custom claims
        """
        return {"email": user.email}

    @classmethod
    def from_string(cls: Type[T], token_string: str, session: Session) -> T:
        """
        Verify given token_string and return new token instance
        """
        claims = cls._decode(token_string)
        cls._verify_claims(claims)
        user = cls._get_user(claims, session)

        return cls(user=user, token_string=token_string, claims=claims)

    @classmethod
    def get_user_query(cls, claims: ClaimsDict) -> UserSelect:
        """
        Overwrite this in case you need custom retrieval logic
        """
        return select(User).options(joinedload(User.customer)).where(User.email == claims["email"])

    @classmethod
    def for_user(
        cls: Type[T], user: User, instantiation_time: datetime | None = None
    ) -> T:
        """
        Generate token for a given user
        """
        instantiation_time = instantiation_time or datetime.utcnow()
        claims = cls._get_claims(user=user, from_time=instantiation_time)
        token_string = cls._encode(claims)

        return cls(user=user, token_string=token_string, claims=claims)
