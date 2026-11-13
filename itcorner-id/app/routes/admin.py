
import logging

import os
import uuid
from decimal import Decimal, InvalidOperation
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError


from datetime import date, timedelta

from flask import (
    current_app,
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from sqlalchemy import func, case, or_

from app.extensions import db
from app.models import Payment, Product, User, Order, OrderItem
from app.utils import format_rupiah, get_current_date_indo


admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@admin_bp.route('/admin/dashboard')
def admin_dashboard():

    # =========================
    # AUTHORIZATION
    # =========================

    if session.get('role') != 'Admin':
        logging.warning(
            "UNAUTHORIZED ACCESS: Percobaan akses admin tanpa izin dari IP %s",
            request.remote_addr
        )
        return redirect(url_for('auth.login'))

    try:
        current_date = get_current_date_indo()

        # =========================
        # PAYMENT STATISTICS
        # =========================

        payment_stats = db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (Payment.status == 'Disetujui', Payment.amount_num),
                        else_=0
                    )
                ),
                0
            ).label('total_omzet'),

            func.count(
                case(
                    (Payment.status == 'Menunggu Approval', 1)
                )
            ).label('menunggu_bayar'),

            func.count(
                case(
                    (Payment.status == 'Disetujui', 1)
                )
            ).label('disetujui'),

            func.count(
                case(
                    (Payment.status == 'Ditolak', 1)
                )
            ).label('ditolak')

        ).one()

        # =========================
        # PRODUCT AND USER TOTAL
        # =========================

        total_products = db.session.query(
            func.count(Product.id)
        ).scalar() or 0

        total_users = db.session.query(
            func.count(User.id)
        ).scalar() or 0

        # =========================
        # DAILY REVENUE
        # =========================

        start_date = date.today() - timedelta(days=6)
        end_date = date.today() + timedelta(days=1)

        daily_revenue = db.session.query(
            func.date(Payment.payment_date).label('tanggal'),
            func.sum(Payment.amount_num).label('omzet')
        ).filter(
            Payment.status == 'Disetujui',
            Payment.payment_date >= start_date,
            Payment.payment_date < end_date
        ).group_by(
            func.date(Payment.payment_date)
        ).order_by(
            func.date(Payment.payment_date)
        ).all()

        revenue_by_date = {
            row.tanggal: row.omzet
            for row in daily_revenue
        }

        chart_data = []

        for i in range(6, -1, -1):
            chart_date = date.today() - timedelta(days=i)
            omzet = revenue_by_date.get(chart_date, 0)

            chart_data.append({
                'tanggal': chart_date,
                'label': chart_date.strftime('%d/%m'),
                'omzet': float(omzet)
            })

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

        # =========================
        # ORDER STATISTICS
        # =========================

        order_stats = db.session.query(
            func.count(
                case(
                    (Order.status == 'Menunggu Pembayaran', 1)
                )
            ).label('menunggu_bayar'),

            func.count(
                case(
                    (Order.status == 'Diproses', 1)
                )
            ).label('diproses'),

            func.count(
                case(
                    (Order.status == 'Dikirim', 1)
                )
            ).label('dikirim'),

            func.count(
                case(
                    (Order.status == 'Selesai', 1)
                )
            ).label('selesai')

        ).one()

        status_counts = {
            'menunggu_bayar': payment_stats.menunggu_bayar,
            'disetujui': payment_stats.disetujui,
            'ditolak': payment_stats.ditolak,
            'diproses': order_stats.diproses,
            'dikirim': order_stats.dikirim,
            'selesai': order_stats.selesai
        }

        # =========================
        # DASHBOARD SUMMARY
        # =========================

        stats = {
            'total_penjualan': format_rupiah(
                payment_stats.total_omzet
            ),
            'pesanan_baru': status_counts['menunggu_bayar'],
            'total_produk': total_products,
            'total_user': total_users
        }

        # =========================
        # LATEST PRODUCTS
        # =========================

        latest_products = Product.query.order_by(
            Product.id.asc()
        ).limit(5).all()

        formatted_products = []

        for product in latest_products:
            product_copy = {
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
                'is_active': product.is_active,
                'image': product.image,
                'specs': product.specs
            }

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

        db.session.rollback()

        flash(
            "Gagal mengambil data dashboard.",
            "error"
        )

        return redirect(url_for('auth.login'))


# --- CRUD PRODUK ORM (dipindahkan dari app.py) ---

