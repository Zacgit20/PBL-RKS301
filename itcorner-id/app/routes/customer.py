
from flask import (
    Blueprint,
    current_app,
    render_template,
    redirect,
    url_for,
    session,
    request,
    jsonify,
    flash
)

from pathlib import Path
from decimal import Decimal
from uuid import uuid4

from app.extensions import db, limiter
from app.models import Product, User, Order, OrderItem, Payment, ProductReview
from app.utils import format_rupiah


customer_bp = Blueprint('customer', __name__)


def _get_session_cart():
    """Ambil dan validasi struktur keranjang dari session."""
    raw_cart = session.get('cart', [])

    if not isinstance(raw_cart, list):
        session['cart'] = []
        return []

    valid_items = []

    for item in raw_cart:
        if not isinstance(item, dict):
            continue

        try:
            product_id = int(item.get('product_id'))
            quantity = int(item.get('quantity'))

            if product_id <= 0 or quantity <= 0:
                continue

            valid_items.append({
                'product_id': product_id,
                'quantity': quantity
            })

        except (TypeError, ValueError):
            continue

    if valid_items != raw_cart:
        session['cart'] = valid_items

    return valid_items


def _add_product_to_cart(product_id, quantity):
    """Validasi produk dan stok sebelum menambah keranjang."""
    product = db.session.get(Product, product_id)

    if not product or not product.is_active:
        return False, "Produk tidak tersedia."

    if product.stock <= 0:
        return False, "Stok produk habis."

    cart_items = _get_session_cart()

    existing_item = next(
        (
            item for item in cart_items
            if item['product_id'] == product_id
        ),
        None
    )

    current_quantity = (
        existing_item['quantity'] if existing_item else 0
    )

    if current_quantity + quantity > product.stock:
        return False, (
            f"Stok tersedia hanya {product.stock} unit."
        )

    if existing_item:
        existing_item['quantity'] += quantity
    else:
        cart_items.append({
            'product_id': product_id,
            'quantity': quantity
        })

    session['cart'] = cart_items
    session.modified = True

    return True, "Produk berhasil ditambahkan."


# =========================
# DETAIL PRODUK
# =========================

