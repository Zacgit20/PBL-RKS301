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
from app.extensions import db, migrate, csrf
from app.routes import register_blueprints
from sqlalchemy.engine import URL
from app.models import User, Product, Payment, Order, OrderItem
from decimal import Decimal, InvalidOperation
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

# Konfigurasi upload gambar produk
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # Maksimal 2 MB

app.config["PRODUCT_UPLOAD_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "uploads",
    "products"
)

os.makedirs(app.config["PRODUCT_UPLOAD_FOLDER"], exist_ok=True)

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

db.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)
register_blueprints(app)

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



# Endpoint wajib untuk pengecekan kesehatan server oleh CI/CD (healthcheck.sh)

if __name__ == '__main__':
    app.run(debug=False)