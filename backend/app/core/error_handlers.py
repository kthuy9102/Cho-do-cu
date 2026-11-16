"""Mọi lỗi trả về cùng một định dạng:
{"error": {"code": "...", "message": "...", "details": ..., "request_id": "..."}}"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError

logger = logging.getLogger("app.error")

_STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "validation_error",
    429: "too_many_requests",
}


def _rid(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _body(request: Request, code: str, message: str, details=None) -> dict:
    return {"error": {"code": code, "message": message, "details": details, "request_id": _rid(request)}}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    level = logging.WARNING if exc.status_code in (401, 403, 429) else logging.INFO
    logger.log(
        level,
        "app_error",
        extra={"status_code": exc.status_code, "error_code": exc.code, "path": request.url.path},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_body(request, exc.code, exc.message, exc.details),
        headers=exc.headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _STATUS_CODES.get(exc.status_code, f"http_{exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content=_body(request, code, str(exc.detail)),
        headers=getattr(exc, "headers", None),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for err in exc.errors():
        loc = err.get("loc", ())
        details.append(
            {
                "in": str(loc[0]) if loc else None,  # body / query / path
                "field": ".".join(str(p) for p in loc[1:]),
                "message": str(err.get("msg", "")).removeprefix("Value error, "),
                "type": err.get("type"),
            }
        )
    return JSONResponse(
        status_code=422,
        content=_body(request, "validation_error", "Dữ liệu gửi lên không hợp lệ", details),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    rid = _rid(request)
    logger.exception(
        "unhandled_exception",
        extra={"path": request.url.path, "method": request.method, "request_id": rid or "-"},
    )
    # Không lộ chi tiết nội bộ (stack trace, SQL) cho client
    response = JSONResponse(
        status_code=500,
        content=_body(request, "internal_error", "Đã xảy ra lỗi hệ thống, vui lòng thử lại sau"),
    )
    if rid:
        response.headers["X-Request-ID"] = rid
    return response


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