@customer_bp.route('/detail/<int:product_id>')
def detail(product_id):
    product = db.session.get(Product, product_id)

    if not product or not product.is_active:
        return redirect(url_for('main.home'))

    # Pastikan gambar benar-benar berada di folder upload produk.
    image_url = None
    if product.image:
        upload_dir = (
            Path(current_app.static_folder) / 'uploads' / 'products'
        ).resolve()
        image_path = (
            Path(current_app.static_folder) / product.image
        ).resolve()

        if image_path.is_relative_to(upload_dir) and image_path.is_file():
            image_url = url_for('static', filename=product.image)

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
        'image_url': image_url,
        'specs': product.specs
    }

    reviews = (
        ProductReview.query
        .join(OrderItem, ProductReview.order_item_id == OrderItem.id)
        .filter(OrderItem.product_id == product.id)
        .order_by(ProductReview.created_at.desc())
        .all()
    )

    review_user = None
    eligible_order_items = []

    if session.get('user_id'):
        review_user = db.session.get(User, session.get('user_id'))

    if (
        review_user
        and review_user.status == 'Aktif'
        and review_user.role == 'Pelanggan'
    ):
        reviewed_item_ids = {
            review.order_item_id for review in reviews
        }

        eligible_order_items = (
            db.session.query(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .join(Payment, Payment.order_id == Order.id)
            .filter(
                OrderItem.product_id == product.id,
                Order.user_id == review_user.id,
                Payment.user_id == review_user.id,
                Payment.status == 'Disetujui'
            )
            .distinct()
            .all()
        )

        eligible_order_items = [
            item for item in eligible_order_items
            if item.id not in reviewed_item_ids
        ]

    average_rating = (
        sum(review.rating for review in reviews) / len(reviews)
        if reviews else 0
    )

    return render_template(
        'detail.html',
        product=product_data,
        product_specifications=product.specifications,
        reviews=reviews,
        average_rating=average_rating,
        eligible_order_items=eligible_order_items
    )




# =========================
# PRODUCT REVIEWS (FR-005)
# =========================

@customer_bp.route(
    '/detail/<int:product_id>/review/<int:order_item_id>',
    methods=['POST']
)
@limiter.limit("5 per minute", methods=["POST"])
def submit_product_review(product_id, order_item_id):
    user_id = session.get('user_id')

    if not user_id:
        flash("Silakan login untuk memberikan ulasan.", "warning")
        return redirect(url_for('auth.login'))

    user = db.session.get(User, user_id)

    if (
        user is None
        or user.status != 'Aktif'
        or user.role != 'Pelanggan'
    ):
        flash("Akun tidak memiliki izin untuk memberikan ulasan.", "danger")
        return redirect(url_for('customer.detail', product_id=product_id))

    product = db.session.get(Product, product_id)

    if product is None or not product.is_active:
        return redirect(url_for('main.home'))

    # Verifikasi item pembelian, pemilik pesanan, dan pembayaran.
    verified_item = (
        db.session.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .join(Payment, Payment.order_id == Order.id)
        .filter(
            OrderItem.id == order_item_id,
            OrderItem.product_id == product_id,
            Order.user_id == user.id,
            Payment.user_id == user.id,
            Payment.status == 'Disetujui'
        )
        .first()
    )

    if verified_item is None:
        flash(
            "Ulasan hanya dapat diberikan untuk pembelian milik Anda "
            "yang pembayarannya telah disetujui.",
            "danger"
        )
        return redirect(url_for('customer.detail', product_id=product_id))

    # Satu item pembelian hanya boleh memiliki satu ulasan.
    existing_review = ProductReview.query.filter_by(
        order_item_id=order_item_id
    ).first()

    if existing_review:
        flash("Item pembelian ini sudah memiliki ulasan.", "warning")
        return redirect(url_for('customer.detail', product_id=product_id))

    try:
        rating = int(request.form.get('rating', ''))
    except (TypeError, ValueError):
        rating = 0

    comment = (request.form.get('comment') or '').strip()

    if rating < 1 or rating > 5:
        flash("Rating harus bernilai 1 sampai 5.", "danger")
        return redirect(url_for('customer.detail', product_id=product_id))

    if not comment or len(comment) > 1000:
        flash("Komentar wajib diisi dan maksimal 1.000 karakter.", "danger")
        return redirect(url_for('customer.detail', product_id=product_id))

    review = ProductReview(
        order_item_id=verified_item.id,
        user_id=user.id,
        rating=rating,
        comment=comment
    )

    try:
        db.session.add(review)
        db.session.commit()
        flash("Ulasan berhasil dikirim.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Gagal menyimpan ulasan produk.")
        flash("Ulasan gagal disimpan. Silakan coba kembali.", "danger")

    return redirect(url_for('customer.detail', product_id=product_id))

# =========================
# KERANJANG
# =========================

@customer_bp.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    session.pop('_checkout_items', None)
    session.pop('_checkout_mode', None)

    if request.method == 'POST':
        try:
            product_id = int(request.form.get('product_id', ''))
            quantity = int(request.form.get('quantity', 1))

            if product_id <= 0 or quantity <= 0:
                raise ValueError

        except (TypeError, ValueError):
            flash("Data produk atau jumlah tidak valid.", "error")
            return redirect(url_for('customer.cart'))

        success, message = _add_product_to_cart(
            product_id,
            quantity
        )

        flash(message, "success" if success else "error")

        return redirect(url_for('customer.cart'))

    cart_items = _get_session_cart()

    product_ids = [
        item['product_id'] for item in cart_items
    ]

    products = {}

    if product_ids:
        product_rows = Product.query.filter(
            Product.id.in_(product_ids),
            Product.is_active.is_(True)
        ).all()

        products = {
            product.id: product
            for product in product_rows
        }

    displayed_items = []
    total_price = 0

    for item in cart_items:
        product = products.get(item['product_id'])

        if not product:
            continue

        quantity = item['quantity']
        item_total = product.price_num * quantity
        total_price += item_total

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
            'image': product.image
        }

        displayed_items.append({
            'product': product_data,
            'quantity': quantity,
            'subtotal': format_rupiah(item_total)
        })

    cart_count = sum(
        item['quantity'] for item in displayed_items
    )

    # Rekomendasi produk aktif yang belum ada di keranjang
    recommendation_query = Product.query.filter(
        Product.is_active.is_(True),
        Product.stock > 0
    )

    if product_ids:
        recommendation_query = recommendation_query.filter(
            ~Product.id.in_(product_ids)
        )

    recommendations = (
        recommendation_query
        .order_by(Product.updated_at.desc())
        .limit(3)
        .all()
    )

    return render_template(
        'cart.html',
        items=displayed_items,
        total=format_rupiah(total_price),
        cart_count=cart_count,
        recommendations=recommendations
    )


# =========================
# JUMLAH KERANJANG TERBARU
# =========================

