from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import OrderStatus
from app.schemas.listing import ListingBrief
from app.schemas.user import UserBrief


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_id: int
    listing: ListingBrief
    buyer: UserBrief
    seller: UserBrief
    amount: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
