
from app.extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(
        db.String(50),
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    amount_num = db.Column(
        db.Numeric(15, 2),
        nullable=False
    )

    method = db.Column(
        db.String(50),
        nullable=False
    )

    payment_date = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        server_default="Menunggu Approval"
    )

    user = db.relationship(
        "User",
        backref="payments"
    )

    __table_args__ = (
        db.CheckConstraint(
            "amount_num >= 0",
            name="check_payment_amount_nonnegative"
        ),
        db.Index(
            "idx_payments_user_id",
            "user_id"
        ),
    )
