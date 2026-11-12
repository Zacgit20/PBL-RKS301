import sys
from pathlib import Path

# Menambahkan direktori utama proyek ke Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from getpass import getpass
from sqlalchemy import func
from app.app import app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    name = input("Nama Admin: ").strip()
    email = input("Email Admin: ").strip().lower()
    password = getpass("Password Admin: ")
    confirm = getpass("Ulangi Password: ")

    if not name or not email:
        raise SystemExit("Nama dan email wajib diisi.")

    if len(password) < 12:
        raise SystemExit("Password minimal 12 karakter.")

    if password != confirm:
        raise SystemExit("Password tidak cocok.")

    existing = User.query.filter(
        func.lower(User.email) == email
    ).first()

    if existing:
        raise SystemExit("Email sudah terdaftar.")

    admin = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role="Admin",
        status="Aktif"
    )

    try:
        db.session.add(admin)
        db.session.commit()

        app.logger.info(
            "ADMIN ACCOUNT CREATED: ID=%s, email=%s",
            admin.id,
            admin.email
        )

        print("Akun Admin berhasil dibuat.")
        print("ID:", admin.id)
        print("Email:", admin.email)
        print("Role:", admin.role)

    except Exception:
        db.session.rollback()
        app.logger.exception("Gagal membuat akun Admin")
        raise
