from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    # Perintah ini yang menyuruh Flask mengambil file HTML, bukan lagi teks biasa
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    email_error = None
    password_error = None
    rate_limit_error = False

    if request.method == 'POST':
        email = request.form.get ('email', '').strip()
        password = request.form.get('password', '').strip()

        # 1. Cek jika kolom kosong
        if not email: 
            email_error = "Email wajib diisi."
        if not password:
            password_error = "Password wajib diisi."
        # 2. Jika kedua kolom sudah diisi, baru diproses ke halaman selanjutnya/home
        if email and password:
            return redirect(url_for('home'))
        
    return render_template('login.html', email_error=email_error, password_error=password_error, rate_limit_error=rate_limit_error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/detail')
def detail():
    return render_template('detail.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    email_error = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            email_error = "Email wajib diisi."
        else:
            return redirect(url_for('reset_password'))

    return render_template('forgot_password.html', email_error=email_error)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    password_error = None
    confirm_error = None

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not password:
            password_error = "Kata sandi baru wajib diisi."
        elif len(password) < 8:
            password_error = "Kata sandi minimal harus 8 karakter."

        if not confirm_password:
            confirm_error = "Konfirmasi kata sandi wajib diisi."
        elif password != confirm_password:
            confirm_error = "Kata sandi dan konfirmasi kata sandi tidak cocok."

        # Jika validasi lolos, simpan password baru & arahkan ke login
        if password and confirm_password and (password == confirm_password) and len(password) >= 8:
            # Di sini logika update password di database
            return redirect(url_for('login'))

    return render_template('reset_password.html', password_error=password_error, confirm_error=confirm_error)

if __name__ == '__main__':
    app.run(debug=True)