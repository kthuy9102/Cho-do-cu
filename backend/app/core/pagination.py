from math import ceil
from typing import Any, Sequence

from fastapi import Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


class PageParams:
    """Query param chung: ?page=1&page_size=20 (tối đa 100)."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Số trang, bắt đầu từ 1"),
        page_size: int = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang (tối đa 100)"),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def paginate(db: Session, stmt: Select, params: PageParams, options: Sequence[Any] = ()) -> tuple[list, int]:
    """Đếm tổng rồi lấy đúng một trang. `options` (joinedload/selectinload) chỉ áp cho câu lấy dữ liệu."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.options(*options).limit(params.page_size).offset(params.offset)).all()
    return list(items), total


def make_page(items: list, total: int, params: PageParams) -> dict:
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "pages": ceil(total / params.page_size) if total else 0,
    }
