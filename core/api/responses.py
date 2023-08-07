from pydantic import BaseModel

from common.types import APIResponseType


class ExceptionMessageSchema(BaseModel):
    detail: str


class InvalidTokenSchema(BaseModel):
    detail: str = "Token is invalid or expired"

class InvalidCodeSchema(BaseModel):
    detail: str = "Code is invalid or expired"


INVALID_CODE: APIResponseType = {
    400: {"model": InvalidCodeSchema, "description": "Invalid code"}
}

INVALID_TOKEN: APIResponseType = {
    400: {"model": InvalidTokenSchema, "description": "Invalid token"}
}

BAD_REQUEST: APIResponseType = {
    400: {"model": ExceptionMessageSchema, "description": "Bad Request"}
}

UNAUTHORIZED: APIResponseType = {
    401: {"model": ExceptionMessageSchema, "description": "Unauthorized Error"}
}

PERMISSION_DENIED: APIResponseType = {
    403: {"model": ExceptionMessageSchema, "description": "Permission denied"}
}

NOT_FOUND: APIResponseType = {
    404: {"model": ExceptionMessageSchema, "description": "Not found"},
}

CONFLICT: APIResponseType = {
    409: {"model": ExceptionMessageSchema, "description": "Conflict"},
}

SERVICE_UNAVAILABLE: APIResponseType = {
    503: {"model": ExceptionMessageSchema, "description": "3rd party service exception"},
}

CRUD_RESPONSES: APIResponseType = UNAUTHORIZED | PERMISSION_DENIED | NOT_FOUND
