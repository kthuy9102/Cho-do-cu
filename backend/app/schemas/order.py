from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import OrderStatus
from app.schemas.listing import ListingBrief
from app.schemas.user import UserBrief


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delivery_name: str = Field(min_length=2, max_length=100)
    delivery_phone: str = Field(min_length=9, max_length=20)
    delivery_address: str = Field(min_length=5, max_length=500)
    payment_method: str = Field(min_length=3, max_length=60)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("delivery_name", "delivery_address", "payment_method")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Trường này không được để trống")
        return value

    @field_validator("delivery_phone")
    @classmethod
    def clean_phone(cls, value: str) -> str:
        value = re.sub(r"\s+", "", value)
        if not re.fullmatch(r"0[0-9]{8,10}", value):
            raise ValueError("Số điện thoại phải gồm 9-11 chữ số và bắt đầu bằng 0")
        return value


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_id: int | None
    listing: ListingBrief
    buyer: UserBrief
    seller: UserBrief
    amount: int
    delivery_name: str | None
    delivery_phone: str | None
    delivery_address: str | None
    payment_method: str | None
    note: str | None
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
