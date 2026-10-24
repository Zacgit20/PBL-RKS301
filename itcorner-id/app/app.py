import sys
import os
import logging


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from dummy_db import products_db, users_db, payments_db, format_rupiah, get_current_date_indo

app = Flask(__name__)
app.secret_key = 'FLASK_SECRET_KEY_itcorner-id-secret-demo-2026'

# ==========================================
# KONFIGURASI LOGGING (MODUL 8 / OWASP A09)
# ==========================================
logging.basicConfig(
    filename='app_activity.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# log_werkzeug = logging.getLogger('werkzeug')
# log_werkzeug.setLevel(logging.ERROR)


# ==========================================
# RUTE CLIENT / USER
# ==========================================
@app.route('/')
@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 1. Ambil kata kunci pencarian ('q') dan kategori ('category') dari URLexit
    search_query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', 'all').strip()
    
    filtered_db = products_db
    
    # 2. Filter Berdasarkan Kata Kunci Pencarian
    if search_query:
        filtered_db = [
            p for p in filtered_db
            if search_query.lower() in p['name'].lower() or 
               search_query.lower() in p.get('description', '').lower() or
               search_query.lower() in p.get('category', '').lower()
        ]
        
    # 3. Filter Berdasarkan Kategori
    if selected_category and selected_category.lower() != 'all':
        filtered_db = [
            p for p in filtered_db
            if p.get('category', '').lower() == selected_category.lower()
        ]
        
    # 4. Format harga produk DARI HASIL FILTER (filtered_db), bukan products_db
    formatted_products = []
    for p in filtered_db:
        p_copy = p.copy()
        p_copy['price'] = format_rupiah(p['price_num'])
        formatted_products.append(p_copy)
        
    # 5. Kirim data dan status filter ke index.html
    return render_template('index.html', 
                           products=formatted_products, 
                           search_query=search_query,
                           selected_category=selected_category)

@app.route('/login', methods=['GET', 'POST'])
def login():
    email_error = None
    password_error = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        if not email: 
            email_error = "Email wajib diisi."
        if not password:
            password_error = "Password wajib diisi."
        elif len(password) < 8:
            password_error = "Password minimal 8 karakter."
    
        if email and password and len(password) >= 8:
            user = next((u for u in users_db if u['email'] == email), None)

            if not user:
                email_error = "Email belum terdaftar."
                logging.warning(f"LOGIN FAILED: Email '{email}' tidak ditemukan dari IP {request.remote_addr}")
            elif user.get('password') != password:
                password_error = "Kata sandi salah."
                logging.warning(f"LOGIN FAILED: Password salah untuk email '{email}' dari IP {request.remote_addr}")
            else:
                session['user_id'] = user['id']
                session['email'] = user['email']
                session['user_name'] = user['name']
                session['role'] = user['role']
                
                logging.info(f"LOGIN SUCCESS: User '{email}' ({user['role']}) berhasil login dari IP {request.remote_addr}")
                
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
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
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
        # 7. Cek Duplikasi Email (Sangat Penting!)
        existing_user = next((u for u in users_db if u['email'].lower() == email), None)
        if existing_user:
            form_error = "Email sudah terdaftar. Silakan gunakan email lain atau login."
            logging.warning(f"REGISTER FAILED: Email '{email}' sudah terdaftar dari IP {request.remote_addr}")
            return render_template('register.html', form_error=form_error)
        # 8. Simpan ke Database Dummy
        new_user = {
            "id": len(users_db) + 1,
            "name": fullname,
            "email": email,
            "phone": phone,
            "password": password,
            "role": "Pelanggan",
            "joined": get_current_date_indo(),
            "status": "Aktif"
        }
        users_db.append(new_user)

        # # 9. HASH PASSWORD DI SINI SEBELUM DISIMPAN KE DATABASE DUMMY
        # hashed_password = generate_password_hash(password)  # <-- Bikin hash di sini

        # new_user = {
        #     "id": len(users_db) + 1,
        #     "name": fullname,
        #     "email": email,
        #     "phone": phone,
        #     "password": hashed_password,  # <-- Simpan password yang sudah di-hash
        #     "role": "Pelanggan",
        #     "joined": get_current_date_indo(),
        #     "status": "Aktif"
        # }
        # users_db.append(new_user)

        # 10. Log Register Berhasil
        logging.info(f"REGISTER SUCCESS: User '{email}' ({fullname}) berhasil mendaftar dari IP {request.remote_addr}")
        return redirect(url_for('login'))

    return render_template('register.html', form_error=form_error)

@app.route('/detail/<int:product_id>')
def detail(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Cari produk berdasarkan ID
    product = next((p for p in products_db if p['id'] == product_id), None)
    if not product:
        return redirect(url_for('home'))

    # Format harga ke Rupiah
    product_data = product.copy()
    product_data['price'] = format_rupiah(product['price_num'])

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
        logging.warning(f"UNAUTHORIZED ACCESS: Percobaan akses admin tanpa izin dari IP {request.remote_addr}")
        return redirect(url_for('login'))
    current_date = get_current_date_indo()

    total_omzet = sum(p['amount_num'] for p in payments_db if p['status'] == 'Disetujui')

    status_counts = {
        "menunggu_bayar": len([p for p in payments_db if p['status'] == 'Menunggu Approval']),
        "disetujui": len([p for p in payments_db if p['status'] == 'Disetujui']),
        "ditolak": len([p for p in payments_db if p['status'] == 'Ditolak'])
    }

    stats = {
        "total_penjualan": format_rupiah(total_omzet),
        "pesanan_baru": status_counts["menunggu_bayar"],
        "total_produk": len(products_db),
        "total_user": len(users_db)
    }

    formatted_products = []
    for p in products_db:
        p_copy = p.copy()
        p_copy['price'] = format_rupiah(p['price_num'])
        formatted_products.append(p_copy)

    return render_template('admin/dashboard.html', stats=stats, products=formatted_products, status_counts=status_counts, current_date=current_date)

@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    formatted_products = []
    for p in products_db:
        p_copy = p.copy()
        p_copy['price'] = format_rupiah(p['price_num'])
        formatted_products.append(p_copy)

    edit_id = request.args.get('edit', type=int)
    selected_product = next((p for p in products_db if p['id'] == edit_id), None)

    return render_template(
        'admin/products.html', 
        products=formatted_products, 
        selected_product=selected_product
    )

@app.route('/admin/product/save', methods=['POST'])
def save_product():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    product_id = request.form.get('product_id')
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    brand = request.form.get('brand', '').strip()

    price_raw = request.form.get('price', '0').replace('.', '').replace('Rp', '').strip()
    price_num = int(price_raw) if price_raw.isdigit() else 0
    stock_raw = str(request.form.get('stock', '0')).strip()
    stock = int(stock_raw) if stock_raw.isdigit() else 0
    description = request.form.get('description', '').strip()

    if not name:
        return redirect(url_for('admin_products'))

    if product_id:
        p_id = int(product_id)
        product = next((p for p in products_db if p['id'] == p_id), None)
        if product:
            product['name'] = name
            product['category'] = category
            product['brand'] = brand
            product['price_num'] = price_num
            product['stock'] = stock
            product['description'] = description
            logging.info(f"PRODUCT UPDATED: Admin '{session.get('user_name')}' memperbarui produk '{name}' (ID: {p_id})")
    else:
        new_id = max([p['id'] for p in products_db], default=0) + 1
        products_db.append({
            "id": new_id,
            "sku": f"PROD-{new_id:03d}",
            "name": name,
            "category": category,
            "brand": brand,
            "price_num": price_num,
            "stock": stock,
            "description": description
        })
        logging.info(f"PRODUCT ADDED: Admin '{session.get('user_name')}' menambahkan produk '{name}' (ID: {new_id})")

    return redirect(url_for('admin_products'))

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    global products_db
    product = next((p for p in products_db if p['id'] == product_id), None)

    if product:
        products_db = [p for p in products_db if p['id'] != product_id]
        logging.info(f"PRODUCT DELETED: Admin '{session.get('user_name')}' menghapus produk '{product['name']}' (ID: {product_id})")

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

if __name__ == '__main__':
    app.run(debug=True)