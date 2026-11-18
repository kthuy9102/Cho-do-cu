from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.core.pagination import PageParams, make_page, paginate
from app.database import get_db
from app.models import Notification, User
from app.schemas.common import Page, error_responses
from app.schemas.notification import NotificationRead, UnreadCount
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=Page[NotificationRead], summary="Thông báo của tôi",
            responses=error_responses(401, 422))
def my_notifications(page: PageParams = Depends(), user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    stmt = select(Notification).where(Notification.recipient_id == user.id).order_by(
        Notification.created_at.desc(), Notification.id.desc()
    )
    items, total = paginate(db, stmt, page, options=(joinedload(Notification.actor),))
    return make_page(items, total, page)


@router.get("/unread-count", response_model=UnreadCount, summary="Số thông báo chưa đọc",
            responses=error_responses(401))
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.scalar(select(func.count(Notification.id)).where(
        Notification.recipient_id == user.id, Notification.read_at.is_(None)
    )) or 0
    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=NotificationRead, summary="Đánh dấu đã đọc",
              responses=error_responses(401, 404))
def mark_read(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Notification).options(joinedload(Notification.actor)).where(
        Notification.id == notification_id, Notification.recipient_id == user.id
    ))
    if item is None:
        raise NotFoundError("Không tìm thấy thông báo", code="notification_not_found")
    if item.read_at is None:
        item.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
    return item


@router.post("/read-all", status_code=204, response_class=Response, summary="Đánh dấu tất cả đã đọc",
             responses=error_responses(401))
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(update(Notification).where(
        Notification.recipient_id == user.id, Notification.read_at.is_(None)
    ).values(read_at=datetime.now(timezone.utc)))
    db.commit()
    return Response(status_code=204)
