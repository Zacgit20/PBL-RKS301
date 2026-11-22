from app.extensions import db


class ProductSpecification(db.Model):
    __tablename__ = "product_specifications"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    attribute_name = db.Column(
        db.String(80),
        nullable=False
    )

    attribute_value = db.Column(
        db.String(300),
        nullable=False
    )

    sort_order = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    product = db.relationship(
        "Product",
        backref=db.backref(
            "specifications",
            cascade="all, delete-orphan",
            order_by="ProductSpecification.sort_order"
        )
    )

    __table_args__ = (
        db.CheckConstraint(
            "length(trim(attribute_name)) BETWEEN 1 AND 80",
            name="product_specifications_name_length_check"
        ),
        db.CheckConstraint(
            "length(trim(attribute_value)) BETWEEN 1 AND 300",
            name="product_specifications_value_length_check"
        ),
        db.CheckConstraint(
            "sort_order >= 0",
            name="product_specifications_sort_order_check"
        ),
    )