def process_product_image(file):
    if not file or not file.filename:
        return None

    try:
        # Membaca file gambar
        image_data = file.read()

        if not image_data:
            raise ValueError("File gambar kosong.")

        # Memeriksa format gambar sebenarnya
        image = Image.open(BytesIO(image_data))
        image.verify()

        # Membuka ulang untuk pemrosesan
        image = Image.open(BytesIO(image_data))

        allowed_formats = {
            "JPEG": "jpg",
            "PNG": "png",
            "WEBP": "webp"
        }

        if image.format not in allowed_formats:
            raise ValueError("Format gambar harus JPG, PNG, atau WebP.")

        # Mencegah gambar berdimensi berlebihan
        if image.width > 4000 or image.height > 4000:
            raise ValueError("Dimensi gambar maksimal 4000 x 4000 piksel.")

        # Memperbaiki orientasi gambar
        image = ImageOps.exif_transpose(image)

        # Mengubah ke RGB agar metadata dan konten tidak ikut terbawa
        image = image.convert("RGB")

        # Nama file acak
        filename = f"{uuid.uuid4().hex}.jpg"

        upload_path = os.path.join(
            current_app.config["PRODUCT_UPLOAD_FOLDER"],
            filename
        )

        # Menyimpan ulang sebagai JPEG
        image.save(upload_path, format="JPEG", quality=85, optimize=True)

        return f"uploads/products/{filename}"

    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ValueError(f"Gambar tidak valid: {error}")

@admin_bp.route('/admin/products', methods=['GET'])
def admin_products():
    if 'role' not in session or session['role'] != 'Admin':
        logging.warning(
            "UNAUTHORIZED ACCESS: User '%s' mencoba mengakses halaman produk admin",
            session.get('email', 'Unknown')
        )
        return redirect(url_for('auth.login'))

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
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/product/save', methods=['POST'])
def save_product():
    # 1. Memeriksa hak akses Admin
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('auth.login'))

    # 2. Mengambil data dari form
    product_id = request.form.get('product_id', '').strip()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    brand = request.form.get('brand', '').strip()
    description = request.form.get('description', '').strip()

    # 3. Validasi nama produk
    if not name:
        flash('Nama produk wajib diisi.', 'danger')
        return redirect(url_for('admin.admin_products'))

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
        return redirect(url_for('admin.admin_products'))

    # 6. Mengambil dan memvalidasi stok
    stock_raw = request.form.get('stock', '').strip()

    if not stock_raw.isdigit():
        flash('Stok harus berupa bilangan bulat nonnegatif.', 'danger')
        return redirect(url_for('admin.admin_products'))

    stock = int(stock_raw)

    # Memproses upload gambar produk
    image_file = request.files.get("image")
    image_path = None

    if image_file and image_file.filename:
        try:
            image_path = process_product_image(image_file)

        except ValueError as error:
            flash(str(error), "danger")
            return redirect(url_for("admin_products"))

    # 7. UPDATE PRODUK (menggunakan PostgreSQL)
    if product_id:
        try:
            p_id = int(product_id)

            # Mencari produk berdasarkan ID di PostgreSQL
            product = db.session.get(Product, p_id)

            if not product:
                flash('Produk tidak ditemukan.', 'danger')
                return redirect(url_for('admin.admin_products'))

            # Memperbarui data produk
            product.name = name
            product.category = category or None
            product.brand = brand or None
            product.price_num = price_num
            product.stock = stock
            product.description = description or None

            if image_path:
                product.image = image_path

            # Menyimpan perubahan ke database
            db.session.commit()

            logging.info(
                f"PRODUCT UPDATED: Admin '{session.get('user_name')}' "
                f"memperbarui produk '{name}' (ID: {p_id})"
            )

            flash('Produk berhasil diperbarui.', 'success')

            return redirect(
                url_for('admin.admin_products', edit=p_id) + '#form-produk'
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
            image=image_path,
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

    return redirect(url_for('admin.admin_products'))

@admin_bp.route('/admin/product/toggle/<int:product_id>', methods=['POST'])
def toggle_product_status(product_id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('auth.login'))

    try:
        product = db.session.get(Product, product_id)

        if not product:
            flash("Produk tidak ditemukan.", "error")
            return redirect(url_for('admin.admin_products'))

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

    return redirect(url_for('admin.admin_products'))

@admin_bp.route('/admin/product/permanently-delete/<int:product_id>', methods=['POST'])
def permanently_delete_product(product_id):
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('auth.login'))

    try:
        product = db.session.get(Product, product_id)

        if not product:
            flash("Produk tidak ditemukan.", "error")
            return redirect(url_for('admin.admin_products'))

        # Periksa apakah produk pernah digunakan dalam pesanan
        order_item = OrderItem.query.filter_by(
            product_id=product_id
        ).first()

        if order_item:
            flash(
                "Produk tidak dapat dihapus karena memiliki riwayat pesanan.",
                "error"
            )
            return redirect(url_for('admin.admin_products'))

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

    return redirect(url_for('admin.admin_products'))


