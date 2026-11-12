import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination import PageParams, make_page, paginate
from app.core.utils import escape_like
from app.database import get_db
from app.models import Listing, ListingStatus, Review, Role, User
from app.schemas.common import Page, error_responses
from app.schemas.user import UserActiveUpdate, UserPublic, UserRead, UserRoleUpdate, UserUpdate
from app.security.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["Users"])
logger = logging.getLogger("app.security")


# LƯU Ý THỨ TỰ: "/me" phải khai báo trước "/{user_id}"


@router.get("/me", response_model=UserRead, summary="Thông tin tài khoản đang đăng nhập", responses=error_responses(401, 403))
def read_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserRead, summary="Cập nhật hồ sơ cá nhân", responses=error_responses(401, 403, 422))
def update_me(payload: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    return user


@router.get(
    "",
    response_model=Page[UserRead],
    summary="[Admin] Danh sách người dùng",
    responses=error_responses(401, 403),
)
def list_users(
    page: PageParams = Depends(),
    q: str | None = Query(None, max_length=100, description="Tìm theo email hoặc họ tên"),
    role: Role | None = None,
    is_active: bool | None = None,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(User)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(or_(User.email.ilike(pattern, escape="\\"), User.full_name.ilike(pattern, escape="\\")))
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    items, total = paginate(db, stmt.order_by(User.id), page)
    return make_page(items, total, page)


@router.get(
    "/{user_id}",
    response_model=UserPublic,
    summary="Hồ sơ công khai và điểm uy tín của người bán",
    responses=error_responses(404),
)
def public_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise NotFoundError("Không tìm thấy người dùng", code="user_not_found")
    avg, count = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.seller_id == user_id)
    ).one()
    active = db.scalar(
        select(func.count(Listing.id)).where(Listing.seller_id == user_id, Listing.status == ListingStatus.approved)
    )
    return UserPublic(
        id=user.id,
        full_name=user.full_name,
        created_at=user.created_at,
        rating_avg=round(float(avg), 2) if avg is not None else None,
        review_count=count,
        active_listing_count=active or 0,
    )


def _get_target_or_404(db: Session, user_id: int, admin: User) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise NotFoundError("Không tìm thấy người dùng", code="user_not_found")
    if target.id == admin.id:  # tránh admin tự khóa/tự hạ quyền rồi không ai quản trị được nữa
        raise ForbiddenError("Không thể tự thay đổi vai trò hoặc trạng thái của chính mình", code="cannot_modify_self")
    return target


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    summary="[Admin] Đổi vai trò người dùng",
    responses=error_responses(401, 403, 404, 422),
)
def set_role(user_id: int, payload: UserRoleUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = _get_target_or_404(db, user_id, admin)
    old_role = target.role
    target.role = payload.role
    db.commit()
    logger.warning(
        "role_changed",
        extra={"actor_id": admin.id, "target_id": target.id, "old_role": old_role.value, "new_role": target.role.value},
    )
    return target


@router.patch(
    "/{user_id}/active",
    response_model=UserRead,
    summary="[Admin] Khóa / mở khóa tài khoản",
    responses=error_responses(401, 403, 404, 422),
)
def set_active(user_id: int, payload: UserActiveUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = _get_target_or_404(db, user_id, admin)
    target.is_active = payload.is_active
    db.commit()
    logger.warning("active_changed", extra={"actor_id": admin.id, "target_id": target.id, "is_active": target.is_active})
    return target
