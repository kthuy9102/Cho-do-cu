from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.core.pagination import PageParams, make_page, paginate
from app.database import get_db
from app.models import Listing, Offer, OfferStatus, User
from app.schemas.common import Page, error_responses
from app.schemas.offer import OfferCreate, OfferRead
from app.security.dependencies import get_current_user
from app.services import offers as offer_service

router = APIRouter(tags=["Offers"])

_OPTIONS = (joinedload(Offer.listing), joinedload(Offer.buyer))


def _load(db: Session, offer_id: int) -> Offer:
    return db.scalar(
        select(Offer).options(*_OPTIONS).where(Offer.id == offer_id).execution_options(populate_existing=True)
    )


@router.post(
    "/listings/{listing_id}/offers",
    response_model=OfferRead,
    status_code=201,
    summary="Gửi đề nghị mua",
    responses=error_responses(401, 403, 404, 409, 422),
)
def create_offer(
    listing_id: int, payload: OfferCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    offer = offer_service.create_offer(db, listing_id, user, payload)
    return _load(db, offer.id)


# LƯU Ý THỨ TỰ: "/offers/sent", "/offers/received" trước "/offers/{offer_id}"
@router.get(
    "/offers/sent",
    response_model=Page[OfferRead],
    summary="Đề nghị tôi đã gửi (người mua)",
    responses=error_responses(401, 403, 422),
)
def sent_offers(
    page: PageParams = Depends(),
    status_filter: OfferStatus | None = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Offer).where(Offer.buyer_id == user.id)
    if status_filter is not None:
        stmt = stmt.where(Offer.status == status_filter)
    items, total = paginate(db, stmt.order_by(Offer.created_at.desc(), Offer.id.desc()), page, options=_OPTIONS)
    return make_page(items, total, page)


@router.get(
    "/offers/received",
    response_model=Page[OfferRead],
    summary="Đề nghị gửi tới tin của tôi (người bán)",
    responses=error_responses(401, 403, 422),
)
def received_offers(
    page: PageParams = Depends(),
    status_filter: OfferStatus | None = Query(None, alias="status"),
    listing_id: int | None = Query(None, gt=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Offer).join(Listing, Listing.id == Offer.listing_id).where(Listing.seller_id == user.id)
    if status_filter is not None:
        stmt = stmt.where(Offer.status == status_filter)
    if listing_id is not None:
        stmt = stmt.where(Offer.listing_id == listing_id)
    items, total = paginate(db, stmt.order_by(Offer.created_at.desc(), Offer.id.desc()), page, options=_OPTIONS)
    return make_page(items, total, page)


@router.get(
    "/offers/{offer_id}",
    response_model=OfferRead,
    summary="Chi tiết đề nghị (người mua hoặc người bán của tin)",
    responses=error_responses(401, 403, 404),
)
def get_offer(offer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    offer = _load(db, offer_id)
    if offer is None or user.id not in (offer.buyer_id, offer.listing.seller_id):
        raise NotFoundError("Không tìm thấy đề nghị mua", code="offer_not_found")
    return offer


@router.post(
    "/offers/{offer_id}/accept",
    response_model=OfferRead,
    summary="Người bán chấp nhận đề nghị: tin chuyển 'đã bán', các đề nghị chờ khác bị từ chối",
    responses=error_responses(401, 403, 404, 409),
)
def accept_offer(offer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    offer_service.accept_offer(db, offer_id, user)
    return _load(db, offer_id)


@router.post(
    "/offers/{offer_id}/reject",
    response_model=OfferRead,
    summary="Người bán từ chối đề nghị",
    responses=error_responses(401, 403, 404, 409),
)
def reject_offer(offer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    offer_service.reject_offer(db, offer_id, user)
    return _load(db, offer_id)


@router.post(
    "/offers/{offer_id}/cancel",
    response_model=OfferRead,
    summary="Người mua hủy đề nghị đang chờ",
    responses=error_responses(401, 403, 404, 409),
)
def cancel_offer(offer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    offer_service.cancel_offer(db, offer_id, user)
    return _load(db, offer_id)
