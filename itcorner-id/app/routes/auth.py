
import logging
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

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

from app.extensions import db, limiter, mail
from flask_mail import Message
from app.models import User, ActivationRequest
from app.forms.auth_forms import LoginForm, RegisterForm


auth_bp = Blueprint('auth', __name__)

@auth_bp.errorhandler(429)
def handle_rate_limit(error):
    if request.endpoint == 'auth.request_activation':
        return render_template(
            'request_activation.html',
            message=(
                "Terlalu banyak permintaan aktivasi. "
                "Silakan tunggu sebelum mencoba kembali."
            )
        ), 429

    return render_template(
        'login.html',
        form=LoginForm(),
        email_error=None,
        password_error=None,
        login_error=None,
        rate_limit_error=True
    ), 429




@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    form = LoginForm()
    email_error = None
    password_error = None
    login_error = None
    activation_available = False

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
            login_error = "Email atau kata sandi salah."

            logging.warning(
                "LOGIN FAILED: Kredensial tidak valid "
                "dari IP %s",
                request.remote_addr
            )

        elif user.status != 'Aktif':
            login_error = "Email atau kata sandi salah."
            activation_available = (user.status == 'Nonaktif')

            logging.warning(
                "LOGIN BLOCKED: Akun tidak aktif, User ID %s, IP %s",
                user.id,
                request.remote_addr
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
        password_error=password_error,
        login_error=login_error,
        activation_available=activation_available
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

        logging.info(
            "PASSWORD RECOVERY REQUEST: Permintaan diterima dari IP %s",
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


# ==========================================
# FR-009: PENGAJUAN AKTIVASI AKUN NONAKTIF
# ==========================================

@auth_bp.route('/request-activation', methods=['GET', 'POST'])
@limiter.limit("3 per hour", methods=["POST"])
def request_activation():
    generic_message = (
        "Jika data sesuai, instruksi verifikasi akan dikirim "
        "ke email terdaftar."
    )

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter(
            func.lower(User.email) == email
        ).first() if email else None

        # Respons tetap umum untuk mencegah account enumeration.
        if (
            not user
            or not password
            or not check_password_hash(user.password_hash, password)
            or user.status != 'Nonaktif'
        ):
            logging.warning(
                "ACTIVATION REQUEST DENIED from IP %s",
                request.remote_addr
            )
            return render_template(
                'request_activation.html',
                message=generic_message
            )

        pending = ActivationRequest.query.filter(
            ActivationRequest.user_id == user.id,
            ActivationRequest.status.in_([
                'Menunggu Verifikasi',
                'Menunggu Persetujuan'
            ])
        ).order_by(
            ActivationRequest.created_at.desc()
        ).first()

        # Jangan membuat pengajuan baru jika sudah terverifikasi
        # dan sedang menunggu keputusan admin.
        if pending and pending.status == 'Menunggu Persetujuan':
            return render_template(
                'request_activation.html',
                message=generic_message
            )

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(
            raw_token.encode('utf-8')
        ).hexdigest()

        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)

        if pending:
            pending.token_hash = token_hash
            pending.created_at = now
            pending.expires_at = expires
            pending.verified_at = None
            pending.status = 'Menunggu Verifikasi'
        else:
            pending = ActivationRequest(
                user_id=user.id,
                token_hash=token_hash,
                created_at=now,
                expires_at=expires,
                status='Menunggu Verifikasi'
            )
            db.session.add(pending)

        try:
            db.session.commit()

            verification_url = url_for(
                'auth.verify_activation',
                token=raw_token,
                _external=True
            )

            message = Message(
                subject='Verifikasi Pengajuan Aktivasi Akun ITCorner.id',
                recipients=[user.email],
                body=(
                    f"Halo {user.name},\n\n"
                    "Kami menerima permintaan aktivasi akun ITCorner.id.\n"
                    "Klik tautan berikut untuk memverifikasi email "
                    "dalam 30 menit:\n\n"
                    f"{verification_url}\n\n"
                    "Verifikasi email tidak otomatis mengaktifkan akun. "
                    "Pengajuan tetap memerlukan persetujuan admin.\n\n"
                    "Jika bukan kamu yang meminta, abaikan email ini."
                )
            )
            mail.send(message)

            logging.info(
                "ACTIVATION EMAIL SENT for User ID %s",
                user.id
            )

        except Exception:
            db.session.rollback()
            logging.exception(
                "ACTIVATION REQUEST PROCESSING FAILED from IP %s",
                request.remote_addr
            )

            # Jika pengajuan sudah tersimpan tetapi email gagal,
            # nonaktifkan token agar tidak ada token yatim yang valid.
            try:
                failed_request = ActivationRequest.query.filter_by(
                    user_id=user.id,
                    token_hash=token_hash
                ).first()

                if failed_request:
                    failed_request.token_hash = None
                    failed_request.status = 'Gagal Mengirim'
                    db.session.commit()

            except Exception:
                db.session.rollback()
                logging.exception(
                    "FAILED TO INVALIDATE ACTIVATION TOKEN: user_id=%s",
                    user.id
                )

            return render_template(
                'request_activation.html',
                message=(
                    "Pengiriman email gagal. Silakan coba kembali nanti."
                )
            )

        return render_template(
            'request_activation.html',
            message=generic_message
        )

    return render_template('request_activation.html')


@auth_bp.route(
    '/verify-activation/<token>',
    methods=['GET', 'POST']
)
def verify_activation(token):
    token_hash = hashlib.sha256(
        token.encode('utf-8')
    ).hexdigest()

    activation = ActivationRequest.query.filter_by(
        token_hash=token_hash,
        status='Menunggu Verifikasi'
    ).with_for_update().first()

    now = datetime.now(timezone.utc)

    if not activation or activation.expires_at <= now:
        return render_template(
            'activation_result.html',
            message=(
                "Tautan verifikasi tidak valid atau sudah kedaluwarsa. "
                "Silakan ajukan verifikasi kembali."
            )
        ), 400

    if request.method == 'POST':
        activation.verified_at = now
        activation.token_hash = None
        activation.status = 'Menunggu Persetujuan'
        db.session.commit()

        logging.info(
            "ACTIVATION EMAIL VERIFIED for request ID %s",
            activation.id
        )

        return render_template(
            'activation_result.html',
            message=(
                "Email berhasil diverifikasi. Pengajuan aktivasi "
                "menunggu persetujuan admin."
            )
        )

    return render_template(
        'verify_activation.html',
        token=token
    )
