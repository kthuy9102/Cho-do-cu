"""Add transactional orders and persistent notifications.

Revision ID: 0003_orders_notifications
Revises: 0002_pending_offer_unique
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_orders_notifications"
down_revision = "0002_pending_offer_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "orders" not in tables:
        op.create_table(
            "orders",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("offer_id", sa.Integer(), sa.ForeignKey("offers.id"), nullable=False, unique=True),
            sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id"), nullable=False),
            sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("seller_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("amount", sa.BigInteger(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="confirmed"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("amount > 0", name="ck_orders_amount_positive"),
        )
    order_indexes = {x["name"] for x in sa.inspect(bind).get_indexes("orders")}
    for name, cols in (
        ("ix_orders_offer_id", ["offer_id"]),
        ("ix_orders_listing_id", ["listing_id"]),
        ("ix_orders_buyer_id", ["buyer_id"]),
        ("ix_orders_seller_id", ["seller_id"]),
        ("ix_orders_status", ["status"]),
        ("ix_orders_buyer_created", ["buyer_id", "created_at"]),
        ("ix_orders_seller_created", ["seller_id", "created_at"]),
    ):
        if name not in order_indexes:
            op.create_index(name, "orders", cols, unique=(name == "ix_orders_offer_id"))

    if "notifications" not in tables:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("recipient_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("event_type", sa.String(length=40), nullable=False),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("body", sa.String(length=500), nullable=False),
            sa.Column("resource_type", sa.String(length=40), nullable=True),
            sa.Column("resource_id", sa.Integer(), nullable=True),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    notification_indexes = {x["name"] for x in sa.inspect(bind).get_indexes("notifications")}
    for name, cols in (
        ("ix_notifications_recipient_id", ["recipient_id"]),
        ("ix_notifications_recipient_created", ["recipient_id", "created_at"]),
    ):
        if name not in notification_indexes:
            op.create_index(name, "notifications", cols)


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("orders")
