import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, TooManyRequestsError, UnprocessableError
from app.core.pagination import PageParams, make_page, paginate
from app.core.utils import escape_like
from app.database import get_db
from app.models import Category, ItemCondition, Listing, ListingImage, ListingStatus, User
from app.schemas.common import Page, error_responses
from app.schemas.listing import (
    ListingCreate,
    ListingDetail,
    ListingImageRead,
    ListingSort,
    ListingSummary,
    ListingUpdate,
)
from app.security.dependencies import get_current_user, get_current_user_optional
from app.services import listings as listing_service
from app.services.listings import EDITABLE_STATUSES, LISTING_LOAD_OPTIONS
from app.services.uploads import delete_file, save_image

router = APIRouter(prefix="/listings", tags=["Listings"])
logger = logging.getLogger("app.listings")

# Thêm Listing.id để thứ tự ổn định -> phân trang không bị lặp/sót bản ghi khi nhiều tin cùng giá/thời điểm
_ORDER = {
    ListingSort.newest: (Listing.created_at.desc(), Listing.id.desc()),
    ListingSort.price_asc: (Listing.price.asc(), Listing.id.desc()),
    ListingSort.price_desc: (Listing.price.desc(), Listing.id.desc()),
}


def _get_own_editable_listing(db: Session, listing_id: int, user: User) -> Listing:
    listing = listing_service.get_viewable_listing_or_404(db, listing_id, user)
    if listing.seller_id != user.id:
        raise ForbiddenError("Chỉ người đăng mới được thay đổi tin này", code="not_owner")
    if listing.status not in EDITABLE_STATUSES:
        raise ConflictError("Tin đã bán hoặc đã bị ẩn nên không thể chỉnh sửa", code="listing_not_editable")
    return listing


