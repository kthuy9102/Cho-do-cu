from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserBrief


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor: UserBrief | None = None
    event_type: str
    title: str
    body: str
    resource_type: str | None
    resource_id: int | None
    read_at: datetime | None
    created_at: datetime


class UnreadCount(BaseModel):
    unread_count: int
