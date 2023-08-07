from common.types import ZipCode
import datetime
from datetime import date
from pydantic import BaseModel, validator, Field
from typing import Any, Optional

from models.customer import Genders, Reactions, Kids, Politics, Religion


class GetSignupCodeSchema(BaseModel):
    code: str
    email: str


class GetSigninCodeSchema(BaseModel):
    code: str


class TokenPairSchema(BaseModel):
    access_token: str
    refresh_token: str


class RefreshTokenSchema(BaseModel):
    token: str
