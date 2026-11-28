
import logging

import os
import uuid
from decimal import Decimal, InvalidOperation
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError


from datetime import date, datetime, timedelta, timezone

from flask import (
    current_app,
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request,
    abort,
    send_file
)

from sqlalchemy import func, case, or_

from app.extensions import db
from app.models import (
    Payment,
    PaymentProof,
    Product,
    ProductSpecification,
    User,
    Order,
    OrderItem,
    ActivationRequest
)
from app.utils import format_rupiah, get_current_date_indo


admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@admin_bp.route('/admin/dashboard')
def admin_dashboard():

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
        # Membaca dan membatasi ukuran file gambar.
        image_data = file.read()

        if not image_data:
            raise ValueError("File gambar kosong.")

        if len(image_data) > 2 * 1024 * 1024:
            raise ValueError("Ukuran gambar maksimal 2 MB.")

        # Periksa dimensi sebelum proses decoding penuh.
        image = Image.open(BytesIO(image_data))

        if image.width * image.height > 16_000_000:
            raise ValueError("Jumlah piksel gambar maksimal 16 juta.")

        # Verifikasi isi file, bukan hanya ekstensi.
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

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError
    ) as error:
        raise ValueError(
            "Gambar tidak valid atau dimensinya terlalu besar."
        ) from error

