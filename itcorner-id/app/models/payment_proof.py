from app.extensions import db


class PaymentProof(db.Model):
    __tablename__ = "payment_proofs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    payment_id = db.Column(
        db.String(50),
        db.ForeignKey("payments.id"),
        nullable=False,
        index=True
    )

    filename = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    uploaded_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    review_status = db.Column(
        db.String(20),
        nullable=False,
        default="Menunggu",
        server_default="Menunggu"
    )

    reviewed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    rejection_reason = db.Column(
        db.String(500),
        nullable=True
    )

    payment = db.relationship(
        "Payment",
        backref=db.backref("proofs", lazy=True)
    )

    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewed_by]
    )

    __table_args__ = (
        db.CheckConstraint(
            "review_status IN ('Menunggu', 'Disetujui', 'Ditolak')",
            name="payment_proofs_review_status_check"
        ),
    )
