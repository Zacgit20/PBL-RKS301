
# Halaman utama dan healthcheck.

from flask import Blueprint, request, render_template, jsonify
from sqlalchemy import or_

from app.models import Product
from app.utils import format_rupiah

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/home')
def home():
    # Mengambil parameter pencarian dan filter
    search_query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', 'all').strip()
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    sort_by = request.args.get('sort', '').strip()
    in_stock_only = request.args.get('in_stock', '').strip()

    # Query produk aktif menggunakan SQLAlchemy ORM
    query = Product.query.filter(
        Product.is_active.is_(True)
    )

    # Filter pencarian
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
                Product.category.ilike(search_pattern)
            )
        )

    # Filter kategori
    if selected_category and selected_category.lower() != 'all':
        query = query.filter(
            Product.category.ilike(selected_category)
        )

    # Filter rentang harga
    if min_price is not None:
        query = query.filter(Product.price_num >= min_price)

    if max_price is not None:
        query = query.filter(Product.price_num <= max_price)

    # Filter stok
    if in_stock_only == '1':
        query = query.filter(Product.stock > 0)

    # Pengurutan dengan kolom yang diizinkan
    if sort_by == 'price_asc':
        query = query.order_by(Product.price_num.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price_num.desc())
    elif sort_by == 'name_asc':
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.id.asc())

    # Ambil hasil query dari PostgreSQL
    products = query.all()

    # Pertahankan format dictionary untuk kompatibilitas template
    formatted_products = []

    for product in products:
        product_data = {
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'category': product.category,
            'brand': product.brand,
            'price_num': product.price_num,
            'price': format_rupiah(product.price_num),
            'stock': product.stock,
            'description': product.description,
            'is_promo': product.is_promo,
            'image': product.image,
            'specs': product.specs
        }

        formatted_products.append(product_data)

    return render_template(
        'index.html',
        products=formatted_products,
        search_query=search_query,
        selected_category=selected_category
    )


@main_bp.route('/health', methods=['GET'])
def healthcheck():
    return jsonify({
        "status": "ok",
        "service": "ITCorner.id Secure E-Commerce"
    }), 200
