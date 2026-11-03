from app.extensions import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    order_id = db.Column(
        db.String(50),
        db.ForeignKey("orders.id"),
        nullable=False,
        index=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    price_at_purchase = db.Column(
        db.Numeric(15, 2),
        nullable=False
    )

    order = db.relationship(
        "Order",
        backref="items"
    )

    product = db.relationship(
        "Product"
    )

    __table_args__ = (
        db.CheckConstraint(
            "quantity > 0",
            name="order_items_quantity_check"
        ),
        db.CheckConstraint(
            "price_at_purchase >= 0",
            name="order_items_price_check"
        ),
    )