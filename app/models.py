"""Model ORM. (Phân hệ của người phụ trách CSDL; để sẵn để API chạy được.
Khi nhóm có file models chính thức, giữ nguyên tên enum/cột mà routers đang dùng.)"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(str, enum.Enum):
    student = "student"      # sinh viên: vừa mua vừa bán
    moderator = "moderator"  # kiểm duyệt viên
    admin = "admin"          # quản trị


class ItemCondition(str, enum.Enum):
    new = "new"
    like_new = "like_new"
    good = "good"
    fair = "fair"
    poor = "poor"


class ListingStatus(str, enum.Enum):
    pending = "pending"    # chờ duyệt
    approved = "approved"  # đang hiển thị
    rejected = "rejected"  # bị từ chối
    sold = "sold"          # đã bán
    hidden = "hidden"      # bị ẩn do vi phạm


class OfferStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


class ReportReason(str, enum.Enum):
    spam = "spam"
    fraud = "fraud"
    prohibited_item = "prohibited_item"
    inappropriate = "inappropriate"
    other = "other"


class ReportStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"


def _enum(enum_cls: type[enum.Enum]) -> SAEnum:
    # native_enum=False: lưu VARCHAR, thêm giá trị mới không cần ALTER TYPE
    return SAEnum(enum_cls, native_enum=False, length=20)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    student_id: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[Role] = mapped_column(_enum(Role), default=Role.student)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listings: Mapped[list["Listing"]] = relationship(back_populates="seller")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_listings_price_nonneg"),
        Index("ix_listings_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int] = mapped_column(BigInteger)  # VND
    condition: Mapped[ItemCondition] = mapped_column(_enum(ItemCondition))
    status: Mapped[ListingStatus] = mapped_column(_enum(ListingStatus), default=ListingStatus.pending, index=True)
    reject_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    seller: Mapped[User] = relationship(back_populates="listings")
    category: Mapped[Category] = relationship()
    images: Mapped[list["ListingImage"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan", order_by="ListingImage.id"
    )
    offers: Mapped[list["Offer"]] = relationship(back_populates="listing", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="listing", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="listing", cascade="all, delete-orphan")

    @property
    def thumbnail_url(self) -> str | None:
        return self.images[0].url if self.images else None


class ListingImage(Base):
    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    file_path: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listing: Mapped[Listing] = relationship(back_populates="images")

    @property
    def url(self) -> str:
        return f"/media/{self.file_path}"


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_offers_amount_positive"),
        Index("ix_offers_listing_status", "listing_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    message: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[OfferStatus] = mapped_column(_enum(OfferStatus), default=OfferStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    listing: Mapped[Listing] = relationship(back_populates="offers")
    buyer: Mapped[User] = relationship()
    review: Mapped[Optional["Review"]] = relationship(back_populates="offer", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"), unique=True)  # 1 offer = 1 đánh giá
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    offer: Mapped[Offer] = relationship(back_populates="review")
    reviewer: Mapped[User] = relationship(foreign_keys=[reviewer_id])
    seller: Mapped[User] = relationship(foreign_keys=[seller_id])


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("listing_id", "reporter_id", name="uq_reports_listing_reporter"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason_code: Mapped[ReportReason] = mapped_column(_enum(ReportReason))
    detail: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReportStatus] = mapped_column(_enum(ReportStatus), default=ReportStatus.open, index=True)
    resolution_note: Mapped[str | None] = mapped_column(String(500))
    resolved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    listing: Mapped[Listing] = relationship(back_populates="reports")
    reporter: Mapped[User] = relationship(foreign_keys=[reporter_id])


class Favorite(Base):
    """Bảng trung gian N:N giữa users và listings."""

    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listing: Mapped[Listing] = relationship(back_populates="favorites")
