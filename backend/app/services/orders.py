import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Listing, ListingStatus, Offer, OfferStatus, Order, OrderStatus, User
from app.schemas.order import OrderCreate
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


def create_listing_order(db: Session, listing_id: int, buyer: User, payload: OrderCreate) -> Order:
    listing = db.scalar(select(Listing).where(Listing.id == listing_id).with_for_update())
    if listing is None or listing.status != ListingStatus.approved:
        raise NotFoundError("Không tìm thấy tin đăng đang bán", code="listing_not_found")
    if listing.seller_id == buyer.id:
        raise ConflictError("Không thể tự đặt mua tin của chính mình", code="own_listing")
    active = db.scalar(select(Order.id).where(
        Order.listing_id == listing_id,
        Order.status.in_([OrderStatus.pending, OrderStatus.confirmed, OrderStatus.shipped]),
    ).limit(1))
    if active:
        raise ConflictError("Tin này đã có đơn hàng đang xử lý", code="listing_has_active_order")
    offer = db.scalar(select(Offer).where(
        Offer.listing_id == listing.id, Offer.buyer_id == buyer.id, Offer.status == OfferStatus.pending
    ).with_for_update())
    if offer is None:
        offer = Offer(
            listing_id=listing.id, buyer_id=buyer.id, amount=listing.price,
            message=payload.note, status=OfferStatus.pending,
        )
        db.add(offer)
        db.flush()
    else:
        offer.amount = listing.price
        offer.message = payload.note
    order = Order(
        offer_id=offer.id,
        listing_id=listing.id,
        buyer_id=buyer.id,
        seller_id=listing.seller_id,
        amount=listing.price,
        delivery_name=payload.delivery_name,
        delivery_phone=payload.delivery_phone,
        delivery_address=payload.delivery_address,
        payment_method=payload.payment_method,
        note=payload.note,
        status=OrderStatus.pending,
    )
    db.add(order)
    notify(db, listing.seller_id, "order_placed", "Có đơn mua mới",
           f"{payload.delivery_name} đã đặt mua '{listing.title}' với giá {listing.price:,} VND.",
           actor_id=buyer.id, resource_type="listing", resource_id=listing.id)
    db.commit()
    logger.info("order_created", extra={"order_id": order.id, "listing_id": listing.id, "buyer_id": buyer.id})
    return get_order(db, order.id, buyer)


def transition_order(db: Session, order_id: int, action: str, user: User) -> Order:
    # Lock the order row so concurrent state transitions cannot both succeed.
    order = db.scalar(select(Order).where(Order.id == order_id).with_for_update())
    if order is None or user.id not in (order.buyer_id, order.seller_id):
        raise NotFoundError("Không tìm thấy đơn hàng", code="order_not_found")

    now = datetime.now(timezone.utc)
    if action == "confirm":
        if user.id != order.seller_id:
            raise NotFoundError("Không tìm thấy đơn hàng", code="order_not_found")
        if order.status != OrderStatus.pending:
            raise ConflictError("Chỉ xác nhận đơn đang chờ", code="order_invalid_state")
        listing = db.scalar(select(Listing).where(Listing.id == order.listing_id).with_for_update())
        if listing is None or listing.status != ListingStatus.approved:
            raise ConflictError("Tin đăng không còn khả dụng", code="listing_not_available")
        listing.status = ListingStatus.sold
        order.status = OrderStatus.confirmed
        offer = db.get(Offer, order.offer_id) if order.offer_id else None
        if offer is not None:
            offer.status = OfferStatus.accepted
        db.query(Offer).filter(
            Offer.listing_id == listing.id, Offer.id != (order.offer_id or 0),
            Offer.status == OfferStatus.pending,
        ).update({Offer.status: OfferStatus.rejected}, synchronize_session=False)
        notify(db, order.buyer_id, "order_confirmed", "Đơn hàng đã được xác nhận",
               f"Người bán đã xác nhận đơn #{order.id}.", actor_id=user.id,
               resource_type="order", resource_id=order.id)
    elif action == "ship":
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
        if order.status not in (OrderStatus.pending, OrderStatus.confirmed):
            raise ConflictError("Chỉ có thể hủy đơn trước khi người bán giao hàng", code="order_invalid_state")
        was_confirmed = order.status == OrderStatus.confirmed
        order.status = OrderStatus.cancelled
        listing = db.scalar(select(Listing).where(Listing.id == order.listing_id).with_for_update())
        offer = db.get(Offer, order.offer_id)
        if was_confirmed and listing is not None and listing.status == ListingStatus.sold:
            listing.status = ListingStatus.approved
        if offer is not None and offer.status in (OfferStatus.pending, OfferStatus.accepted):
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
