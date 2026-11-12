from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import Role

_STUDENT_ID_PATTERN = r"^[A-Za-z0-9]+$"


def clean_name(value: str) -> str:
    value = " ".join(value.split())
    if len(value) < 2:
        raise ValueError("Họ tên quá ngắn")
    return value


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class UserRead(UserBrief):
    email: str
    student_id: str | None
    role: Role
    is_active: bool
    created_at: datetime


class UserPublic(BaseModel):
    """Hồ sơ công khai của người bán: không có email, vai trò."""

    id: int
    full_name: str
    created_at: datetime
    rating_avg: float | None = Field(description="Điểm uy tín trung bình 1-5; null nếu chưa có đánh giá")
    review_count: int
    active_listing_count: int


class UserUpdate(BaseModel):
    """PATCH /users/me. KHÔNG có email/role/is_active: người dùng không tự nâng quyền được."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    student_id: str | None = Field(default=None, max_length=20, pattern=_STUDENT_ID_PATTERN)

    @field_validator("full_name")
    @classmethod
    def _name(cls, v: str | None) -> str | None:
        return clean_name(v) if v is not None else v

    @model_validator(mode="after")
    def _not_empty(self):
        if not self.model_fields_set:
            raise ValueError("Cần gửi ít nhất một trường để cập nhật")
        if "full_name" in self.model_fields_set and self.full_name is None:
            raise ValueError("full_name không được là null")
        return self


class UserRoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role


class UserActiveUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool
