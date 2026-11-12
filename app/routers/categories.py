from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, UnprocessableError
from app.core.utils import slugify
from app.database import get_db
from app.models import Category, Listing, User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import error_responses
from app.security.dependencies import require_admin

router = APIRouter(prefix="/categories", tags=["Categories"])


def _unique_check(db: Session, name: str, slug: str, exclude_id: int | None = None) -> None:
    stmt = select(Category.id).where((Category.name == name) | (Category.slug == slug))
    if exclude_id is not None:
        stmt = stmt.where(Category.id != exclude_id)
    if db.scalar(stmt):
        raise ConflictError("Tên danh mục đã tồn tại", code="category_exists")


@router.get("", response_model=list[CategoryRead], summary="Danh sách danh mục (công khai)")
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.name)).all()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=201,
    summary="[Admin] Tạo danh mục",
    responses=error_responses(401, 403, 409, 422),
)
def create_category(payload: CategoryCreate, _admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    slug = slugify(payload.name)
    if not slug:
        raise UnprocessableError("Tên danh mục không hợp lệ", code="invalid_category_name")
    _unique_check(db, payload.name, slug)
    category = Category(name=payload.name, slug=slug)
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Tên danh mục đã tồn tại", code="category_exists")
    return category


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="[Admin] Đổi tên danh mục",
    responses=error_responses(401, 403, 404, 409, 422),
)
def update_category(
    category_id: int, payload: CategoryUpdate, _admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Không tìm thấy danh mục", code="category_not_found")
    slug = slugify(payload.name)
    if not slug:
        raise UnprocessableError("Tên danh mục không hợp lệ", code="invalid_category_name")
    _unique_check(db, payload.name, slug, exclude_id=category_id)
    category.name, category.slug = payload.name, slug
    db.commit()
    return category


@router.delete(
    "/{category_id}",
    status_code=204,
    response_class=Response,
    summary="[Admin] Xóa danh mục (chỉ khi chưa có tin nào dùng)",
    responses=error_responses(401, 403, 404, 409),
)
def delete_category(category_id: int, _admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Không tìm thấy danh mục", code="category_not_found")
    if db.scalar(select(Listing.id).where(Listing.category_id == category_id).limit(1)):
        raise ConflictError("Danh mục đang có tin đăng, không thể xóa", code="category_in_use")
    db.delete(category)
    db.commit()
    return Response(status_code=204)
