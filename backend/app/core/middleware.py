import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging_config import request_id_ctx

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Gán request_id, đo thời gian và log mỗi request đúng một dòng."""

    async def dispatch(self, request: Request, call_next):
        rid = (request.headers.get("x-request-id") or "").strip()[:64] or uuid.uuid4().hex
        request.state.request_id = rid
        token = request_id_ctx.set(rid)
        start = time.perf_counter()
        client_ip = request.client.host if request.client else None
        try:
            response = await call_next(request)
        except Exception:
            self._log(request, 500, start, client_ip)
            raise
        else:
            response.headers["X-Request-ID"] = rid
            self._log(request, response.status_code, start, client_ip)
            return response
        finally:
            request_id_ctx.reset(token)

    @staticmethod
    def _log(request: Request, status_code: int, start: float, client_ip: str | None) -> None:
        if request.url.path == "/health":
            level = logging.DEBUG
        elif status_code >= 500:
            level = logging.ERROR
        else:
            level = logging.INFO
        logger.log(
            level,
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1),
                "client_ip": client_ip,
            },
        )
