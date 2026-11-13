
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request,
    jsonify,
    flash
)

from decimal import Decimal
from uuid import uuid4

from app.extensions import db
from app.models import Product, User, Order, OrderItem, Payment
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

    return render_template(
        'detail.html',
        product=product_data
    )


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

    return render_template(
        'cart.html',
        items=displayed_items,
        total=format_rupiah(total_price),
        cart_count=cart_count
    )


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

    if action == 'increase':
        product = db.session.get(Product, product_id)

        if not product or not product.is_active:
            return jsonify({
                'error': 'Produk tidak tersedia.'
            }), 404

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

@customer_bp.route('/profile')
def profile():
    """Menampilkan profil pengguna dari PostgreSQL."""
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
