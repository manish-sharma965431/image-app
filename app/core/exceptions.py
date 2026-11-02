"""Custom exceptions + global handlers => one consistent error format:

{"error": {"code": "...", "message": "...", "details": ..., "request_id": "..."}}
"""
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.message = message
        self.details = details


class UnauthorizedError(AppException):
    status_code, code = 401, "unauthorized"


class NotFoundError(AppException):
    status_code, code = 404, "not_found"


class ConflictError(AppException):
    status_code, code = 409, "conflict"


class FileTooLargeError(AppException):
    status_code, code = 413, "file_too_large"


class UnsupportedMediaError(AppException):
    status_code, code = 415, "unsupported_media_type"

class ModelUnavailableError(AppException):
    status_code, code = 503, "model_unavailable"

def error_body(code: str, message: str, details: Any = None, request_id: str | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details, "request_id": request_id}}


def _rid(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning("[%s] %s: %s", _rid(request), exc.code, exc.message)
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.details, _rid(request)),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_body(
                "validation_error", "Invalid request data", jsonable_encoder(exc.errors()), _rid(request)
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body("http_error", str(exc.detail), None, _rid(request)),
        )
