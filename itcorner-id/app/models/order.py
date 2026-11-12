from app.extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(
        db.String(50),
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    total_amount = db.Column(
        db.Numeric(15, 2),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Menunggu Pembayaran"
    )

    # Snapshot alamat pengiriman
    recipient_name = db.Column(
        db.String(100),
        nullable=False
    )

    recipient_phone = db.Column(
        db.String(20),
        nullable=False
    )

    shipping_address = db.Column(
        db.Text,
        nullable=False
    )

    province = db.Column(
        db.String(100),
        nullable=False
    )

    city = db.Column(
        db.String(100),
        nullable=False
    )

    district = db.Column(
        db.String(100),
        nullable=False
    )

    postal_code = db.Column(
        db.String(10),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    user = db.relationship(
        "User",
        backref="orders"
    )

    __table_args__ = (
        db.CheckConstraint(
            "total_amount >= 0",
            name="orders_total_amount_check"
        ),
    )