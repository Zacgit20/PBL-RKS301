from app.extensions import db


class ProductReview(db.Model):
    __tablename__ = "product_reviews"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    order_item_id = db.Column(
        db.Integer,
        db.ForeignKey("order_items.id"),
        nullable=False,
        unique=True,
        index=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    rating = db.Column(
        db.SmallInteger,
        nullable=False
    )

    comment = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    order_item = db.relationship(
        "OrderItem",
        backref="review"
    )

    user = db.relationship(
        "User",
        backref="product_reviews"
    )

    __table_args__ = (
        db.CheckConstraint(
            "rating BETWEEN 1 AND 5",
            name="product_reviews_rating_check"
        ),
        db.CheckConstraint(
            "length(trim(comment)) BETWEEN 1 AND 1000",
            name="product_reviews_comment_length_check"
        ),
    )
