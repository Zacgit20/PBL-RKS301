
import logging

from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    session,
    url_for
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app.extensions import db
from app.models import User
from app.forms.auth_forms import LoginForm, RegisterForm


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    email_error = None
    password_error = None

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter(
            func.lower(User.email) == email
        ).first()

        if (
            not user
            or not check_password_hash(
                user.password_hash, password
            )
        ):
            email_error = "Email atau kata sandi salah."

            logging.warning(
                "LOGIN FAILED: Kredensial tidak valid "
                "dari IP %s",
                request.remote_addr
            )

        elif user.status != 'Aktif':
            email_error = (
                "Akun tidak aktif. Silakan hubungi admin."
            )

        else:
            session.clear()
            session['user_id'] = user.id
            session['email'] = user.email
            session['user_name'] = user.name
            session['role'] = user.role

            logging.info(
                "LOGIN SUCCESS: User ID %s dengan role %s "
                "berhasil login dari IP %s",
                user.id,
                user.role,
                request.remote_addr
            )

            if user.role == 'Admin':
                return redirect(
                    url_for('admin.admin_dashboard')
                )

            return redirect(url_for('main.home'))

    elif request.method == 'POST':
        email_error = (
            form.email.errors[0]
            if form.email.errors else None
        )
        password_error = (
            form.password.errors[0]
            if form.password.errors else None
        )

    return render_template(
        'login.html',
        form=form,
        email_error=email_error,
        password_error=password_error
    )


@auth_bp.route('/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id', 'Unknown')

    logging.info(
        "LOGOUT: User ID %s logout dari IP %s",
        user_id,
        request.remote_addr
    )

    session.clear()
    return redirect(url_for('main.home'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    form_error = None

    if form.validate_on_submit():
        fullname = form.fullname.data
        email = form.email.data
        phone = form.phone.data
        password = form.password.data

        existing_user = User.query.filter(
            func.lower(User.email) == email
        ).first()

        if existing_user:
            form_error = (
                "Email sudah terdaftar. Silakan gunakan email lain atau login."
            )

            logging.warning(
                "REGISTER FAILED: Email duplikat dari IP %s",
                request.remote_addr
            )

            return render_template(
                'register.html',
                form=form,
                form_error=form_error
            )

        new_user = User(
            name=fullname,
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password),
            role='Pelanggan',
            status='Aktif'
        )

        try:
            db.session.add(new_user)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            form_error = (
                "Email sudah terdaftar. Silakan gunakan email lain."
            )

            logging.warning(
                "REGISTER FAILED: Pelanggaran unique constraint "
                "dari IP %s",
                request.remote_addr
            )

            return render_template(
                'register.html',
                form=form,
                form_error=form_error
            )

        except Exception:
            db.session.rollback()
            logging.exception(
                "REGISTER ERROR dari IP %s",
                request.remote_addr
            )

            form_error = (
                "Pendaftaran gagal diproses. Silakan coba kembali."
            )

            return render_template(
                'register.html',
                form=form,
                form_error=form_error
            )

        logging.info(
            "REGISTER SUCCESS: User ID %s berhasil mendaftar "
            "dari IP %s",
            new_user.id,
            request.remote_addr
        )

        return redirect(url_for('auth.login'))

    elif request.method == 'POST':
        errors = [
            message
            for field_errors in form.errors.values()
            for message in field_errors
        ]
        form_error = errors[0] if errors else (
            "Data pendaftaran tidak valid."
        )

    return render_template(
        'register.html',
        form=form,
        form_error=form_error
    )


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            return render_template(
                'forgot_password.html',
                email_error="Email tidak boleh kosong!"
            )

        user = User.query.filter(
            func.lower(User.email) == email
        ).first()

        if user:
            logging.info(
                "Permintaan pemulihan password diterima "
                "untuk User ID %s dari IP %s",
                user.id,
                request.remote_addr
            )

        return render_template(
            'forgot_password.html',
            success_message=(
                "Jika email terdaftar, instruksi pemulihan "
                "akan diproses."
            )
        )

    return render_template('forgot_password.html')
