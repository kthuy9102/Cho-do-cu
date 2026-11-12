"""Ngoại lệ nghiệp vụ. Router/service chỉ cần `raise`, handler trung tâm lo phần JSON."""
from typing import Any


class AppError(Exception):
    status_code: int = 400
    code: str = "bad_request"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details
        self.headers = headers


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"


class UnauthorizedError(AppError):
    """401: chưa xác thực / token sai / token hết hạn."""

    status_code = 401
    code = "unauthorized"

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs["headers"] = kwargs.get("headers") or {"WWW-Authenticate": "Bearer"}
        super().__init__(message, **kwargs)


class ForbiddenError(AppError):
    """403: đã xác thực nhưng không đủ quyền."""

    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    """409: dữ liệu hợp lệ nhưng xung đột với trạng thái hiện tại (trùng, sai trạng thái...)."""

    status_code = 409
    code = "conflict"


class PayloadTooLargeError(AppError):
    status_code = 413
    code = "payload_too_large"


class UnsupportedMediaTypeError(AppError):
    status_code = 415
    code = "unsupported_media_type"


class UnprocessableError(AppError):
    """422 do nghiệp vụ gây ra (ví dụ khóa ngoại trong body không tồn tại)."""

    status_code = 422
    code = "unprocessable"


class TooManyRequestsError(AppError):
    status_code = 429
    code = "too_many_requests"
