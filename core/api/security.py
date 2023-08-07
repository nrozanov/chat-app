from fastapi import Request, WebSocket
from fastapi.security import HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param

from core.api.exceptions import UnauthorizedError


class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request) -> str:  # type: ignore[override]
        authorization: str = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)

        if not (authorization and scheme and credentials) or scheme.lower() != "bearer":
            raise UnauthorizedError("Not authenticated")
        return credentials


class JWTBearerWS(HTTPBearer):
    async def __call__(self, websocket: WebSocket) -> str:  # type: ignore[override]
        authorization: str = dict(websocket.headers).get("authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)

        if not (authorization and scheme and credentials) or scheme.lower() != "bearer":
            return None
        return credentials