@customer_bp.route('/cart-count', methods=['GET'])
def get_cart_count():
    cart_items = _get_session_cart()

    response = jsonify({
        'cart_count': sum(
            item['quantity'] for item in cart_items
        )
    })
    response.headers['Cache-Control'] = 'no-store'

    return response


# =========================
# TAMBAH KE KERANJANG
# =========================

@customer_bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({
            'error': 'Unauthorized'
        }), 401

    try:
        product_id = int(request.form.get('product_id', ''))
        quantity = int(request.form.get('quantity', 1))

        if product_id <= 0 or quantity <= 0:
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({
            'error': 'Input produk atau jumlah tidak valid.'
        }), 400

    success, message = _add_product_to_cart(
        product_id,
        quantity
    )

    if not success:
        return jsonify({
            'error': message
        }), 400

    cart_items = _get_session_cart()

    return jsonify({
        'status': 'success',
        'message': message,
        'cart_count': sum(
            item['quantity'] for item in cart_items
        )
    })


# =========================
# UBAH KUANTITAS KERANJANG
# =========================

@customer_bp.route('/update-cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({
            'error': 'Unauthorized'
        }), 401

    try:
        product_id = int(request.form.get('product_id', ''))
        action = request.form.get('action')

        if product_id <= 0 or action not in (
            'increase', 'decrease'
        ):
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({
            'error': 'Input tidak valid.'
        }), 400

    cart_items = _get_session_cart()

    item = next(
        (
            item for item in cart_items
            if item['product_id'] == product_id
        ),
        None
    )

    if not item:
        return jsonify({
            'error': 'Produk tidak ditemukan di keranjang.'
        }), 404

    product = db.session.get(Product, product_id)

    if not product or not product.is_active:
        return jsonify({
            'error': 'Produk tidak tersedia.'
        }), 404

    if action == 'increase':
        if item['quantity'] >= product.stock:
            return jsonify({
                'error': f"Stok maksimal {product.stock} unit."
            }), 400

        item['quantity'] += 1

    elif action == 'decrease':
        if item['quantity'] > 1:
            item['quantity'] -= 1

    session['cart'] = cart_items
    session.modified = True

    return jsonify({
        'status': 'success',
        'cart_count': sum(
            entry['quantity'] for entry in cart_items
        )
    })


# =========================
# HAPUS PRODUK DARI KERANJANG
# =========================

@customer_bp.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return jsonify({
            'error': 'Unauthorized'
        }), 401

    try:
        product_id = int(request.form.get('product_id', ''))

        if product_id <= 0:
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({
            'error': 'ID produk tidak valid.'
        }), 400

    cart_items = _get_session_cart()

    session['cart'] = [
        item for item in cart_items
        if item['product_id'] != product_id
    ]

    session.modified = True

    return jsonify({
        'status': 'success',
        'cart_count': sum(
            item['quantity'] for item in session['cart']
        )
    })



# =========================
# CHECKOUT
# =========================

SHIPPING_FEE = Decimal("35000")


@customer_bp.route('/buy-now', methods=['POST'])
def buy_now():
    if 'user_id' not in session:
        flash("Silakan login terlebih dahulu.", "warning")
        return redirect(url_for('auth.login'))

    try:
        product_id = int(request.form.get('product_id', ''))
        quantity = int(request.form.get('quantity', 1))

        if product_id <= 0 or quantity <= 0:
            raise ValueError

    except (TypeError, ValueError):
        flash("Data pembelian tidak valid.", "danger")
        return redirect(url_for('main.home'))

    product = db.session.get(Product, product_id)

    if not product or not product.is_active:
        flash("Produk tidak tersedia.", "warning")
        return redirect(url_for('main.home'))

    if quantity > product.stock:
        flash(
            f"Stok tersedia hanya {product.stock} unit.",
            "warning"
        )
        return redirect(
            url_for('customer.detail', product_id=product_id)
        )

    session['_checkout_items'] = [{
        'product_id': product_id,
        'quantity': quantity
    }]
    session['_checkout_mode'] = 'direct'
    session.modified = True

    return redirect(url_for('customer.checkout'))


