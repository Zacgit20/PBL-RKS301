"""add product updated timestamp

Revision ID: fee9172dad19
Revises: 740501a2349e
Create Date: 2026-11-13 10:54:08.355457
"""
from alembic import op
import sqlalchemy as sa

revision = 'fee9172dad19'
down_revision = '740501a2349e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'products',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )

    op.execute(
        "UPDATE products SET updated_at = CURRENT_TIMESTAMP "
        "WHERE updated_at IS NULL"
    )

    op.alter_column(
        'products',
        'updated_at',
        existing_type=sa.DateTime(timezone=True),
        nullable=False
    )


def downgrade():
    op.drop_column('products', 'updated_at')
