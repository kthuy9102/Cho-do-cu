from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models import ReportReason, ReportStatus
from app.schemas.listing import ListingBrief
from app.schemas.user import UserBrief


class ReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_code: ReportReason
    detail: str | None = Field(default=None, max_length=1000)


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing: ListingBrief
    reporter: UserBrief
    reason_code: ReportReason
    detail: str | None
    status: ReportStatus
    resolution_note: str | None
    created_at: datetime
    resolved_at: datetime | None


class ReportAction(str, Enum):
    dismiss = "dismiss"            # báo cáo không đúng -> bỏ qua
    hide_listing = "hide_listing"  # đúng -> ẩn tin


class ReportResolve(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: ReportAction
    note: str | None = Field(default=None, max_length=500)
