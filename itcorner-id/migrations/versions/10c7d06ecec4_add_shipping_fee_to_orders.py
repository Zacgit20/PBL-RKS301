"""add shipping fee to orders

Revision ID: 10c7d06ecec4
Revises: 60d6b598d6cd
Create Date: 2026-11-22 02:14:54.874298

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '10c7d06ecec4'
down_revision = '60d6b598d6cd'
branch_labels = None
depends_on = None


def upgrade():
    # Tambahkan kolom sementara agar pesanan lama tetap aman.
    op.add_column(
        'orders',
        sa.Column('shipping_fee', sa.Numeric(15, 2), nullable=True)
    )

    # Hitung ongkir historis berdasarkan total pesanan
    # dikurangi subtotal seluruh item pada pesanan tersebut.
    op.execute(
        sa.text('''
            UPDATE orders
            SET shipping_fee = total_amount - COALESCE(
                (
                    SELECT SUM(
                        order_items.quantity * order_items.price_at_purchase
                    )
                    FROM order_items
                    WHERE order_items.order_id = orders.id
                ),
                0
            )
        ''')
    )

    # Pastikan tidak ada hasil ongkir negatif.
    op.execute(
        sa.text('''
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM orders WHERE shipping_fee < 0
                ) THEN
                    RAISE EXCEPTION
                        'Backfill shipping_fee menghasilkan nilai negatif';
                END IF;
            END $$;
        ''')
    )

    op.alter_column(
        'orders',
        'shipping_fee',
        existing_type=sa.Numeric(15, 2),
        nullable=False
    )


def downgrade():
    op.drop_column('orders', 'shipping_fee')
