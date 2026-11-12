from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.pagination import PageParams, make_page, paginate
from app.database import get_db
from app.models import Favorite, Listing, ListingStatus, User
from app.schemas.common import Page, error_responses
from app.schemas.listing import ListingSummary
from app.security.dependencies import get_current_user
from app.services.listings import LISTING_LOAD_OPTIONS

router = APIRouter(tags=["Favorites"])


@router.put(
    "/listings/{listing_id}/favorite",
    status_code=204,
    response_class=Response,
    summary="Thêm vào yêu thích (idempotent: gọi lại nhiều lần kết quả như nhau)",
    responses=error_responses(401, 403, 404),
)
def add_favorite(listing_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if listing is None or listing.status != ListingStatus.approved:
        raise NotFoundError("Không tìm thấy tin đăng", code="listing_not_found")
    if db.get(Favorite, (user.id, listing_id)) is None:
        db.add(Favorite(user_id=user.id, listing_id=listing_id))
        db.commit()
    return Response(status_code=204)


@router.delete(
    "/listings/{listing_id}/favorite",
    status_code=204,
    response_class=Response,
    summary="Bỏ yêu thích (idempotent)",
    responses=error_responses(401, 403),
)
def remove_favorite(listing_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    favorite = db.get(Favorite, (user.id, listing_id))
    if favorite is not None:
        db.delete(favorite)
        db.commit()
    return Response(status_code=204)


@router.get(
    "/favorites",
    response_model=Page[ListingSummary],
    summary="Danh sách tin yêu thích của tôi",
    responses=error_responses(401, 403, 422),
)
def my_favorites(page: PageParams = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = (
        select(Listing)
        .join(Favorite, Favorite.listing_id == Listing.id)
        .where(Favorite.user_id == user.id, Listing.status == ListingStatus.approved)
        .order_by(Favorite.created_at.desc(), Listing.id.desc())
    )
    items, total = paginate(db, stmt, page, options=LISTING_LOAD_OPTIONS)
    return make_page(items, total, page)