@customer_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash("Silakan login terlebih dahulu.", "warning")
        return redirect(url_for('auth.login'))

    # Checkout biasa menggunakan keranjang utama.
    if request.method == 'GET' and session.get('_checkout_mode') != 'direct':
        session.pop('_checkout_items', None)
        session['_checkout_mode'] = 'cart'

    # Pilih sumber barang sesuai mode checkout.
    if session.get('_checkout_mode') == 'direct':
        cart_items = session.get('_checkout_items', [])
    else:
        cart_items = _get_session_cart()

    if not cart_items:
        flash("Tidak ada produk untuk checkout.", "warning")
        return redirect(url_for('customer.cart'))

    if request.method == 'GET':
        product_ids = [item['product_id'] for item in cart_items]

        products = Product.query.filter(
            Product.id.in_(product_ids),
            Product.is_active.is_(True)
        ).all()

        product_map = {product.id: product for product in products}
        items = []
        subtotal = Decimal("0")

        for cart_item in cart_items:
            product = product_map.get(cart_item['product_id'])

            if product is None:
                flash("Ada produk yang sudah tidak tersedia.", "warning")
                return redirect(url_for('customer.cart'))

            quantity = cart_item['quantity']

            if quantity > product.stock:
                flash(
                    f"Stok {product.name} tidak mencukupi. "
                    f"Stok tersedia: {product.stock}.",
                    "warning"
                )
                return redirect(url_for('customer.cart'))

            item_subtotal = product.price_num * quantity
            subtotal += item_subtotal

            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': item_subtotal
            })

        total = subtotal + SHIPPING_FEE

        return render_template(
            'checkout.html',
            items=items,
            subtotal=subtotal,
            shipping_fee=SHIPPING_FEE,
            total=total,
            current_user=db.session.get(User, session['user_id'])
        )

    # Pastikan akun masih aktif
    user = db.session.get(User, session.get('user_id'))

    if user is None or user.status != 'Aktif':
        session.clear()
        flash("Sesi akun tidak valid atau akun tidak aktif. Silakan login kembali.", "warning")
        return redirect(url_for('auth.login'))

    # Validasi data penerima
    recipient_name = request.form.get('nama_penerima', '').strip()
    recipient_phone = request.form.get('telepon', '').strip()
    shipping_address = request.form.get('alamat_lengkap', '').strip()
    province = request.form.get('provinsi', '').strip()
    city = request.form.get('kota', '').strip()
    district = request.form.get('kecamatan', '').strip()
    postal_code = request.form.get('kode_pos', '').strip()
    payment_method = request.form.get('metode_pembayaran', '').strip()

    required_fields = [
        recipient_name, recipient_phone, shipping_address,
        province, city, district, postal_code, payment_method
    ]

    if not all(required_fields):
        flash("Semua data pengiriman dan pembayaran wajib diisi.", "danger")
        return redirect(url_for('customer.checkout'))

    if (
        len(recipient_name) > 100
        or len(recipient_phone) > 20
        or len(shipping_address) > 500
        or len(province) > 100
        or len(city) > 100
        or len(district) > 100
        or len(postal_code) != 5
        or not postal_code.isdigit()
    ):
        flash("Data pengiriman tidak valid. Periksa kembali formulir.", "danger")
        return redirect(url_for('customer.checkout'))

    # Metode pembayaran harus diizinkan server
    allowed_payment_methods = {'Transfer BCA'}

    if payment_method not in allowed_payment_methods:
        flash("Metode pembayaran tidak valid.", "danger")
        return redirect(url_for('customer.checkout'))

    # Gabungkan produk yang sama agar quantity tidak bisa terhitung terpisah
    quantities = {}

    for item in cart_items:
        product_id = item['product_id']
        quantities[product_id] = quantities.get(product_id, 0) + item['quantity']

    try:
        # Kunci baris produk selama transaksi untuk mencegah overselling
        products = Product.query.filter(
            Product.id.in_(list(quantities.keys())),
            Product.is_active.is_(True)
        ).with_for_update().all()

        product_map = {product.id: product for product in products}

        if len(product_map) != len(quantities):
            flash("Ada produk yang tidak tersedia. Periksa keranjang.", "warning")
            return redirect(url_for('customer.cart'))

        subtotal = Decimal("0")
        order_items = []

        for product_id, quantity in quantities.items():
            product = product_map[product_id]

            if quantity > product.stock:
                db.session.rollback()
                flash(
                    f"Stok {product.name} tidak mencukupi. "
                    f"Stok tersedia: {product.stock}.",
                    "warning"
                )
                return redirect(url_for('customer.cart'))

            item_price = product.price_num
            subtotal += item_price * quantity

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=quantity,
                    price_at_purchase=item_price
                )
            )

        total_amount = subtotal + SHIPPING_FEE
        order_id = f"ORD-{uuid4().hex[:12].upper()}"
        payment_id = f"PAY-{uuid4().hex[:12].upper()}"

        order = Order(
            id=order_id,
            user_id=user.id,
            total_amount=total_amount,
            status="Menunggu Pembayaran",
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            shipping_address=shipping_address,
            province=province,
            city=city,
            district=district,
            postal_code=postal_code
        )

        for item in order_items:
            item.order_id = order_id
            db.session.add(item)

        payment = Payment(
            id=payment_id,
            user_id=user.id,
            order_id=order_id,
            amount_num=total_amount,
            method=payment_method,
            status="Menunggu Approval"
        )

        db.session.add(order)
        db.session.add(payment)

        # Kurangi stok dalam transaksi yang sama
        for product_id, quantity in quantities.items():
            product_map[product_id].stock -= quantity

        db.session.commit()

    except Exception:
        db.session.rollback()
        flash("Checkout gagal diproses. Silakan coba kembali.", "danger")
        return redirect(url_for('customer.checkout'))

    # Bersihkan hanya sumber checkout yang berhasil diproses.
    if session.get('_checkout_mode') == 'direct':
        session.pop('_checkout_items', None)
        session.pop('_checkout_mode', None)
    else:
        session['cart'] = []
        session.pop('_checkout_items', None)
        session.pop('_checkout_mode', None)

    session.modified = True

    flash("Pesanan berhasil dibuat. Silakan lanjutkan proses pembayaran.", "success")
    return redirect(url_for('customer.orders'))

