import sys
import os
import logging
import uuid
from dotenv import load_dotenv
# Membaca konfigurasi dari file .env
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from dummy_db import products_db, users_db, payments_db, format_rupiah, get_current_date_indo
from models.db import execute_query
from app.extensions import db, migrate
from sqlalchemy.engine import URL
from app.models import User, Product, Payment, Order, OrderItem
from decimal import Decimal, InvalidOperation


app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]


# ==========================================
# KONFIGURASI DATABASE (SQLAlchemy)
# ==========================================
database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER", "postgres"),
    password=os.environ["DB_PASSWORD"],
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "itcorner-db")
)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate.init_app(app, db)

# ==========================================
# KONFIGURASI LOGGING (MODUL 8 / OWASP A09)
# ==========================================
logging.basicConfig(
    filename='app_activity.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

log_werkzeug = logging.getLogger('werkzeug')
log_werkzeug.setLevel(logging.ERROR)



# ==========================================
# RUTE CLIENT / USER
# ==========================================
@app.route('/')
@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 1. Ambil parameter filter dan pencarian dari URL
    search_query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', 'all').strip()
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    sort_by = request.args.get('sort', '').strip()
    in_stock_only = request.args.get('in_stock', '').strip()

    # 2. Ambil produk dari PostgreSQL
    filtered_db = execute_query(
        """
        SELECT id, sku, name, category, brand,
               price_num, stock, description, is_promo,
               image, specs
        FROM products
        WHERE is_active = TRUE
        ORDER BY id
        """,
        fetch_all=True
    )

    # 4. Filter berdasarkan kata kunci
    if search_query:
        filtered_db = [
            p for p in filtered_db
            if search_query.lower() in p['name'].lower()
            or search_query.lower() in (p.get('description') or '').lower()
            or search_query.lower() in (p.get('category') or '').lower()
        ]

    # 5. Filter berdasarkan kategori
    if selected_category and selected_category.lower() != 'all':
        filtered_db = [
            p for p in filtered_db
            if (p.get('category') or '').lower() == selected_category.lower()
        ]

    # 6. Filter berdasarkan rentang harga
    if min_price is not None:
        filtered_db = [
            p for p in filtered_db if p.get('price_num', 0) >= min_price
        ]

    if max_price is not None:
        filtered_db = [
            p for p in filtered_db if p.get('price_num', 0) <= max_price
        ]

    # 7. Filter produk yang tersedia
    if in_stock_only == '1':
        filtered_db = [
            p for p in filtered_db if p.get('stock', 0) > 0
        ]

    # 8. Sorting produk
    if sort_by == 'price_asc':
        filtered_db.sort(key=lambda x: x.get('price_num', 0))
    elif sort_by == 'price_desc':
        filtered_db.sort(
            key=lambda x: x.get('price_num', 0), reverse=True
        )
    elif sort_by == 'name_asc':
        filtered_db.sort(key=lambda x: x.get('name', ''))

    # 9. Format harga
    formatted_products = []
    for p in filtered_db:
        p_copy = p.copy()
        p_copy['price'] = format_rupiah(p['price_num'])
        formatted_products.append(p_copy)

    # 10. Kirim data ke template
    return render_template(
        'index.html',
        products=formatted_products,
        search_query=search_query,
        selected_category=selected_category
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    email_error = None
    password_error = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email:
            email_error = "Email wajib diisi."
        if not password:
            password_error = "Password wajib diisi."
        elif len(password) < 8:
            password_error = "Password minimal 8 karakter."

        if email and password and len(password) >= 8:
            user = execute_query(
                """
                SELECT id, name, email, password_hash, role, status
                FROM users
                WHERE email = %s
                """,
                (email,),
                fetch_one=True
            )

            if not user:
                email_error = "Email belum terdaftar."
                logging.warning(
                    f"LOGIN FAILED: Email '{email}' tidak ditemukan dari IP {request.remote_addr}"
                )

            elif not check_password_hash(user['password_hash'], password):
                password_error = "Kata sandi salah."
                logging.warning(
                    f"LOGIN FAILED: Password salah untuk email '{email}' dari IP {request.remote_addr}"
                )

            elif user['status'] != 'Aktif':
                email_error = "Akun tidak aktif. Silakan hubungi admin."

            else:
                session.clear()
                session['user_id'] = user['id']
                session['email'] = user['email']
                session['user_name'] = user['name']
                session['role'] = user['role']

                logging.info(
                    f"LOGIN SUCCESS: User '{email}' ({user['role']}) berhasil login dari IP {request.remote_addr}"
                )

                if user['role'] == 'Admin':
                    return redirect(url_for('admin_dashboard'))

                return redirect(url_for('home'))
    return render_template('login.html', email_error=email_error, password_error=password_error)

@app.route('/logout')
def logout():
    user_email = session.get('user_name', 'Unknown')
    logging.info(f"LOGOUT: User '{user_email}' telah logout dari IP {request.remote_addr}")
    session.clear()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form_error = None
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        terms = request.form.get('terms')

        # 1. Validasi Kolom Kosong
        if not fullname or not email or not phone or not password or not confirm_password:
            form_error = "Harap isi semua kolom pendaftaran terlebih dahulu."
            return render_template('register.html', form_error=form_error)

        # 2. Validasi Format Email
        if '@' not in email or '.' not in email:
            form_error = "Format alamat email tidak valid."
            return render_template('register.html', form_error=form_error)

        # 3. Validasi Nomor HP Harus Angka
        if not phone.isdigit():
            form_error = "Nomor telepon hanya boleh berisi angka."
            return render_template('register.html', form_error=form_error)
        elif len(phone) < 10 or len(phone) > 13:
            form_error = "Nomor telepon harus terdiri dari 10 hingga 13 digit."
            return render_template('register.html', form_error=form_error)

        # 4. Validasi Panjang Password
        if len(password) < 8:
            form_error = "Kata sandi minimal 8 karakter."
            return render_template('register.html', form_error=form_error)

        # 5. Validasi Konfirmasi Password
        if password != confirm_password:
            form_error = "Konfirmasi kata sandi tidak cocok."
            return render_template('register.html', form_error=form_error)

        # 6. Validasi Syarat & Ketentuan
        if not terms:
            form_error = "Anda harus menyetujui Syarat & Ketentuan terlebih dahulu."
            return render_template('register.html', form_error=form_error)


        # 7. Cek Duplikasi Email di PostgreSQL
        existing_user = execute_query(
            "SELECT id FROM users WHERE email = %s",
            (email,),
            fetch_one=True
        )

        if existing_user:
            form_error = "Email sudah terdaftar. Silakan gunakan email lain atau login."
            logging.warning(
                f"REGISTER FAILED: Email '{email}' sudah terdaftar dari IP {request.remote_addr}"
            )
            return render_template('register.html', form_error=form_error)

        # 8. Hash Password
        hashed_password = generate_password_hash(password)

        # 9. Simpan Pengguna ke PostgreSQL
        execute_query(
            """
            INSERT INTO users (name, email, phone, password_hash, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (fullname, email, phone, hashed_password, 'Pelanggan'),
            commit=True
        )

        logging.info(
            f"REGISTER SUCCESS: User '{email}' ({fullname}) berhasil mendaftar dari IP {request.remote_addr}"
        )

        # Arahkan pengguna ke halaman login setelah berhasil mendaftar
        return redirect(url_for('login'))

    # Tampilkan halaman register ketika menerima GET
    return render_template('register.html', form_error=form_error)

@app.route('/detail/<int:product_id>')
def detail(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Ambil produk dari PostgreSQL
    product = db.session.get(Product, product_id)

    if not product:
        return redirect(url_for('home'))

    # Ubah objek model menjadi dictionary untuk template
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

    return render_template('detail.html', product=product_data)

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'cart' not in session:
        session['cart'] = []

    if request.method == 'POST':
        try:
            product_id = int(request.form.get('product_id'))
            quantity = int(request.form.get('quantity', 1))
        except (TypeError, ValueError):
            return redirect(url_for('cart'))

        cart = session['cart']
        found = False
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] += quantity
                found = True
                break

        if not found:
            cart.append({'product_id': product_id, 'quantity': quantity})

        session['cart'] = cart
        session.modified = True
        return redirect(url_for('cart'))

    cart_items = []
    total_price = 0
    for item in session.get('cart', []):
        prod = next((p for p in products_db if p['id'] == item['product_id']), None)
        if prod:
            item_total = prod['price_num'] * item['quantity']
            total_price += item_total

            # Buat salinan data produk dan tambahkan harga terformat
            prod_copy = prod.copy()
            prod_copy['price'] = format_rupiah(prod['price_num'])

            cart_items.append({
                'product': prod_copy,
                'quantity': item['quantity'],
                'subtotal': format_rupiah(item_total)
            })

    return render_template('cart.html', items=cart_items, total=format_rupiah(total_price))


@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    if 'cart' not in session:
        session['cart'] = []

    try:
        product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity', 1))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid input'}), 400

    cart = session['cart']
    found = False
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            found = True
            break

    if not found:
        cart.append({'product_id': product_id, 'quantity': quantity})

    session['cart'] = cart
    session.modified = True

    return jsonify({'status': 'success', 'cart_count': sum(item['quantity'] for item in cart)})


@app.route('/update-cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        product_id = int(request.form.get('product_id'))
        action = request.form.get('action')
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid input'}), 400

    cart = session.get('cart', [])
    for item in cart:
        if item['product_id'] == product_id:
            if action == 'increase':
                item['quantity'] += 1
            elif action == 'decrease' and item['quantity'] > 1:
                item['quantity'] -= 1
            break

    session['cart'] = cart
    session.modified = True
    return jsonify({'status': 'success'})


@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        product_id = int(request.form.get('product_id'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid product ID'}), 400

    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item['product_id'] != product_id]
    session.modified = True
    return jsonify({'status': 'success'})


@app.context_processor
def inject_cart_count():
    cart = session.get('cart', [])
    cart_count = sum(item['quantity'] for item in cart)
    return dict(cart_count=cart_count, format_rupiah=format_rupiah)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int) or 1
        qty = request.form.get('quantity', type=int) or 1
        payment_method = request.form.get('payment_method') or "Transfer BCA"

        # 1. Validasi quantity wajib angka positif
        if qty <= 0:
            return "Jumlah barang tidak valid!", 400

        # 2. Cari produk & cek kecukupan stok
        product = next((p for p in products_db if p['id'] == product_id), None)
        if not product:
            return "Produk tidak ditemukan!", 404

        if product['stock'] < qty:
            return f"Stok {product['name']} tidak mencukupi! Tersisa: {product['stock']}", 400

        # 3. Potong stok jika valid
        product['stock'] -= qty
        total_amount = product['price_num'] * qty

        # 4. Simpan ke payments_db dengan user_id & format tanggal aman
        inv_id = f"INV-20261018-0{len(payments_db) + 1}"
        payments_db.append({
            "id": inv_id,
            "user_id": session.get('user_id'),
            "user": session.get('user_name', 'Pelanggan'),
            "amount_num": total_amount,
            "amount": format_rupiah(total_amount),
            "method": payment_method,
            "date": datetime.now().strftime("%d %b %Y"),
            "status": "Menunggu Approval"
        })

        return redirect(url_for('orders'))

    return render_template('checkout.html')

@app.route('/orders')
def orders():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    # Ambil HANYA pesanan milik user aktif
    user_payments = [o for o in payments_db if o.get('user_id') == session['user_id']]
    return render_template('orders.html', payments=user_payments)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Ambil data user dari session atau dummy_db
    user_info = {
        'name': session.get('user_name', 'Pengguna'),
        'email': session.get('email', '-'),
        'role': session.get('role', 'Pelanggan')
    }
    return render_template('profile.html', user=user_info)

@app.route('/forgot_password',methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            return render_template('forgot_password.html', email_error="Email tidak boleh kosong!")

        # Cek apakah email terdaftar di database
        user_exists = any(u['email'].lower() == email for u in users_db)

        if not user_exists:
            return render_template('forgot_password.html', email_error="Email tidak terdaftar dalam sistem!")

        # Jika email ditemukan, berikan pesan sukses (simulasi kirim instruksi)
        logging.info(f"Permintaan reset password dikirimkan untuk email: {email}")
        return render_template('forgot_password.html', success_message="Tautan pemulihan kata sandi telah dikirimkan ke email Anda.")

    return render_template('forgot_password.html')


# ==========================================
# RUTE ADMIN (SEMUA LOGIKA HITUNG OTOMATIS)
# ==========================================

@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'Admin':
        logging.warning(
            "UNAUTHORIZED ACCESS: Percobaan akses admin tanpa izin dari IP %s",
            request.remote_addr
        )
        return redirect(url_for('login'))

    from datetime import date, timedelta

    try:
        current_date = get_current_date_indo()

        # Mengambil ringkasan pembayaran dari PostgreSQL
        payment_stats = execute_query("""
            SELECT
                COALESCE(
                    SUM(amount_num) FILTER (
                        WHERE status = 'Disetujui'
                    ), 0
                ) AS total_omzet,
                COUNT(*) FILTER (
                    WHERE status = 'Menunggu Approval'
                ) AS menunggu_bayar,
                COUNT(*) FILTER (
                    WHERE status = 'Disetujui'
                ) AS disetujui,
                COUNT(*) FILTER (
                    WHERE status = 'Ditolak'
                ) AS ditolak
            FROM payments
        """, fetch_one=True)

        product_stats = execute_query(
            "SELECT COUNT(*) AS total FROM products",
            fetch_one=True
        )

        user_stats = execute_query(
            "SELECT COUNT(*) AS total FROM users",
            fetch_one=True
        )

        # Mengambil omzet harian selama 7 hari terakhir
        daily_revenue = execute_query("""
            SELECT
                payment_date::date AS tanggal,
                SUM(amount_num) AS omzet
            FROM payments
            WHERE status = 'Disetujui'
              AND payment_date >= CURRENT_DATE - INTERVAL '6 days'
              AND payment_date < CURRENT_DATE + INTERVAL '1 day'
            GROUP BY payment_date::date
            ORDER BY tanggal
        """, fetch_all=True)

        # Mengubah hasil query menjadi dictionary berdasarkan tanggal
        revenue_by_date = {
            row['tanggal']: row['omzet']
            for row in daily_revenue
        }

        # Melengkapi tanggal yang tidak memiliki transaksi dengan omzet 0
        chart_data = []

        for i in range(6, -1, -1):
            chart_date = date.today() - timedelta(days=i)
            omzet = revenue_by_date.get(chart_date, 0)

            chart_data.append({
                'tanggal': chart_date,
                'label': chart_date.strftime('%d/%m'),
                'omzet': float(omzet)
            })

        # Menentukan nilai tertinggi untuk skala tinggi batang grafik
        max_omzet = max(
            (item['omzet'] for item in chart_data),
            default=0
        )

        for item in chart_data:
            item['tinggi'] = (
                max(8, (item['omzet'] / max_omzet) * 100)
                if max_omzet > 0 and item['omzet'] > 0
                else 0
            )

        # Menghitung jumlah pesanan berdasarkan status
        order_stats = execute_query("""
            SELECT
                COUNT(*) FILTER (
                    WHERE status = 'Menunggu Pembayaran'
                ) AS menunggu_bayar,
                COUNT(*) FILTER (
                    WHERE status = 'Diproses'
                ) AS diproses,
                COUNT(*) FILTER (
                    WHERE status = 'Dikirim'
                ) AS dikirim,
                COUNT(*) FILTER (
                    WHERE status = 'Selesai'
                ) AS selesai
            FROM orders
        """, fetch_one=True)

        status_counts = {
            "menunggu_bayar": payment_stats['menunggu_bayar'],
            "disetujui": payment_stats['disetujui'],
            "ditolak": payment_stats['ditolak'],
            "diproses": order_stats['diproses'],
            "dikirim": order_stats['dikirim'],
            "selesai": order_stats['selesai']
        }

        stats = {
            "total_penjualan": format_rupiah(
                payment_stats['total_omzet']
            ),
            "pesanan_baru": status_counts['menunggu_bayar'],
            "total_produk": product_stats['total'],
            "total_user": user_stats['total']
        }

        # Mengambil 5 produk untuk ringkasan dashboard
        products_db_list = execute_query("""
            SELECT *
            FROM products
            ORDER BY id ASC
            LIMIT 5
        """, fetch_all=True)

        formatted_products = []

        for product in products_db_list:
            product_copy = dict(product)
            product_copy['price'] = format_rupiah(
                product['price_num']
            )
            formatted_products.append(product_copy)

        logging.info(
            "ADMIN DASHBOARD: Admin '%s' membuka dashboard",
            session.get('user_name')
        )

        return render_template(
            'admin/dashboard.html',
            stats=stats,
            products=formatted_products,
            status_counts=status_counts,
            current_date=current_date,
            chart_data=chart_data
        )

    except Exception:
        logging.exception(
            "ERROR: Gagal mengambil data dashboard Admin"
        )
        flash("Gagal mengambil data dashboard.", "error")
        return redirect(url_for('login'))


@app.route('/admin/products', methods=['GET'])
def admin_products():
    if 'role' not in session or session['role'] != 'Admin':
        logging.warning(
            "UNAUTHORIZED ACCESS: User '%s' mencoba mengakses halaman produk admin",
            session.get('email', 'Unknown')
        )
        return redirect(url_for('login'))

    try:
        products_db_list = Product.query.order_by(Product.id.asc()).all()

        logging.info(
            "ADMIN VIEW PRODUCTS: Admin '%s' melihat daftar produk",
            session.get('user_name')
        )

        formatted_products = []

        for p in products_db_list:
            formatted_products.append({
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "category": p.category,
                "brand": p.brand,
                "price_num": p.price_num,
                "price": format_rupiah(p.price_num),
                "stock": p.stock,
                "is_active": p.is_active,
                "description": p.description
            })

        edit_id = request.args.get('edit', type=int)
        selected_product = None

        if edit_id is not None:
            selected_product = db.session.get(Product, edit_id)

        return render_template(
            'admin/products.html',
            products=formatted_products,
            selected_product=selected_product
        )

    except Exception:
        logging.exception("ERROR: Gagal mengambil daftar produk dari database")
        flash("Terjadi kesalahan saat mengambil data produk.", "error")
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/product/save', methods=['POST'])
def save_product():
    # 1. Memeriksa hak akses Admin
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    # 2. Mengambil data dari form
    product_id = request.form.get('product_id', '').strip()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    brand = request.form.get('brand', '').strip()
    description = request.form.get('description', '').strip()

    # 3. Validasi nama produk
    if not name:
        flash('Nama produk wajib diisi.', 'danger')
        return redirect(url_for('admin_products'))

    # 4. Mengambil dan membersihkan harga
    price_raw = request.form.get('price', '').strip()

    price_raw = (
        price_raw
        .replace('Rp', '')
        .replace('rp', '')
        .replace('.', '')
        .replace(' ', '')
    )

    # 5. Validasi harga menggunakan Decimal
    try:
        price_num = Decimal(price_raw)

        if not price_num.is_finite() or price_num <= 0:
            raise InvalidOperation

    except (InvalidOperation, ValueError):
        flash('Harga harus berupa angka lebih dari Rp0.', 'danger')
        return redirect(url_for('admin_products'))

    # 6. Mengambil dan memvalidasi stok
    stock_raw = request.form.get('stock', '').strip()

    if not stock_raw.isdigit():
        flash('Stok harus berupa bilangan bulat nonnegatif.', 'danger')
        return redirect(url_for('admin_products'))

    stock = int(stock_raw)

    # 7. UPDATE PRODUK (menggunakan PostgreSQL)
    if product_id:
        try:
            p_id = int(product_id)

            # Mencari produk berdasarkan ID di PostgreSQL
            product = db.session.get(Product, p_id)

            if not product:
                flash('Produk tidak ditemukan.', 'danger')
                return redirect(url_for('admin_products'))

            # Memperbarui data produk
            product.name = name
            product.category = category or None
            product.brand = brand or None
            product.price_num = price_num
            product.stock = stock
            product.description = description or None

            # Menyimpan perubahan ke database
            db.session.commit()

            logging.info(
                f"PRODUCT UPDATED: Admin '{session.get('user_name')}' "
                f"memperbarui produk '{name}' (ID: {p_id})"
            )

            flash('Produk berhasil diperbarui.', 'success')

            return redirect(
                url_for('admin_products', edit=p_id) + '#form-produk'
            )

        except ValueError:
            db.session.rollback()
            flash('ID produk tidak valid.', 'danger')

        except Exception:
            db.session.rollback()
            logging.exception("Gagal memperbarui produk.")
            flash('Produk gagal diperbarui.', 'danger')

    # 8. CREATE PRODUK (menggunakan PostgreSQL)
    else:
        new_product = Product(
            sku=f"ITC-{uuid.uuid4().hex[:12].upper()}",
            name=name,
            category=category or None,
            brand=brand or None,
            price_num=price_num,
            stock=stock,
            description=description or None,
            is_promo=False
        )

        try:
            db.session.add(new_product)
            db.session.commit()

            logging.info(
                f"PRODUCT ADDED: Admin '{session.get('user_name')}' "
                f"menambahkan produk '{name}' (ID: {new_product.id})"
            )

            flash('Produk berhasil ditambahkan.', 'success')

        except Exception:
            db.session.rollback()

            logging.exception(
                "Gagal menambahkan produk ke database."
            )

            flash('Produk gagal ditambahkan.', 'danger')

    return redirect(url_for('admin_products'))

@app.route('/admin/product/toggle/<int:product_id>', methods=['POST'])
def toggle_product_status(product_id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    try:
        product = db.session.get(Product, product_id)

        if not product:
            flash("Produk tidak ditemukan.", "error")
            return redirect(url_for('admin_products'))

        product.is_active = not product.is_active
        new_status = "Aktif" if product.is_active else "Nonaktif"

        db.session.commit()

        logging.info(
            "PRODUCT STATUS CHANGED: Admin '%s' mengubah status produk '%s' menjadi %s",
            session.get('user_name'),
            product.name,
            new_status
        )

        flash(f"Status produk berhasil diubah menjadi {new_status}.", "success")

    except Exception:
        db.session.rollback()
        logging.exception(
            "ERROR: Gagal mengubah status produk ID %s",
            product_id
        )
        flash("Gagal mengubah status produk.", "error")

    return redirect(url_for('admin_products'))

@app.route('/admin/product/permanently-delete/<int:product_id>', methods=['POST'])
def permanently_delete_product(product_id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    try:
        product = db.session.get(Product, product_id)

        if not product:
            flash("Produk tidak ditemukan.", "error")
            return redirect(url_for('admin_products'))

        # Periksa apakah produk pernah digunakan dalam pesanan
        order_item = OrderItem.query.filter_by(
            product_id=product_id
        ).first()

        if order_item:
            flash(
                "Produk tidak dapat dihapus karena memiliki riwayat pesanan.",
                "error"
            )
            return redirect(url_for('admin_products'))

        product_name = product.name

        db.session.delete(product)
        db.session.commit()

        logging.info(
            "PRODUCT PERMANENTLY DELETED: Admin '%s' menghapus produk '%s' (ID: %s)",
            session.get('user_name'),
            product_name,
            product_id
        )

        flash("Produk berhasil dihapus permanen.", "success")

    except Exception:
        db.session.rollback()
        logging.exception(
            "ERROR: Gagal menghapus permanen produk ID %s",
            product_id
        )
        flash("Gagal menghapus produk.", "error")

    return redirect(url_for('admin_products'))

@app.route('/admin/users')
def admin_users():
    if 'role' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip().lower()
    role_filter = request.args.get('role', 'all').strip()
    status_filter = request.args.get('status', 'all').strip()
    edit_id = request.args.get('edit', type=int)

    # Hitung statistik untuk stat card
    stats = {
        "total": len(users_db),
        "pelanggan_aktif": len([u for u in users_db if u.get('role') == 'Pelanggan' and u.get('status') == 'Aktif']),
        "admin": len([u for u in users_db if u.get('role') == 'Admin']),
        "nonaktif": len([u for u in users_db if u.get('status') == 'Nonaktif'])
    }

    # Filter tabel user
    filtered_users = users_db
    if q:
        filtered_users = [u for u in filtered_users if q in u['name'].lower() or q in u['email'].lower()]
    if role_filter != 'all':
        filtered_users = [u for u in filtered_users if u.get('role') == role_filter]
    if status_filter != 'all':
        filtered_users = [u for u in filtered_users if u.get('status') == status_filter]

    selected_user = next((u for u in users_db if u['id'] == edit_id), None) if edit_id else None

    return render_template(
        'admin/users.html',
        stats=stats,
        users=filtered_users,
        selected_user=selected_user,
        search_query=q,
        role_filter=role_filter,
        status_filter=status_filter
    )

@app.route('/admin/users/save', methods=['POST'])
def save_user_settings():
    if 'role' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    user_id = request.form.get('user_id', type=int)
    new_role = request.form.get('role')
    new_status = request.form.get('status')

    user = next((u for u in users_db if u['id'] == user_id), None)
    if user:
        if user['id'] == session.get('user_id') and new_status == 'Nonaktif':
            return redirect(url_for('admin_users'))

        user['role'] = new_role
        user['status'] = new_status
        logging.info(f"USER UPDATED: Admin '{session.get('user_name')}' mengubah user ID {user_id} (Role: {new_role}, Status: {new_status})")

    return redirect(url_for('admin_users'))





# ==========================================
# RUTE ADMIN: APPROVAL PEMBAYARAN
# ==========================================
@app.route('/admin/payments')
def admin_payments():
    if 'role' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip().lower()
    status_filter = request.args.get('status', 'Menunggu Approval').strip()
    selected_inv = request.args.get('inv')

    filtered_payments = payments_db
    if q:
        filtered_payments = [p for p in filtered_payments if q in p['id'].lower() or q in p['user'].lower()]
    if status_filter != 'all':
        filtered_payments = [p for p in filtered_payments if p.get('status') == status_filter]

    selected_payment = None
    if selected_inv:
        selected_payment = next((p for p in payments_db if p['id'] == selected_inv), None)
    elif filtered_payments:
        selected_payment = filtered_payments[0]

    pending_count = len([p for p in payments_db if p.get('status') == 'Menunggu Approval'])

    return render_template(
        'admin/payments.html',
        payments=filtered_payments,
        selected_payment=selected_payment,
        pending_count=pending_count,
        search_query=q,
        status_filter=status_filter
    )

@app.route('/admin/payments/action', methods=['POST'])
def process_payment_action():
    if 'role' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    payment_id = request.form.get('payment_id')
    action = request.form.get('action')
    reason = request.form.get('reason', '').strip()

    payment = next((p for p in payments_db if p['id'] == payment_id), None)
    if payment:
        if action == 'approve':
            payment['status'] = 'Disetujui'
            logging.info(f"PAYMENT APPROVED: Invoice {payment_id} disetujui oleh Admin '{session.get('user_name')}'")
        elif action == 'reject':
            payment['status'] = 'Ditolak'
            payment['reject_reason'] = reason
            logging.warning(f"PAYMENT REJECTED: Invoice {payment_id} ditolak oleh Admin '{session.get('user_name')}' (Alasan: {reason})")

    return redirect(url_for('admin_payments'))

# Endpoint wajib untuk pengecekan kesehatan server oleh CI/CD (healthcheck.sh)
@app.route("/health", methods=["GET"])
def healthcheck():
    return jsonify({"status": "ok", "service": "ITCorner.id Secure E-Commerce"}), 200

if __name__ == '__main__':
    app.run(debug=False)