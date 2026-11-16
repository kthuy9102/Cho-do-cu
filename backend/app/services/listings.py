"""Quy tắc nghiệp vụ về tin đăng dùng chung cho nhiều router."""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.exceptions import NotFoundError
from app.models import Listing, ListingStatus, Role, User

# Khách vãng lai xem được chi tiết tin đang bán hoặc đã bán
PUBLIC_STATUSES = (ListingStatus.approved, ListingStatus.sold)
# Người đăng chỉ sửa được khi tin chưa bán/chưa bị ẩn
EDITABLE_STATUSES = (ListingStatus.pending, ListingStatus.approved, ListingStatus.rejected)

# Nạp sẵn quan hệ để tránh lỗi N+1 khi trả danh sách:
# many-to-one -> joinedload (1 JOIN); one-to-many -> selectinload (1 câu SELECT ... IN thêm)
LISTING_LOAD_OPTIONS = (
    joinedload(Listing.seller),
    joinedload(Listing.category),
    selectinload(Listing.images),
)


def is_staff(user: User | None) -> bool:
    return user is not None and user.role in (Role.moderator, Role.admin)


def can_view_listing(listing: Listing, user: User | None) -> bool:
    if listing.status in PUBLIC_STATUSES:
        return True
    return user is not None and (user.id == listing.seller_id or is_staff(user))


def get_listing_detail(db: Session, listing_id: int) -> Listing | None:
    return db.scalar(
        select(Listing)
        .options(*LISTING_LOAD_OPTIONS)
        .where(Listing.id == listing_id)
        .execution_options(populate_existing=True)
    )


def get_viewable_listing_or_404(db: Session, listing_id: int, user: User | None) -> Listing:
    """Tin không tồn tại HOẶC người xem không có quyền thấy -> cùng trả 404 (không lộ sự tồn tại)."""
    listing = get_listing_detail(db, listing_id)
    if listing is None or not can_view_listing(listing, user):
        raise NotFoundError("Không tìm thấy tin đăng", code="listing_not_found")
    return listing


def reset_moderation(listing: Listing) -> None:
    """Sửa nội dung/ảnh của tin đã duyệt hoặc bị từ chối -> phải qua kiểm duyệt lại."""
    if listing.status in (ListingStatus.approved, ListingStatus.rejected):
        listing.status = ListingStatus.pending
        listing.reject_reason = None
