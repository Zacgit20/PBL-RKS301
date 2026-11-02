from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    price_num = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=True)
    is_promo = db.Column(db.Boolean, nullable=False, default=False)
    image = db.Column(db.Text, nullable=True)
    specs = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.CheckConstraint("price_num >= 0", name="check_product_price_nonnegative"),
        db.CheckConstraint("stock >= 0", name="check_product_stock_nonnegative"),
    )
