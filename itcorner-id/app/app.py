import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for
from dummy_db import products_db, users_db, payments_db, format_rupiah, get_current_date_indo

app = Flask(__name__)
app.secret_key = 'itcorner_secret_key_bebas_diisi_bebas'

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
        
    formatted_products = []
    for p in products_db:
        p_copy = p.copy()
        p_copy['price'] = format_rupiah(p['price_num'])
        formatted_products.append(p_copy)
    return render_template('index.html', products=formatted_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    email_error = None
    password_error = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
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
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        terms = request.form.get('terms')

        if not fullname or not email or not phone or not password or not confirm_password:
            form_error = "Harap isi semua kolom pendaftaran terlebih dahulu."
            return render_template('register.html', form_error=form_error)

        if password != confirm_password:
            form_error = "Konfirmasi kata sandi tidak cocok."
            return render_template('register.html', form_error=form_error)
            
        if not terms:
            form_error = "Anda harus menyetujui Syarat & Ketentuan terlebih dahulu."
            return render_template('register.html', form_error=form_error)

        users_db.append({
            "id": len(users_db) + 1,
            "name": fullname,
            "email": email,
            "role": "Pelanggan",
            "joined": "18 Okt 2026",
            "status": "Aktif"
        })
        return redirect(url_for('login'))

    return render_template('register.html', form_error=form_error)

@app.route('/detail')
def detail():
    return render_template('detail.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int) or 1
        qty = request.form.get('quantity', type=int) or 1
        payment_method = request.form.get('payment_method') or "Transfer BCA"

        total_amount = 0
        for p in products_db:
            if p['id'] == product_id:
                if p['stock'] >= qty:
                    p['stock'] -= qty
                total_amount = p['price_num'] * qty
                break

        inv_id = f"INV-20261018-0{len(payments_db) + 1}"
        payments_db.append({
            "id": inv_id,
            "user": session.get('user_name', 'Pelanggan'),
            "amount_num": total_amount,
            "amount": format_rupiah(total_amount),
            "method": payment_method,
            "date": "18 Okt 2026",
            "status": "Menunggu Approval"
        })

        return redirect(url_for('orders'))

    return render_template('checkout.html')

@app.route('/orders')
def orders():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('orders.html', payments=payments_db)

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/forgot_password')
def forgot_password():
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

    total_omzet = sum(p['amount_num'] for p in payments_db if p['status'] == 'Disetujui')

    status_counts = {
        "menunggu_bayar": len([p for p in payments_db if p['status'] == 'Menunggu Approval']),
        "disetujui": len([p for p in payments_db if p['status'] == 'Disetujui'])
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

    return render_template('admin/dashboard.html', stats=stats, products=formatted_products, status_counts=status_counts)

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
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    return render_template('admin/users.html', users=users_db)

@app.route('/admin/payments')
def admin_payments():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    return render_template('admin/payments.html', payments=payments_db)

@app.route('/admin/payments/approve/<payment_id>')
def approve_payment(payment_id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    for p in payments_db:
        if p['id'] == payment_id:
            p['status'] = 'Disetujui'
            break
    return redirect(url_for('admin_payments'))


if __name__ == '__main__':
    app.run(debug=True)