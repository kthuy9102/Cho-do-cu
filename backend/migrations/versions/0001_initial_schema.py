"""Initial database schema baseline.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-18
"""
from alembic import op

from app.database import Base
from app import models  # noqa: F401 - register all ORM tables

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all application tables for a fresh database."""
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Drop application tables created by the initial schema."""
    Base.metadata.drop_all(bind=op.get_bind())