# =========================
# ORDER HISTORY
# =========================

@customer_bp.route('/orders')
def orders():
    if 'user_id' not in session:
        flash("Silakan login terlebih dahulu.", "warning")
        return redirect(url_for('auth.login'))

    user = db.session.get(User, session['user_id'])

    if user is None or user.status != 'Aktif':
        session.clear()
        flash("Akun tidak valid atau tidak aktif.", "warning")
        return redirect(url_for('auth.login'))

    user_orders = (
        Order.query
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    order_ids = [order.id for order in user_orders]

    payment_map = {}
    if order_ids:
        user_payments = Payment.query.filter(
            Payment.user_id == user.id,
            Payment.order_id.in_(order_ids)
        ).all()
        payment_map = {payment.order_id: payment for payment in user_payments}

    payments = []

    for order in user_orders:
        payment = payment_map.get(order.id)
        items = order.items
        first_item = items[0] if items else None

        product_name = "Pesanan"
        quantity = 0
        unit_price = Decimal("0")

        if first_item:
            product_name = (
                first_item.product.name
                if first_item.product
                else "Produk tidak tersedia"
            )
            if len(items) > 1:
                product_name += f" dan {len(items) - 1} produk lainnya"

            quantity = sum(item.quantity for item in items)
            unit_price = first_item.price_at_purchase

        payments.append({
            'id': order.id,
            'date': order.created_at.strftime("%d %b %Y")
                    if order.created_at else "-",
            'amount': format_rupiah(order.total_amount),
            'status': payment.status if payment else order.status,
            'method': payment.method if payment else "-",
            'product_name': product_name,
            'quantity': quantity,
            'unit_price': format_rupiah(unit_price)
        })

    latest_payment = payments[0] if payments else None

    return render_template(
        'orders.html',
        payments=payments,
        latest_payment=latest_payment
    )


# =========================
# CONTEXT PROCESSOR
# =========================

@customer_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """Menampilkan dan memperbarui informasi profil pengguna."""
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('auth.login'))

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        session.clear()
        return redirect(url_for('auth.login'))

    user = db.session.get(User, user_id)

    if not user or user.status != 'Aktif':
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()

        if not name:
            flash('Nama lengkap wajib diisi.', 'error')
            return redirect(url_for('customer.profile'))

        if len(name) > 100:
            flash('Nama maksimal 100 karakter.', 'error')
            return redirect(url_for('customer.profile'))

        if phone:
            phone_digits = phone[1:] if phone.startswith('+') else phone

            if (
                not phone_digits.isdigit()
                or not 8 <= len(phone_digits) <= 13
                or len(phone) > 13
            ):
                flash(
                    'Nomor telepon harus berisi 8–13 digit '
                    'dan boleh diawali tanda +.',
                    'error'
                )
                return redirect(url_for('customer.profile'))

        try:
            user.name = name
            user.phone = phone or None

            db.session.commit()

            session['user_name'] = user.name

            flash('Informasi profil berhasil diperbarui.', 'success')

        except Exception:
            db.session.rollback()
            flash(
                'Perubahan profil gagal disimpan. Silakan coba kembali.',
                'error'
            )

        return redirect(url_for('customer.profile'))

    return render_template('profile.html', user=user)


@customer_bp.app_context_processor
def inject_cart_count():
    cart_items = _get_session_cart()

    return {
        'cart_count': sum(
            item['quantity'] for item in cart_items
        ),
        'format_rupiah': format_rupiah
    }
