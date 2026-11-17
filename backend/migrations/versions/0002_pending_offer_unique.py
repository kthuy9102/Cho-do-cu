"""Enforce one pending offer per buyer and listing.

Revision ID: 0002_pending_offer_unique
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_pending_offer_unique"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

INDEX_NAME = "uq_offers_one_pending_per_buyer_listing"


def upgrade() -> None:
    # The initial baseline uses Base.metadata.create_all(), which may already
    # create this model index on a fresh database. Check before creating it so
    # both fresh and previously-stamped databases can upgrade safely.
    bind = op.get_bind()
    existing = {item["name"] for item in sa.inspect(bind).get_indexes("offers")}
    if INDEX_NAME not in existing:
        op.create_index(
            INDEX_NAME,
            "offers",
            ["listing_id", "buyer_id"],
            unique=True,
            postgresql_where=sa.text("status = 'pending'"),
            sqlite_where=sa.text("status = 'pending'"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    existing = {item["name"] for item in sa.inspect(bind).get_indexes("offers")}
    if INDEX_NAME in existing:
        op.drop_index(INDEX_NAME, table_name="offers")
