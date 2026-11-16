import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination import PageParams, make_page, paginate
from app.database import get_db
from app.models import Offer, OfferStatus, Review, User
from app.schemas.common import Page, error_responses
from app.schemas.review import ReviewCreate, ReviewRead
from app.security.dependencies import get_current_user

router = APIRouter(tags=["Reviews"])
logger = logging.getLogger("app.reviews")


@router.post(
    "/offers/{offer_id}/review",
    response_model=ReviewRead,
    status_code=201,
    summary="Người mua đánh giá người bán sau giao dịch (mỗi đề nghị một lần)",
    responses=error_responses(401, 403, 404, 409, 422),
)
def create_review(
    offer_id: int, payload: ReviewCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    offer = db.scalar(select(Offer).options(joinedload(Offer.listing)).where(Offer.id == offer_id))
    if offer is None or offer.buyer_id != user.id:
        raise NotFoundError("Không tìm thấy đề nghị mua", code="offer_not_found")
    if offer.status != OfferStatus.accepted:
        raise ConflictError("Chỉ được đánh giá sau khi đề nghị đã được chấp nhận", code="offer_not_accepted")
    if db.scalar(select(Review.id).where(Review.offer_id == offer.id)):
        raise ConflictError("Bạn đã đánh giá giao dịch này rồi", code="already_reviewed")

    review = Review(
        offer_id=offer.id,
        reviewer_id=user.id,
        seller_id=offer.listing.seller_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError:  # UNIQUE(offer_id) chặn trường hợp hai request đồng thời
        db.rollback()
        raise ConflictError("Bạn đã đánh giá giao dịch này rồi", code="already_reviewed")
    logger.info("review_created", extra={"review_id": review.id, "seller_id": review.seller_id, "rating": review.rating})
    return db.scalar(
        select(Review).options(joinedload(Review.reviewer)).where(Review.id == review.id).execution_options(populate_existing=True)
    )


@router.get(
    "/users/{user_id}/reviews",
    response_model=Page[ReviewRead],
    summary="Các đánh giá về một người bán (công khai)",
    responses=error_responses(404, 422),
)
def seller_reviews(user_id: int, page: PageParams = Depends(), db: Session = Depends(get_db)):
    seller = db.get(User, user_id)
    if seller is None or not seller.is_active:
        raise NotFoundError("Không tìm thấy người dùng", code="user_not_found")
    stmt = select(Review).where(Review.seller_id == user_id).order_by(Review.created_at.desc(), Review.id.desc())
    items, total = paginate(db, stmt, page, options=(joinedload(Review.reviewer),))
    return make_page(items, total, page)