# --- MANAJEMEN PENGGUNA DAN PEMBAYARAN ORM ---

def _active_admin():
    """Validasi admin berdasarkan data terbaru di PostgreSQL."""
    user_id = session.get("user_id")
    if not user_id:
        return None

    admin_user = db.session.get(User, user_id)

    if (
        not admin_user
        or admin_user.role != "Admin"
        or admin_user.status != "Aktif"
    ):
        return None

    return admin_user


@admin_bp.route('/admin/users', methods=['GET'])
def admin_users():
    if not _active_admin():
        flash("Akses admin ditolak. Silakan login kembali.", "error")
        return redirect(url_for('auth.login'))

    q = request.args.get('q', '').strip()
    role_filter = request.args.get('role', 'all')
    status_filter = request.args.get('status', 'all')
    edit_id = request.args.get('edit', type=int)

    stats = {
        'total': User.query.count(),
        'pelanggan_aktif': User.query.filter_by(
            role='Pelanggan', status='Aktif'
        ).count(),
        'admin': User.query.filter_by(role='Admin').count(),
        'nonaktif': User.query.filter_by(status='Nonaktif').count()
    }

    query = User.query

    if q:
        query = query.filter(
            or_(
                User.name.ilike(f'%{q}%'),
                User.email.ilike(f'%{q}%')
            )
        )

    if role_filter in ('Pelanggan', 'Admin'):
        query = query.filter_by(role=role_filter)
    else:
        role_filter = 'all'

    if status_filter in ('Aktif', 'Nonaktif'):
        query = query.filter_by(status=status_filter)
    else:
        status_filter = 'all'

    users = query.order_by(User.id.desc()).all()
    selected_user = db.session.get(User, edit_id) if edit_id else None

    return render_template(
        'admin/users.html',
        stats=stats,
        users=users,
        selected_user=selected_user,
        search_query=q,
        role_filter=role_filter,
        status_filter=status_filter
    )


@admin_bp.route('/admin/users/save', methods=['POST'])
def save_user_settings():
    admin_user = _active_admin()

    if not admin_user:
        flash("Akses admin ditolak. Silakan login kembali.", "error")
        return redirect(url_for('auth.login'))

    user_id = request.form.get('user_id', type=int)
    new_role = request.form.get('role', '').strip()
    new_status = request.form.get('status', '').strip()

    if new_role not in ('Pelanggan', 'Admin'):
        flash("Peran pengguna tidak valid.", "error")
        return redirect(url_for('admin.admin_users'))

    if new_status not in ('Aktif', 'Nonaktif'):
        flash("Status pengguna tidak valid.", "error")
        return redirect(url_for('admin.admin_users'))

    try:
        target_user = db.session.get(User, user_id)

        if not target_user:
            flash("Pengguna tidak ditemukan.", "error")
            return redirect(url_for('admin.admin_users'))

        if target_user.id == admin_user.id and (
            new_role != 'Admin' or new_status != 'Aktif'
        ):
            flash(
                "Anda tidak dapat menurunkan peran atau menonaktifkan akun sendiri.",
                "error"
            )
            return redirect(url_for('admin.admin_users'))

        target_user.role = new_role
        target_user.status = new_status

        db.session.commit()

        logging.info(
            "USER SETTINGS UPDATED: Admin ID %s mengubah pengguna ID %s menjadi role=%s status=%s",
            admin_user.id,
            target_user.id,
            new_role,
            new_status
        )

        flash("Pengaturan akun berhasil disimpan.", "success")

    except Exception:
        db.session.rollback()
        logging.exception("Gagal memperbarui pengaturan pengguna.")
        flash("Gagal menyimpan pengaturan akun.", "error")

    return redirect(url_for('admin.admin_users'))


