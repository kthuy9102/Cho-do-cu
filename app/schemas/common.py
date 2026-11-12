from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(description="Tổng số bản ghi thỏa điều kiện")
    page: int
    page_size: int
    pages: int


class Message(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    code: str = Field(examples=["not_found"], description="Mã lỗi máy đọc được, ổn định")
    message: str = Field(description="Thông báo cho người dùng")
    details: Any | None = Field(default=None, description="Chi tiết, ví dụ danh sách trường sai (lỗi 422)")
    request_id: str | None = Field(default=None, description="Dùng để tra log")


class ErrorResponse(BaseModel):
    error: ErrorDetail


_DESCRIPTIONS = {
    400: "Yêu cầu không hợp lệ",
    401: "Chưa đăng nhập hoặc token sai/hết hạn",
    403: "Không đủ quyền",
    404: "Không tìm thấy tài nguyên",
    409: "Xung đột với trạng thái hiện tại",
    413: "Tệp quá lớn",
    415: "Định dạng tệp không được hỗ trợ",
    422: "Dữ liệu không hợp lệ",
    429: "Gửi quá nhiều yêu cầu",
}


def error_responses(*codes: int) -> dict[int | str, dict[str, Any]]:
    """Khai báo các mã lỗi có thể xảy ra để Swagger hiển thị đầy đủ."""
    return {c: {"model": ErrorResponse, "description": _DESCRIPTIONS[c]} for c in codes}
