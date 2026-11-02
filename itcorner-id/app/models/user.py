
from datetime import date

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(13),
        nullable=True
    )

    password_hash = db.Column(
        db.Text,
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="Pelanggan"
    )

    joined = db.Column(
        db.Date,
        nullable=False,
        default=date.today
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Aktif"
    )

    __table_args__ = (
        db.Index(
            "idx_users_email",
            "email"
        ),
    )
