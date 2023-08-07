from typing import Any, Optional

import fastapi
from starlette import status


class _HTTPException(fastapi.HTTPException):
    status_code: int
    detail: Any = None
    headers: Optional[dict[str, Any]] = None

    def __init__(
        self,
        detail: Any = None,
        headers: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail,
            headers=headers or self.headers,
        )


class BadRequestError(_HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail: str


class NotFoundError(_HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Requested resource cannot be found"


class UnauthorizedError(_HTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid credentials"
    headers = {"WWW-Authenticate": "Bearer"}


class PermissionDeniedError(_HTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permission denied"
    headers = {"WWW-Authenticate": "Bearer"}
