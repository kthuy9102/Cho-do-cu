"""Nghiệp vụ đề nghị mua. Chấp nhận đề nghị là thao tác nhiều bước nên gói trong MỘT transaction."""
import logging

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import Listing, ListingStatus, Offer, OfferStatus, User
from app.schemas.offer import OfferCreate
from app.services.listings import PUBLIC_STATUSES

logger = logging.getLogger("app.offers")


def create_offer(db: Session, listing_id: int, buyer: User, payload: OfferCreate) -> Offer:
    listing = db.get(Listing, listing_id)
    if listing is None or listing.status not in PUBLIC_STATUSES:
        raise NotFoundError("Không tìm thấy tin đăng", code="listing_not_found")
    if listing.seller_id == buyer.id:
        raise ForbiddenError("Không thể đặt mua tin do chính mình đăng", code="own_listing")
    if listing.status != ListingStatus.approved:
        raise ConflictError("Tin này đã bán", code="listing_not_available")

    duplicate = db.scalar(
        select(Offer.id).where(
            Offer.listing_id == listing_id, Offer.buyer_id == buyer.id, Offer.status == OfferStatus.pending
        )
    )
    if duplicate:
        raise ConflictError(
            "Bạn đã có đề nghị đang chờ cho tin này, hãy hủy đề nghị cũ trước", code="duplicate_offer"
        )

    offer = Offer(listing_id=listing_id, buyer_id=buyer.id, amount=payload.amount, message=payload.message)
    db.add(offer)
    db.commit()
    logger.info("offer_created", extra={"offer_id": offer.id, "listing_id": listing_id, "buyer_id": buyer.id})
    return offer


def _offer_or_404(db: Session, offer_id: int) -> Offer:
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise NotFoundError("Không tìm thấy đề nghị mua", code="offer_not_found")
    return offer


def accept_offer(db: Session, offer_id: int, seller: User) -> Offer:
    offer = _offer_or_404(db, offer_id)

    # Khóa dòng tin (SELECT ... FOR UPDATE): hai lần "chấp nhận" đồng thời sẽ xếp hàng,
    # lần sau thấy tin đã bán và nhận 409 thay vì bán một món cho hai người.
    listing = db.scalar(select(Listing).where(Listing.id == offer.listing_id).with_for_update())
    if listing is None or listing.seller_id != seller.id:
        db.rollback()
        raise NotFoundError("Không tìm thấy đề nghị mua", code="offer_not_found")  # không lộ cho người ngoài cuộc

    db.refresh(offer)  # đọc lại trạng thái mới nhất sau khi giữ khóa
    if offer.status != OfferStatus.pending:
        db.rollback()
        raise ConflictError("Đề nghị này không còn ở trạng thái chờ", code="offer_not_pending")
    if listing.status != ListingStatus.approved:
        db.rollback()
        raise ConflictError("Tin đăng không còn ở trạng thái đang bán", code="listing_not_available")

    offer.status = OfferStatus.accepted
    listing.status = ListingStatus.sold
    db.execute(  # các đề nghị chờ khác của cùng tin tự động bị từ chối
        update(Offer)
        .where(Offer.listing_id == listing.id, Offer.id != offer.id, Offer.status == OfferStatus.pending)
        .values(status=OfferStatus.rejected)
    )
    db.commit()
    logger.info("offer_accepted", extra={"offer_id": offer.id, "listing_id": listing.id, "seller_id": seller.id})
    return offer


def reject_offer(db: Session, offer_id: int, seller: User) -> Offer:
    offer = _offer_or_404(db, offer_id)
    if offer.listing.seller_id != seller.id:
        raise NotFoundError("Không tìm thấy đề nghị mua", code="offer_not_found")
    if offer.status != OfferStatus.pending:
        raise ConflictError("Đề nghị này không còn ở trạng thái chờ", code="offer_not_pending")
    offer.status = OfferStatus.rejected
    db.commit()
    logger.info("offer_rejected", extra={"offer_id": offer.id, "seller_id": seller.id})
    return offer


def cancel_offer(db: Session, offer_id: int, buyer: User) -> Offer:
    offer = _offer_or_404(db, offer_id)
    if offer.buyer_id != buyer.id:
        raise NotFoundError("Không tìm thấy đề nghị mua", code="offer_not_found")
    if offer.status != OfferStatus.pending:
        raise ConflictError("Chỉ hủy được đề nghị đang chờ", code="offer_not_pending")
    offer.status = OfferStatus.cancelled
    db.commit()
    logger.info("offer_cancelled", extra={"offer_id": offer.id, "buyer_id": buyer.id})
    return offer
