from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import OfferStatus
from app.schemas.listing import ListingBrief
from app.schemas.user import UserBrief


class OfferCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int = Field(gt=0, le=1_000_000_000, description="Giá đề nghị, VND")
    message: str | None = Field(default=None, max_length=500)


class OfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing: ListingBrief
    buyer: UserBrief
    amount: int
    message: str | None
    status: OfferStatus
    created_at: datetime
    updated_at: datetime
