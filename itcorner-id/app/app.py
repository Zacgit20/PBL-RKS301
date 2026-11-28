import sys
import os
import logging
import uuid
from dotenv import load_dotenv
# Membaca konfigurasi dari file .env
load_dotenv()

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from app.extensions import db, migrate, csrf, limiter, mail
from app.routes import register_blueprints
from sqlalchemy.engine import URL
from app.models import User, Product, Payment, Order, OrderItem, ProductReview
from decimal import Decimal, InvalidOperation
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError

app = Flask(__name__)

# Mempercayai satu reverse proxy (Nginx)
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=0,
    x_port=0,
    x_prefix=0
)

app.secret_key = os.environ["FLASK_SECRET_KEY"]

# Keamanan cookie sesi
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = (
    os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Konfigurasi upload gambar produk
# Maksimal request 2,5 MB: file 2 MB + ruang overhead multipart.
app.config["MAX_CONTENT_LENGTH"] = (2 * 1024 * 1024) + (512 * 1024)

app.config["PRODUCT_UPLOAD_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "uploads",
    "products"
)

os.makedirs(app.config["PRODUCT_UPLOAD_FOLDER"], exist_ok=True)

# Penyimpanan privat bukti pembayaran (tidak berada di static).
app.config["PAYMENT_PROOF_UPLOAD_FOLDER"] = os.path.join(
    os.path.dirname(app.root_path),
    "private_uploads",
    "payment_proofs"
)
os.makedirs(app.config["PAYMENT_PROOF_UPLOAD_FOLDER"], exist_ok=True)

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
            app.config["PRODUCT_UPLOAD_FOLDER"],
            filename
        )

        # Menyimpan ulang sebagai JPEG
        image.save(upload_path, format="JPEG", quality=85, optimize=True)

        return f"uploads/products/{filename}"

    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ValueError(f"Gambar tidak valid: {error}")


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

# ==========================================
# KONFIGURASI EMAIL (BREVO SMTP)
# ==========================================
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")


db.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)
mail.init_app(app)

# Konfigurasi Flask-Limiter menggunakan Redis
redis_password = os.environ["REDIS_PASSWORD"]
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = os.getenv("REDIS_PORT", "6379")

app.config["RATELIMIT_STORAGE_URI"] = (
    f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
)

# Aktifkan header informasi rate limit
app.config["RATELIMIT_HEADERS_ENABLED"] = True

limiter.init_app(app)

register_blueprints(app)

# ==========================================
# KONFIGURASI LOGGING (MODUL 8 / OWASP A09)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

log_werkzeug = logging.getLogger('werkzeug')
log_werkzeug.setLevel(logging.ERROR)



# Endpoint wajib untuk pengecekan kesehatan server oleh CI/CD (healthcheck.sh)

if __name__ == '__main__':
    app.run(debug=False)