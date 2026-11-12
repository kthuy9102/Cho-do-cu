import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.database import get_db
from app.models import Listing, Report, User
from app.schemas.common import error_responses
from app.schemas.report import ReportCreate, ReportRead
from app.security.dependencies import get_current_user
from app.services.listings import PUBLIC_STATUSES

router = APIRouter(tags=["Reports"])
logger = logging.getLogger("app.reports")


@router.post(
    "/listings/{listing_id}/reports",
    response_model=ReportRead,
    status_code=201,
    summary="Báo cáo tin vi phạm (mỗi người một lần cho mỗi tin)",
    responses=error_responses(401, 403, 404, 409, 422),
)
def report_listing(
    listing_id: int, payload: ReportCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    listing = db.get(Listing, listing_id)
    if listing is None or listing.status not in PUBLIC_STATUSES:
        raise NotFoundError("Không tìm thấy tin đăng", code="listing_not_found")
    if listing.seller_id == user.id:
        raise ForbiddenError("Không thể báo cáo tin của chính mình", code="own_listing")
    if db.scalar(select(Report.id).where(Report.listing_id == listing_id, Report.reporter_id == user.id)):
        raise ConflictError("Bạn đã báo cáo tin này rồi", code="already_reported")

    report = Report(listing_id=listing_id, reporter_id=user.id, reason_code=payload.reason_code, detail=payload.detail)
    db.add(report)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Bạn đã báo cáo tin này rồi", code="already_reported")
    logger.info("listing_reported", extra={"report_id": report.id, "listing_id": listing_id, "reporter_id": user.id})
    return db.scalar(
        select(Report).options(joinedload(Report.listing), joinedload(Report.reporter)).where(Report.id == report.id).execution_options(populate_existing=True)
    )
