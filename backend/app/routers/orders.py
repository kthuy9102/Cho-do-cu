from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, make_page, paginate
from app.database import get_db
from app.models import Order, User
from app.schemas.common import Page, error_responses
from app.schemas.order import OrderCreate, OrderRead
from app.security.dependencies import get_current_user
from app.services.orders import _ORDER_OPTIONS, create_listing_order, get_order, transition_order

router = APIRouter(tags=["Orders"])


@router.get("/orders", response_model=Page[OrderRead], summary="Đơn mua và đơn bán của tôi",
            responses=error_responses(401, 422))
def my_orders(
    page: PageParams = Depends(),
    side: str = Query("all", pattern="^(all|buying|selling)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Order).where(
        or_(Order.buyer_id == user.id, Order.seller_id == user.id)
    )
    if side == "buying":
        stmt = stmt.where(Order.buyer_id == user.id)
    elif side == "selling":
        stmt = stmt.where(Order.seller_id == user.id)
    items, total = paginate(db, stmt.order_by(Order.created_at.desc(), Order.id.desc()), page, options=_ORDER_OPTIONS)
    return make_page(items, total, page)


@router.get("/orders/{order_id}", response_model=OrderRead, summary="Chi tiết đơn hàng",
            responses=error_responses(401, 404))
def order_detail(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_order(db, order_id, user)


@router.post("/orders/{order_id}/confirm", response_model=OrderRead, summary="Người bán xác nhận đơn mua",
             responses=error_responses(401, 403, 404, 409))
def confirm_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return transition_order(db, order_id, "confirm", user)


@router.post("/orders/{order_id}/ship", response_model=OrderRead, summary="Người bán xác nhận đã giao hàng",
             responses=error_responses(401, 403, 404, 409))
def ship_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return transition_order(db, order_id, "ship", user)


@router.post("/orders/{order_id}/complete", response_model=OrderRead, summary="Người mua xác nhận nhận hàng",
             responses=error_responses(401, 403, 404, 409))
def complete_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return transition_order(db, order_id, "complete", user)


@router.post("/orders/{order_id}/cancel", response_model=OrderRead, summary="Hủy đơn trước khi giao",
             responses=error_responses(401, 403, 404, 409))
def cancel_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return transition_order(db, order_id, "cancel", user)



@router.post("/listings/{listing_id}/orders", response_model=OrderRead, status_code=201,
             summary="Người mua đặt hàng trực tiếp",
             responses=error_responses(401, 403, 404, 409, 422))
def place_order(listing_id: int, payload: OrderCreate, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    return create_listing_order(db, listing_id, user, payload)