@router.get(
    "",
    response_model=Page[ListingSummary],
    summary="Tìm kiếm, lọc, sắp xếp, phân trang tin đang bán (công khai)",
    responses=error_responses(422),
)
def search_listings(
    page: PageParams = Depends(),
    q: str | None = Query(None, max_length=100, description="Từ khóa trong tiêu đề hoặc mô tả"),
    category_id: int | None = Query(None, gt=0),
    min_price: int | None = Query(None, ge=0),
    max_price: int | None = Query(None, ge=0),
    condition: ItemCondition | None = None,
    sort: ListingSort = ListingSort.newest,
    db: Session = Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise UnprocessableError("min_price không được lớn hơn max_price", code="invalid_price_range")

    conditions = [Listing.status == ListingStatus.approved]  # khách chỉ thấy tin đã duyệt và chưa bán
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        conditions.append(
            or_(Listing.title.ilike(pattern, escape="\\"), Listing.description.ilike(pattern, escape="\\"))
        )
    if category_id is not None:
        conditions.append(Listing.category_id == category_id)
    if min_price is not None:
        conditions.append(Listing.price >= min_price)
    if max_price is not None:
        conditions.append(Listing.price <= max_price)
    if condition is not None:
        conditions.append(Listing.condition == condition)

    stmt = select(Listing).where(*conditions).order_by(*_ORDER[sort])
    items, total = paginate(db, stmt, page, options=LISTING_LOAD_OPTIONS)
    return make_page(items, total, page)


# LƯU Ý THỨ TỰ: "/mine" phải khai báo trước "/{listing_id}"
@router.get(
    "/mine",
    response_model=Page[ListingSummary],
    summary="Tin do tôi đăng (mọi trạng thái)",
    responses=error_responses(401, 403, 422),
)
def my_listings(
    page: PageParams = Depends(),
    status_filter: ListingStatus | None = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Listing).where(Listing.seller_id == user.id)
    if status_filter is not None:
        stmt = stmt.where(Listing.status == status_filter)
    items, total = paginate(db, stmt.order_by(Listing.created_at.desc(), Listing.id.desc()), page, options=LISTING_LOAD_OPTIONS)
    return make_page(items, total, page)


@router.post(
    "",
    response_model=ListingDetail,
    status_code=201,
    summary="Đăng tin (trạng thái ban đầu: chờ duyệt)",
    responses=error_responses(401, 403, 422, 429),
)
def create_listing(payload: ListingCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = get_settings()
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    posted_today = db.scalar(
        select(func.count(Listing.id)).where(Listing.seller_id == user.id, Listing.created_at >= since)
    ) or 0
    if posted_today >= settings.max_listings_per_day:
        raise TooManyRequestsError(
            f"Mỗi tài khoản chỉ được đăng tối đa {settings.max_listings_per_day} tin trong 24 giờ",
            code="daily_listing_limit",
        )
    if db.get(Category, payload.category_id) is None:
        raise UnprocessableError("Danh mục không tồn tại", code="invalid_category")

    listing = Listing(seller_id=user.id, status=ListingStatus.pending, **payload.model_dump())
    db.add(listing)
    db.commit()
    logger.info("listing_created", extra={"listing_id": listing.id, "seller_id": user.id})
    return listing_service.get_listing_detail(db, listing.id)


@router.get(
    "/{listing_id}",
    response_model=ListingDetail,
    summary="Chi tiết tin đăng",
    responses=error_responses(401, 403, 404),
)
def get_listing(
    listing_id: int, user: User | None = Depends(get_current_user_optional), db: Session = Depends(get_db)
):
    return listing_service.get_viewable_listing_or_404(db, listing_id, user)


@router.patch(
    "/{listing_id}",
    response_model=ListingDetail,
    summary="Sửa tin (chỉ người đăng); sửa xong tin quay về trạng thái chờ duyệt",
    responses=error_responses(401, 403, 404, 409, 422),
)
def update_listing(
    listing_id: int, payload: ListingUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    listing = _get_own_editable_listing(db, listing_id, user)
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data and db.get(Category, data["category_id"]) is None:
        raise UnprocessableError("Danh mục không tồn tại", code="invalid_category")
    for field, value in data.items():
        setattr(listing, field, value)
    listing_service.reset_moderation(listing)
    db.commit()
    logger.info("listing_updated", extra={"listing_id": listing.id, "seller_id": user.id, "fields": sorted(data)})
    return listing_service.get_listing_detail(db, listing_id)


@router.delete(
    "/{listing_id}",
    status_code=204,
    response_class=Response,
    summary="Xóa tin (người đăng hoặc kiểm duyệt viên); không xóa được tin đã bán",
    responses=error_responses(401, 403, 404, 409),
)
def delete_listing(listing_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listing = listing_service.get_viewable_listing_or_404(db, listing_id, user)
    if listing.seller_id != user.id and not listing_service.is_staff(user):
        raise ForbiddenError("Bạn không có quyền xóa tin này", code="not_owner")
    if listing.status == ListingStatus.sold:
        raise ConflictError("Tin đã bán, không thể xóa vì còn lịch sử giao dịch", code="listing_sold")
    file_paths = [img.file_path for img in listing.images]
    db.delete(listing)
    db.commit()
    for path in file_paths:
        delete_file(path)
    logger.info("listing_deleted", extra={"listing_id": listing_id, "actor_id": user.id})
    return Response(status_code=204)


@router.post(
    "/{listing_id}/images",
    response_model=list[ListingImageRead],
    status_code=201,
    summary="Upload ảnh cho tin (JPEG/PNG/WebP, tối đa 5 MB/ảnh, tối đa 5 ảnh/tin)",
    responses=error_responses(401, 403, 404, 409, 413, 415, 422),
)
def upload_images(
    listing_id: int,
    files: list[UploadFile] = File(..., description="Một hoặc nhiều ảnh"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    listing = _get_own_editable_listing(db, listing_id, user)
    if len(listing.images) + len(files) > settings.max_images_per_listing:
        raise ConflictError(
            f"Mỗi tin chỉ có tối đa {settings.max_images_per_listing} ảnh", code="image_limit_reached"
        )

    saved: list[str] = []
    try:
        for file in files:
            saved.append(save_image(file, f"listings/{listing.id}"))
        new_images = [ListingImage(listing_id=listing.id, file_path=path) for path in saved]
        db.add_all(new_images)
        listing_service.reset_moderation(listing)
        db.commit()
    except Exception:
        db.rollback()
        for path in saved:  # không để lại file mồ côi nếu một ảnh lỗi hoặc ghi CSDL thất bại
            delete_file(path)
        raise
    logger.info("images_uploaded", extra={"listing_id": listing.id, "count": len(saved)})
    return new_images


@router.delete(
    "/{listing_id}/images/{image_id}",
    status_code=204,
    response_class=Response,
    summary="Xóa một ảnh của tin",
    responses=error_responses(401, 403, 404, 409),
)
def delete_image(listing_id: int, image_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listing = _get_own_editable_listing(db, listing_id, user)
    image = next((img for img in listing.images if img.id == image_id), None)
    if image is None:
        raise NotFoundError("Không tìm thấy ảnh", code="image_not_found")
    path = image.file_path
    listing.images.remove(image)  # delete-orphan sẽ xóa bản ghi
    listing_service.reset_moderation(listing)
    db.commit()
    delete_file(path)
    return Response(status_code=204)
