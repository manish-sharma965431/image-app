import time
import uuid
from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import error_body
from app.core.logger import get_logger

logger = get_logger("api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs request time, API, status and response time. Also the last line of
    defence: any unhandled exception becomes a clean 500 (stack trace only in logs)."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        client = request.client.host if request.client else "-"
        received_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        start = time.perf_counter()

        logger.info("[%s] --> %s %s | client=%s | request_time=%s",
                    request_id, request.method, request.url.path, client, received_at)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("[%s] Unhandled error on %s %s", request_id, request.method, request.url.path)
            response = JSONResponse(
                status_code=500,
                content=error_body("internal_error", "Something went wrong", None, request_id),
            )

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-ms"] = f"{duration_ms:.2f}"
        logger.info("[%s] <-- %s %s | status=%d | response_time=%.2fms",
                    request_id, request.method, request.url.path, response.status_code, duration_ms)
        return response
