from app.extensions import db


class UserAddress(db.Model):
    __tablename__ = "user_addresses"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    label = db.Column(
        db.String(30),
        nullable=False,
        default="Rumah"
    )

    recipient_name = db.Column(
        db.String(100),
        nullable=False
    )

    recipient_phone = db.Column(
        db.String(20),
        nullable=False
    )

    address = db.Column(
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
        db.String(5),
        nullable=False
    )

    is_default = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.false()
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "shipping_addresses",
            cascade="all, delete-orphan"
        )
    )

    __table_args__ = (
        db.Index(
            "uq_user_addresses_one_default_per_user",
            "user_id",
            unique=True,
            postgresql_where=db.text("is_default IS TRUE")
        ),
    )
