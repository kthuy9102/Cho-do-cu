import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import PageParams, make_page, paginate
from app.database import get_db
from app.models import Listing, ListingStatus, Offer, OfferStatus, Report, ReportStatus, User
from app.schemas.common import Page, error_responses
from app.schemas.listing import ListingDetail, RejectRequest
from app.schemas.report import ReportAction, ReportRead, ReportResolve
from app.security.dependencies import require_moderator
from app.services import listings as listing_service
from app.services.listings import LISTING_LOAD_OPTIONS

# Cả router chỉ cho moderator và admin: khai báo ở mức router để không endpoint nào bị sót
router = APIRouter(prefix="/moderation", tags=["Moderation"], dependencies=[Depends(require_moderator)])
logger = logging.getLogger("app.moderation")


def _get_listing_for_review(db: Session, listing_id: int, moderator: User) -> Listing:
    listing = listing_service.get_listing_detail(db, listing_id)
    if listing is None:
        raise NotFoundError("Không tìm thấy tin đăng", code="listing_not_found")
    if listing.seller_id == moderator.id:
        raise ForbiddenError("Không được tự duyệt tin của chính mình", code="self_moderation")
    return listing


@router.get(
    "/listings",
    response_model=Page[ListingDetail],
    summary="Hàng đợi kiểm duyệt (mặc định: tin chờ duyệt)",
    responses=error_responses(401, 403, 422),
)
def moderation_queue(
    page: PageParams = Depends(),
    status_filter: ListingStatus = Query(ListingStatus.pending, alias="status"),
    db: Session = Depends(get_db),
):
    stmt = select(Listing).where(Listing.status == status_filter).order_by(Listing.created_at.asc(), Listing.id.asc())
    items, total = paginate(db, stmt, page, options=LISTING_LOAD_OPTIONS)
    return make_page(items, total, page)


@router.post(
    "/listings/{listing_id}/approve",
    response_model=ListingDetail,
    summary="Duyệt tin",
    responses=error_responses(401, 403, 404, 409),
)
def approve_listing(listing_id: int, moderator: User = Depends(require_moderator), db: Session = Depends(get_db)):
    listing = _get_listing_for_review(db, listing_id, moderator)
    if listing.status != ListingStatus.pending:
        raise ConflictError("Chỉ duyệt được tin đang chờ duyệt", code="listing_not_pending")
    listing.status = ListingStatus.approved
    listing.reject_reason = None
    db.commit()
    logger.info("listing_approved", extra={"listing_id": listing_id, "moderator_id": moderator.id})
    return listing_service.get_listing_detail(db, listing_id)


@router.post(
    "/listings/{listing_id}/reject",
    response_model=ListingDetail,
    summary="Từ chối tin (bắt buộc nêu lý do)",
    responses=error_responses(401, 403, 404, 409, 422),
)
def reject_listing(
    listing_id: int, payload: RejectRequest, moderator: User = Depends(require_moderator), db: Session = Depends(get_db)
):
    listing = _get_listing_for_review(db, listing_id, moderator)
    if listing.status != ListingStatus.pending:
        raise ConflictError("Chỉ từ chối được tin đang chờ duyệt", code="listing_not_pending")
    listing.status = ListingStatus.rejected
    listing.reject_reason = payload.reason.strip()
    db.commit()
    logger.info("listing_rejected", extra={"listing_id": listing_id, "moderator_id": moderator.id})
    return listing_service.get_listing_detail(db, listing_id)


@router.get(
    "/reports",
    response_model=Page[ReportRead],
    summary="Danh sách báo cáo vi phạm (mặc định: chưa xử lý)",
    responses=error_responses(401, 403, 422),
)
def list_reports(
    page: PageParams = Depends(),
    status_filter: ReportStatus = Query(ReportStatus.open, alias="status"),
    db: Session = Depends(get_db),
):
    stmt = select(Report).where(Report.status == status_filter).order_by(Report.created_at.asc(), Report.id.asc())
    items, total = paginate(db, stmt, page, options=(joinedload(Report.listing), joinedload(Report.reporter)))
    return make_page(items, total, page)


@router.patch(
    "/reports/{report_id}",
    response_model=ReportRead,
    summary="Xử lý báo cáo: bỏ qua hoặc ẩn tin vi phạm",
    responses=error_responses(401, 403, 404, 409, 422),
)
def resolve_report(
    report_id: int, payload: ReportResolve, moderator: User = Depends(require_moderator), db: Session = Depends(get_db)
):
    report = db.scalar(
        select(Report).options(joinedload(Report.listing), joinedload(Report.reporter)).where(Report.id == report_id)
    )
    if report is None:
        raise NotFoundError("Không tìm thấy báo cáo", code="report_not_found")
    if report.status != ReportStatus.open:
        raise ConflictError("Báo cáo này đã được xử lý", code="report_already_resolved")

    if payload.action == ReportAction.hide_listing:
        listing = report.listing
        if listing.seller_id == moderator.id:
            raise ForbiddenError("Không được tự xử lý tin của chính mình", code="self_moderation")
        if listing.status == ListingStatus.sold:
            raise ConflictError("Tin đã bán, không thể ẩn", code="listing_sold")
        listing.status = ListingStatus.hidden
        db.execute(  # tin bị ẩn thì các đề nghị đang chờ không còn ý nghĩa
            update(Offer)
            .where(Offer.listing_id == listing.id, Offer.status == OfferStatus.pending)
            .values(status=OfferStatus.rejected)
        )
        report.status = ReportStatus.resolved
    else:
        report.status = ReportStatus.dismissed

    report.resolution_note = payload.note
    report.resolved_by_id = moderator.id
    report.resolved_at = datetime.now(timezone.utc)
    db.commit()
    logger.warning(
        "report_resolved",
        extra={"report_id": report.id, "listing_id": report.listing_id, "moderator_id": moderator.id, "action": payload.action.value},
    )
    return report