@admin_bp.route('/admin/products', methods=['GET'])
def admin_products():
    try:
        search_query = request.args.get('q', '').strip()[:100]
        selected_category = request.args.get('category', 'all')
        selected_stock = request.args.get('stock', 'all')

        allowed_categories = {
            'Laptop', 'Aksessori', 'Monitor', 'Komponen', 'Audio'
        }
        allowed_stock = {'all', 'available', 'low', 'empty'}

        if selected_category not in allowed_categories:
            selected_category = 'all'

        if selected_stock not in allowed_stock:
            selected_stock = 'all'

        query = Product.query

        # Pencarian nama produk atau SKU
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.sku.ilike(search_pattern)
                )
            )

        # Filter kategori
        if selected_category != 'all':
            query = query.filter(Product.category == selected_category)

        # Filter kondisi stok
        if selected_stock == 'available':
            query = query.filter(Product.stock > 5)
        elif selected_stock == 'low':
            query = query.filter(Product.stock.between(1, 5))
        elif selected_stock == 'empty':
            query = query.filter(Product.stock == 0)

        # Produk terbaru atau terakhir diedit berada di atas
        products_db_list = query.order_by(
            Product.updated_at.desc(),
            Product.id.desc()
        ).all()


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
            selected_product=selected_product,
            search_query=search_query,
            selected_category=selected_category,
            selected_stock=selected_stock
        )

    except Exception:
        logging.exception("ERROR: Gagal mengambil daftar produk dari database")
        flash("Terjadi kesalahan saat mengambil data produk.", "error")
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/product/save', methods=['POST'])
def save_product():
    # 1. Memeriksa hak akses dan status Admin di PostgreSQL
    if not _active_admin():
        flash('Akses ditolak. Silakan login sebagai Admin aktif.', 'danger')
        return redirect(url_for('auth.login'))

    # 2. Mengambil data dari form
    product_id = request.form.get('product_id', '').strip()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    brand = request.form.get('brand', '').strip()
    description = request.form.get('description', '').strip()
    specs = request.form.get('specs', '').strip()

    # Mengambil atribut spesifikasi dari form dinamis
    attribute_names = request.form.getlist('attribute_name[]')
    attribute_values = request.form.getlist('attribute_value[]')

    if len(attribute_names) > 30 or len(attribute_values) > 30:
        flash('Maksimal 30 atribut spesifikasi.', 'danger')
        return redirect(url_for('admin.admin_products'))

    if len(attribute_names) != len(attribute_values):
        flash('Data atribut spesifikasi tidak valid.', 'danger')
        return redirect(url_for('admin.admin_products'))

    specifications = []
    used_names = set()

    for attribute_name, attribute_value in zip(
        attribute_names, attribute_values
    ):
        attribute_name = attribute_name.strip()
        attribute_value = attribute_value.strip()

        if not attribute_name and not attribute_value:
            continue

        if not attribute_name or not attribute_value:
            flash(
                'Nama dan nilai setiap atribut harus diisi.',
                'danger'
            )
            return redirect(url_for('admin.admin_products'))

        if len(attribute_name) > 80:
            flash('Nama atribut maksimal 80 karakter.', 'danger')
            return redirect(url_for('admin.admin_products'))

        if len(attribute_value) > 300:
            flash('Nilai atribut maksimal 300 karakter.', 'danger')
            return redirect(url_for('admin.admin_products'))

        normalized_name = attribute_name.casefold()

        if normalized_name in used_names:
            flash('Nama atribut tidak boleh duplikat.', 'danger')
            return redirect(url_for('admin.admin_products'))

        used_names.add(normalized_name)

        specifications.append({
            'attribute_name': attribute_name,
            'attribute_value': attribute_value
        })

    # 3. Validasi panjang spesifikasi
    if len(specs) > 5000:
        flash('Spesifikasi maksimal 5.000 karakter.', 'danger')
        return redirect(url_for('admin.admin_products'))

    # 4. Validasi nama produk
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
            # Pertahankan spesifikasi teks lama jika field legacy tidak dikirim.
            if 'specs' in request.form:
                product.specs = specs or None

            # Mengganti atribut lama dengan atribut terbaru
            product.specifications.clear()

            for index, item in enumerate(specifications):
                product.specifications.append(
                    ProductSpecification(
                        attribute_name=item['attribute_name'],
                        attribute_value=item['attribute_value'],
                        sort_order=index
                    )
                )

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
            specs=specs or None,
            image=image_path,
            is_promo=False
        )

        try:
            db.session.add(new_product)
            db.session.flush()

            # Menyimpan atribut spesifikasi produk baru
            for index, item in enumerate(specifications):
                db.session.add(
                    ProductSpecification(
                        product_id=new_product.id,
                        attribute_name=item['attribute_name'],
                        attribute_value=item['attribute_value'],
                        sort_order=index
                    )
                )

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

        # Lindungi agar selalu ada minimal satu Admin aktif.
        if (
            target_user.role == 'Admin'
            and target_user.status == 'Aktif'
            and (new_role != 'Admin' or new_status != 'Aktif')
        ):
            active_admins = (
                User.query
                .filter_by(role='Admin', status='Aktif')
                .order_by(User.id.asc())
                .with_for_update()
                .all()
            )

            if len(active_admins) <= 1:
                db.session.rollback()
                flash(
                    "Tidak dapat menonaktifkan atau menurunkan peran "
                    "Admin terakhir yang masih aktif.",
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


@admin_bp.route('/admin/payments/proof/<int:proof_id>')
def admin_payment_proof_image(proof_id):
    """Tampilkan bukti pembayaran hanya kepada admin aktif."""

    admin_user = _active_admin()
    if not admin_user:
        abort(403)

    proof = PaymentProof.query.filter_by(
        id=proof_id
    ).first_or_404()

    # Nama file dibatasi ke basename agar tidak bisa membaca file di luar folder.
    filename = os.path.basename(proof.filename)
    file_path = os.path.join(
        current_app.config["PAYMENT_PROOF_UPLOAD_FOLDER"],
        filename
    )

    if not os.path.isfile(file_path):
        abort(404)

    return send_file(
        file_path,
        mimetype="image/jpeg",
        as_attachment=False,
        download_name="bukti-pembayaran.jpg"
    )


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
        latest_proof = (
            PaymentProof.query
            .filter_by(payment_id=payment.id)
            .order_by(
                PaymentProof.uploaded_at.desc(),
                PaymentProof.id.desc()
            )
            .first()
        )

        order = payment.order
        invoice_items = []
        subtotal_amount = Decimal("0")

        if order:
            for item in order.items:
                product_name = (
                    item.product.name
                    if item.product else "Produk tidak tersedia"
                )
                quantity = item.quantity or 0
                unit_price = item.price_at_purchase or Decimal("0")
                item_subtotal = unit_price * quantity
                subtotal_amount += item_subtotal

                invoice_items.append({
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit_price': format_rupiah(unit_price),
                    'subtotal': format_rupiah(item_subtotal)
                })

        shipping_fee = order.shipping_fee if order else Decimal("0")
        order_total = order.total_amount if order else Decimal("0")

        amount_matches_order = bool(
            order and payment.amount_num == order_total
        )
        invoice_matches_order = bool(
            order and subtotal_amount + shipping_fee == order_total
        )

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
            ),
            'order_status': order.status if order else '-',
            'invoice_items': invoice_items,
            'subtotal': format_rupiah(subtotal_amount),
            'shipping_fee': format_rupiah(shipping_fee),
            'order_total': format_rupiah(order_total) if order else '-',
            'amount_matches_order': amount_matches_order,
            'invoice_matches_order': invoice_matches_order,
            'proof_id': latest_proof.id if latest_proof else None,
            'proof_status': latest_proof.review_status if latest_proof else None,
            'proof_date': (
                latest_proof.uploaded_at.strftime('%d-%m-%Y %H:%M')
                if latest_proof and latest_proof.uploaded_at else '-'
            ),
            'proof_rejection_reason': (
                latest_proof.rejection_reason if latest_proof else None
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
        payment = (
            Payment.query
            .filter_by(id=payment_id)
            .with_for_update()
            .first()
        )

        if not payment:
            flash("Pembayaran tidak ditemukan.", "error")
            return redirect(url_for('admin.admin_payments'))

        if payment.status != 'Menunggu Approval':
            flash("Pembayaran ini tidak sedang menunggu persetujuan.", "warning")
            return redirect(
                url_for('admin.admin_payments', inv=payment_id)
            )

        # Pastikan pesanan terkait tersedia dan masih menunggu pembayaran.
        order = (
            Order.query
            .filter_by(id=payment.order_id, user_id=payment.user_id)
            .with_for_update()
            .first()
        )

        if not order or order.status != 'Menunggu Pembayaran':
            flash("Status pesanan tidak memungkinkan verifikasi pembayaran.", "warning")
            return redirect(
                url_for('admin.admin_payments', inv=payment_id)
            )

        # Hanya bukti terbaru yang boleh diproses.
        latest_proof = (
            PaymentProof.query
            .filter_by(payment_id=payment.id)
            .order_by(
                PaymentProof.uploaded_at.desc(),
                PaymentProof.id.desc()
            )
            .with_for_update()
            .first()
        )

        if not latest_proof or latest_proof.review_status != 'Menunggu':
            flash("Bukti transfer belum tersedia atau sudah diproses.", "warning")
            return redirect(
                url_for('admin.admin_payments', inv=payment_id)
            )

        # Validasi integritas invoice sebelum pembayaran disetujui.
        if action == 'approve':
            invoice_subtotal = sum(
                (
                    (item.price_at_purchase or Decimal("0")) * item.quantity
                    for item in order.items
                ),
                Decimal("0")
            )
            invoice_total = invoice_subtotal + (
                order.shipping_fee or Decimal("0")
            )

            if (
                payment.amount_num != order.total_amount
                or invoice_total != order.total_amount
            ):
                db.session.rollback()
                flash(
                    "Pembayaran tidak dapat disetujui karena nominal invoice tidak cocok.",
                    "error"
                )
                return redirect(
                    url_for('admin.admin_payments', inv=payment_id)
                )

        if action == 'approve':
            payment.status = 'Disetujui'
            order.status = 'Diproses'

            latest_proof.review_status = 'Disetujui'
            latest_proof.rejection_reason = None

            log_action = 'APPROVED'
            success_message = "Pembayaran disetujui dan pesanan masuk proses."

        else:
            payment.status = 'Ditolak'
            latest_proof.review_status = 'Ditolak'
            latest_proof.rejection_reason = reason

            log_action = 'REJECTED'
            success_message = "Pembayaran ditolak. Customer dapat mengunggah ulang bukti."

        latest_proof.reviewed_at = db.func.now()
        latest_proof.reviewed_by = admin_user.id

        db.session.commit()

        logging.info(
            "PAYMENT %s: Admin ID %s memproses pembayaran %s, bukti ID %s",
            log_action,
            admin_user.id,
            payment_id,
            latest_proof.id
        )

        flash(success_message, "success")

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


# ==========================================
# FR-009: PERSETUJUAN AKTIVASI AKUN
# ==========================================

@admin_bp.route('/admin/activation-requests', methods=['GET'])
def admin_activation_requests():
    if not _active_admin():
        flash("Akses admin ditolak. Silakan login kembali.", "error")
        return redirect(url_for('auth.login'))

    requests_list = ActivationRequest.query.filter_by(
        status='Menunggu Persetujuan'
    ).order_by(
        ActivationRequest.verified_at.asc()
    ).all()

    return render_template(
        'admin/activation_requests.html',
        activation_requests=requests_list
    )


@admin_bp.route(
    '/admin/activation-requests/<int:request_id>/decision',
    methods=['POST']
)
def decide_activation_request(request_id):
    admin_user = _active_admin()

    if not admin_user:
        flash("Akses admin ditolak. Silakan login kembali.", "error")
        return redirect(url_for('auth.login'))

    decision = request.form.get('decision', '').strip()

    if decision not in ('approve', 'reject'):
        flash("Keputusan aktivasi tidak valid.", "error")
        return redirect(url_for('admin.admin_activation_requests'))

    try:
        activation = ActivationRequest.query.filter_by(
            id=request_id,
            status='Menunggu Persetujuan'
        ).with_for_update().first()

        if not activation:
            db.session.rollback()
            flash(
                "Pengajuan tidak ditemukan atau sudah diproses.",
                "error"
            )
            return redirect(url_for('admin.admin_activation_requests'))

        target_user = db.session.get(User, activation.user_id)

        if (
            not target_user
            or target_user.role != 'Pelanggan'
            or target_user.status != 'Nonaktif'
            or activation.verified_at is None
        ):
            db.session.rollback()
            flash(
                "Data akun tidak memenuhi syarat aktivasi.",
                "error"
            )
            return redirect(url_for('admin.admin_activation_requests'))

        activation.reviewed_by = admin_user.id
        activation.reviewed_at = datetime.now(timezone.utc)

        if decision == 'approve':
            target_user.status = 'Aktif'
            activation.status = 'Disetujui'
            activation.rejection_reason = None
            success_message = "Pengajuan aktivasi berhasil disetujui."
        else:
            reason = request.form.get(
                'rejection_reason', ''
            ).strip()

            activation.status = 'Ditolak'
            activation.rejection_reason = (
                reason[:255] if reason else "Tidak ada alasan diberikan."
            )
            # Status akun tetap Nonaktif.
            success_message = "Pengajuan aktivasi berhasil ditolak."

        db.session.commit()

        logging.info(
            "ACTIVATION DECISION: request_id=%s, admin_id=%s, decision=%s",
            activation.id,
            admin_user.id,
            activation.status
        )

        flash(success_message, "success")

    except Exception:
        db.session.rollback()
        logging.exception(
            "ACTIVATION DECISION FAILED: request_id=%s",
            request_id
        )
        flash("Gagal memproses keputusan aktivasi.", "error")

    return redirect(url_for('admin.admin_activation_requests'))


# ==========================================
# FR-010: LAPORAN TRANSAKSI
# ==========================================

def _get_report_period():
    """Validasi periode laporan dari parameter URL."""
    today = date.today()

    start_raw = request.args.get(
        'start_date',
        (today - timedelta(days=29)).isoformat()
    )
    end_raw = request.args.get(
        'end_date',
        today.isoformat()
    )

    try:
        start_date = date.fromisoformat(start_raw)
        end_date = date.fromisoformat(end_raw)
    except (TypeError, ValueError):
        abort(400, description="Format tanggal laporan tidak valid.")

    if start_date > end_date:
        abort(400, description="Tanggal awal tidak boleh melewati tanggal akhir.")

    if (end_date - start_date).days > 366:
        abort(400, description="Rentang laporan maksimal 367 hari.")

    return start_date, end_date


def _get_approved_report_data(start_date, end_date):
    """Ambil pembayaran disetujui dalam rentang tanggal inklusif."""
    start_datetime = datetime.combine(
        start_date,
        datetime.min.time()
    )
    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        datetime.min.time()
    )

    payments = Payment.query.join(
        User,
        Payment.user_id == User.id
    ).filter(
        Payment.status == 'Disetujui',
        Payment.payment_date >= start_datetime,
        Payment.payment_date < end_datetime
    ).order_by(
        Payment.payment_date.desc()
    ).all()

    total_revenue = sum(
        (payment.amount_num or Decimal("0") for payment in payments),
        Decimal("0")
    )

    return payments, total_revenue


