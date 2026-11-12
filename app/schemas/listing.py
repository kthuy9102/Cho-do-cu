from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import ItemCondition, ListingStatus
from app.schemas.category import CategoryRead
from app.schemas.user import UserBrief


class ListingSort(str, Enum):
    newest = "newest"
    price_asc = "price_asc"
    price_desc = "price_desc"


class ListingImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str


class ListingBrief(BaseModel):
    """Thông tin tối thiểu về tin, nhúng trong offer/report."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: int
    status: ListingStatus
    seller_id: int


class ListingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: int
    condition: ItemCondition
    status: ListingStatus
    reject_reason: str | None
    thumbnail_url: str | None
    category: CategoryRead
    seller: UserBrief
    created_at: datetime


class ListingDetail(ListingSummary):
    description: str
    images: list[ListingImageRead]
    updated_at: datetime


def _clean_text(v: str) -> str:
    return v.strip()


class ListingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")  # không cho client tự gửi status/seller_id

    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    price: int = Field(ge=0, le=1_000_000_000, description="Giá bán, đơn vị VND")
    condition: ItemCondition
    category_id: int = Field(gt=0)

    @field_validator("title", "description")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = _clean_text(v)
        if not v:
            raise ValueError("Không được để trống")
        return v


class ListingUpdate(BaseModel):
    """PATCH: chỉ gửi trường cần đổi."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=5, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    price: int | None = Field(default=None, ge=0, le=1_000_000_000)
    condition: ItemCondition | None = None
    category_id: int | None = Field(default=None, gt=0)

    @field_validator("title", "description")
    @classmethod
    def _strip(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v

    @model_validator(mode="after")
    def _validate_fields(self):
        if not self.model_fields_set:
            raise ValueError("Cần gửi ít nhất một trường để cập nhật")
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"Trường '{name}' không được là null")
        return self


class RejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=5, max_length=500, description="Lý do từ chối, hiển thị cho người đăng")
