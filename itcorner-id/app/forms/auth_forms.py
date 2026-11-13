from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    Regexp
)


class LoginForm(FlaskForm):
    email = StringField(
        'Email',
        filters=[lambda value: value.strip().lower() if value else value],
        validators=[
            DataRequired(message='Email wajib diisi.'),
            Length(max=150, message='Email terlalu panjang.'),
            Email(message='Format email tidak valid.')
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password wajib diisi.')
        ]
    )


class RegisterForm(FlaskForm):
    fullname = StringField(
        'Nama lengkap',
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message='Nama lengkap wajib diisi.'),
            Length(
                max=100,
                message='Nama maksimal 100 karakter.'
            )
        ]
    )

    email = StringField(
        'Email',
        filters=[lambda value: value.strip().lower() if value else value],
        validators=[
            DataRequired(message='Email wajib diisi.'),
            Length(max=150, message='Email terlalu panjang.'),
            Email(message='Format email tidak valid.')
        ]
    )

    phone = StringField(
        'Nomor telepon',
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message='Nomor telepon wajib diisi.'),
            Regexp(
                r'^[0-9]{10,13}$',
                message='Nomor telepon harus terdiri dari 10 hingga 13 digit.'
            )
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password wajib diisi.'),
            Length(
                min=8,
                max=128,
                message='Password harus terdiri dari 8 hingga 128 karakter.'
            )
        ]
    )

    confirm_password = PasswordField(
        'Konfirmasi password',
        validators=[
            DataRequired(message='Konfirmasi password wajib diisi.'),
            EqualTo(
                'password',
                message='Konfirmasi kata sandi tidak cocok.'
            )
        ]
    )

    terms = BooleanField(
        'Persetujuan syarat dan ketentuan',
        validators=[
            DataRequired(message='Anda harus menyetujui Syarat & Ketentuan.')
        ]
    )
