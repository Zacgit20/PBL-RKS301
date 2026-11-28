from app.extensions import db
from datetime import datetime, timezone


class ActivationRequest(db.Model):
    __tablename__ = "activation_requests"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    token_hash = db.Column(
        db.String(64),
        nullable=True,
        unique=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    verified_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Menunggu Verifikasi"
    )

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    reviewed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    rejection_reason = db.Column(
        db.String(255),
        nullable=True
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id]
    )

    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewed_by]
    )
