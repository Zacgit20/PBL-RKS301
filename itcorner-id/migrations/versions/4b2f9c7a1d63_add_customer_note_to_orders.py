"""add customer note to orders

Revision ID: 4b2f9c7a1d63
Revises: 10c7d06ecec4
Create Date: 2026-11-22
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4b2f9c7a1d63"
down_revision = "10c7d06ecec4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "orders",
        sa.Column("customer_note", sa.String(length=500), nullable=True)
    )


def downgrade():
    op.drop_column("orders", "customer_note")