@admin_bp.route('/admin/payments', methods=['GET'])
def admin_payments():
    if not _active_admin():
        flash("Akses admin ditolak. Silakan login kembali.", "error")
        return redirect(url_for('auth.login'))

    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'Menunggu Approval')
    selected_id = request.args.get('inv', '').strip()

    pending_count = Payment.query.filter_by(
        status='Menunggu Approval'
    ).count()

    query = Payment.query.join(User)

    if q:
        query = query.filter(
            or_(
                Payment.id.ilike(f'%{q}%'),
                Payment.order_id.ilike(f'%{q}%'),
                User.name.ilike(f'%{q}%'),
                User.email.ilike(f'%{q}%')
            )
        )

    allowed_statuses = (
        'Menunggu Approval',
        'Disetujui',
        'Ditolak'
    )

    if status_filter in allowed_statuses:
        query = query.filter(Payment.status == status_filter)
    else:
        status_filter = 'all'

    payment_records = query.order_by(
        Payment.payment_date.desc()
    ).all()

    def payment_view(payment):
        return {
            'id': payment.id,
            'order_id': payment.order_id,
            'user': payment.user.name if payment.user else 'Pengguna tidak ditemukan',
            'amount': format_rupiah(payment.amount_num),
            'status': payment.status,
            'method': payment.method,
            'date': (
                payment.payment_date.strftime('%d-%m-%Y %H:%M')
                if payment.payment_date else '-'
            )
        }

    payments = [payment_view(p) for p in payment_records]

    selected_record = next(
        (p for p in payment_records if p.id == selected_id),
        None
    )

    if not selected_record and payment_records:
        selected_record = payment_records[0]

    selected_payment = (
        payment_view(selected_record) if selected_record else None
    )

    return render_template(
        'admin/payments.html',
        payments=payments,
        selected_payment=selected_payment,
        pending_count=pending_count,
        search_query=q,
        status_filter=status_filter
    )


@admin_bp.route('/admin/payments/action', methods=['POST'])
def process_payment_action():
    admin_user = _active_admin()

    if not admin_user:
        flash("Akses admin ditolak. Silakan login kembali.", "error")
        return redirect(url_for('auth.login'))

    payment_id = request.form.get('payment_id', '').strip()
    action = request.form.get('action', '').strip()
    reason = request.form.get('reason', '').strip()

    if action not in ('approve', 'reject'):
        flash("Aksi pembayaran tidak valid.", "error")
        return redirect(url_for('admin.admin_payments'))

    if action == 'reject' and not reason:
        flash("Alasan penolakan wajib diisi.", "error")
        return redirect(url_for('admin.admin_payments', inv=payment_id))

    if len(reason) > 500:
        flash("Alasan penolakan maksimal 500 karakter.", "error")
        return redirect(url_for('admin.admin_payments', inv=payment_id))

    try:
        payment = Payment.query.filter_by(
            id=payment_id
        ).with_for_update().first()

        if not payment:
            flash("Pembayaran tidak ditemukan.", "error")
            return redirect(url_for('admin.admin_payments'))

        if payment.status != 'Menunggu Approval':
            flash("Pembayaran ini sudah pernah diproses.", "warning")
            return redirect(
                url_for('admin.admin_payments', inv=payment_id)
            )

        if action == 'approve':
            payment.status = 'Disetujui'
            log_action = 'APPROVED'
            flash("Pembayaran berhasil disetujui.", "success")
        else:
            payment.status = 'Ditolak'
            log_action = 'REJECTED'
            logging.warning(
                "PAYMENT REJECTION REASON: Payment %s, Admin ID %s, Reason: %s",
                payment_id,
                admin_user.id,
                reason
            )
            flash("Pembayaran berhasil ditolak.", "success")

        db.session.commit()

        logging.info(
            "PAYMENT %s: Admin ID %s memproses pembayaran %s",
            log_action,
            admin_user.id,
            payment_id
        )

    except Exception:
        db.session.rollback()
        logging.exception(
            "Gagal memproses pembayaran ID %s",
            payment_id
        )
        flash("Gagal memproses pembayaran.", "error")

    return redirect(
        url_for('admin.admin_payments', inv=payment_id)
    )


@admin_bp.before_request
def protect_admin_routes():
    """Lindungi seluruh endpoint Admin berdasarkan data PostgreSQL."""
    if not _active_admin():
        logging.warning(
            "ADMIN ACCESS DENIED: user_id=%s, IP=%s, endpoint=%s",
            session.get("user_id"),
            request.remote_addr,
            request.endpoint
        )
        flash("Akses Admin ditolak. Silakan login dengan akun Admin aktif.", "error")
        return redirect(url_for("auth.login"))