@admin_bp.route('/admin/reports', methods=['GET'])
def admin_reports():
    start_date, end_date = _get_report_period()

    payments, total_revenue = _get_approved_report_data(
        start_date,
        end_date
    )

    return render_template(
        'admin/reports.html',
        payments=payments,
        total_revenue=format_rupiah(total_revenue),
        format_rupiah=format_rupiah,
        total_transactions=len(payments),
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )

@admin_bp.route('/admin/reports/export/pdf', methods=['GET'])
def admin_export_report_pdf():
    """Ekspor laporan transaksi disetujui ke PDF."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    start_date, end_date = _get_report_period()
    payments, total_revenue = _get_approved_report_data(start_date, end_date)

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Laporan Transaksi ITCorner.id", styles["Title"]),
        Paragraph(
            f"Periode: {start_date.isoformat()} sampai {end_date.isoformat()}",
            styles["Normal"]
        ),
        Spacer(1, 16)
    ]

    rows = [[
        "ID Pembayaran", "ID Pesanan", "Pelanggan",
        "Metode", "Tanggal", "Nominal"
    ]]

    for payment in payments:
        customer_name = payment.user.name if payment.user else "Tidak tersedia"
        payment_date = (
            payment.payment_date.strftime("%d-%m-%Y %H:%M")
            if payment.payment_date else "-"
        )
        rows.append([
            str(payment.id),
            str(payment.order_id or "-"),
            str(customer_name or "-"),
            str(payment.method or "-"),
            payment_date,
            format_rupiah(payment.amount_num or Decimal("0"))
        ])

    table = Table(
        rows,
        repeatRows=1,
        colWidths=[105, 105, 130, 90, 110, 110]
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white, colors.HexColor("#f1f5f9")
        ]),
        ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f"Total transaksi: {len(payments)} | Total omzet: {format_rupiah(total_revenue)}",
        styles["Heading2"]
    ))

    document.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"laporan-transaksi-{start_date.isoformat()}-sampai-{end_date.isoformat()}.pdf"
    )

def _safe_excel_text(value):
    """Cegah teks tidak tepercaya dieksekusi sebagai formula Excel."""
    text = str(value if value is not None else "")
    check = text.lstrip(" \\t\\r\\n")
    if check.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text



@admin_bp.route('/admin/reports/export/excel', methods=['GET'])
def admin_export_report_excel():
    """Ekspor laporan transaksi disetujui ke Excel."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    start_date, end_date = _get_report_period()
    payments, total_revenue = _get_approved_report_data(start_date, end_date)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Laporan Transaksi"

    sheet.append(["LAPORAN TRANSAKSI ITCORNER.ID"])
    sheet.append([
        "Periode",
        f"{start_date.isoformat()} sampai {end_date.isoformat()}"
    ])
    sheet.append([])
    sheet.append([
        "ID Pembayaran", "ID Pesanan", "Pelanggan",
        "Metode", "Tanggal Pembayaran", "Nominal (Rp)"
    ])

    for cell in sheet[4]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1E293B")
        cell.alignment = Alignment(horizontal="center")

    for payment in payments:
        sheet.append([
            _safe_excel_text(payment.id),
            _safe_excel_text(payment.order_id),
            _safe_excel_text(payment.user.name if payment.user else "Tidak tersedia"),
            _safe_excel_text(payment.method),
            payment.payment_date.strftime("%d-%m-%Y %H:%M")
            if payment.payment_date else "-",
            float(payment.amount_num or Decimal("0"))
        ])

    sheet.append([])
    sheet.append(["Total transaksi", len(payments)])
    sheet.append(["Total omzet (Rp)", float(total_revenue)])

    widths = [22, 22, 28, 20, 24, 20]
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width

    sheet.freeze_panes = "A5"
    sheet.auto_filter.ref = f"A4:F{4 + len(payments)}"

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"laporan-transaksi-{start_date.isoformat()}-sampai-{end_date.isoformat()}.xlsx"
    )

