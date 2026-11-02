from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppException, UnauthorizedError, error_body
from app.core.security import decode_access_token

PUBLIC_PATHS = {
    "/health", "/docs", "/redoc", "/openapi.json",
    "/api/v1/auth/register", "/api/v1/auth/login",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Rejects any request without a valid Bearer JWT, except PUBLIC_PATHS.
    On success it puts the user id on request.state for the dependencies."""

    async def dispatch(self, request: Request, call_next):
        # CORS preflight requests never carry credentials, so let them through
        if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        try:
            if scheme.lower() != "bearer" or not token:
                raise UnauthorizedError("Missing or malformed Authorization header")
            request.state.user_id = decode_access_token(token)["sub"]
        except AppException as exc:
            # Exceptions raised inside middleware bypass FastAPI handlers, so respond directly
            return JSONResponse(
                status_code=exc.status_code,
                content=error_body(exc.code, exc.message, None, getattr(request.state, "request_id", None)),
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)
