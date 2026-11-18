import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Listing, ListingStatus, Offer, OfferStatus, Order, OrderStatus, User
from app.services.notifications import notify

logger = logging.getLogger("app.orders")

_ORDER_OPTIONS = (
    joinedload(Order.listing),
    joinedload(Order.buyer),
    joinedload(Order.seller),
)


def get_order(db: Session, order_id: int, user: User) -> Order:
    order = db.scalar(select(Order).options(*_ORDER_OPTIONS).where(Order.id == order_id))
    if order is None or user.id not in (order.buyer_id, order.seller_id):
        raise NotFoundError("Không tìm thấy đơn hàng", code="order_not_found")
    return order


def transition_order(db: Session, order_id: int, action: str, user: User) -> Order:
    # Lock the order row so concurrent state transitions cannot both succeed.
    order = db.scalar(select(Order).where(Order.id == order_id).with_for_update())
    if order is None or user.id not in (order.buyer_id, order.seller_id):
        raise NotFoundError("Không tìm thấy đơn hàng", code="order_not_found")

    now = datetime.now(timezone.utc)
    if action == "ship":
        if user.id != order.seller_id:
            raise NotFoundError("Không tìm thấy đơn hàng", code="order_not_found")
        if order.status != OrderStatus.confirmed:
            raise ConflictError("Chỉ có thể giao đơn đã xác nhận", code="order_invalid_state")
        order.status = OrderStatus.shipped
        notify(db, order.buyer_id, "order_shipped", "Đơn hàng đã được giao",
               f"Người bán đã cập nhật giao đơn #{order.id}.", actor_id=user.id,
               resource_type="order", resource_id=order.id)
    elif action == "complete":
        if user.id != order.buyer_id:
            raise NotFoundError("Không tìm thấy đơn hàng", code="order_not_found")
        if order.status != OrderStatus.shipped:
            raise ConflictError("Chỉ xác nhận hoàn tất sau khi người bán giao hàng", code="order_invalid_state")
        order.status = OrderStatus.completed
        notify(db, order.seller_id, "order_completed", "Giao dịch hoàn tất",
               f"Người mua đã xác nhận hoàn tất đơn #{order.id}.", actor_id=user.id,
               resource_type="order", resource_id=order.id)
    elif action == "cancel":
        if order.status != OrderStatus.confirmed:
            raise ConflictError("Chỉ có thể hủy đơn trước khi người bán giao hàng", code="order_invalid_state")
        order.status = OrderStatus.cancelled
        listing = db.scalar(select(Listing).where(Listing.id == order.listing_id).with_for_update())
        offer = db.get(Offer, order.offer_id)
        if listing is not None and listing.status == ListingStatus.sold:
            listing.status = ListingStatus.approved
        if offer is not None and offer.status == OfferStatus.accepted:
            offer.status = OfferStatus.cancelled
        other_party = order.seller_id if user.id == order.buyer_id else order.buyer_id
        notify(db, other_party, "order_cancelled", "Đơn hàng đã bị hủy",
               f"Đơn hàng #{order.id} đã bị hủy trước khi giao.", actor_id=user.id,
               resource_type="order", resource_id=order.id)
    else:
        raise ValueError("Unsupported order action")

    order.updated_at = now
    db.commit()
    logger.info("order_transition", extra={"order_id": order.id, "action": action, "actor_id": user.id})
    return get_order(db, order.id, user)
