"""add product specifications

Revision ID: 8f31c2a7d910
Revises: 6c6428053789
"""

from alembic import op
import sqlalchemy as sa


revision = "8f31c2a7d910"
down_revision = "6c6428053789"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_specifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False
        ),
        sa.Column("attribute_name", sa.String(80), nullable=False),
        sa.Column("attribute_value", sa.String(300), nullable=False),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0"
        ),
        sa.CheckConstraint(
            "length(trim(attribute_name)) BETWEEN 1 AND 80",
            name="product_specifications_name_length_check"
        ),
        sa.CheckConstraint(
            "length(trim(attribute_value)) BETWEEN 1 AND 300",
            name="product_specifications_value_length_check"
        ),
        sa.CheckConstraint(
            "sort_order >= 0",
            name="product_specifications_sort_order_check"
        )
    )

    op.create_index(
        "ix_product_specifications_product_id",
        "product_specifications",
        ["product_id"]
    )


def downgrade():
    op.drop_index(
        "ix_product_specifications_product_id",
        table_name="product_specifications"
    )
    op.drop_table("product_specifications")
