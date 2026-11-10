# ITCorner.id – Web Application & Service Component

Modul aplikasi web e-commerce berbasis Python Flask untuk proyek **PBL-RKS301: ITCorner.id**. Modul ini mencakup antarmuka pelanggan (*customer*), antarmuka administrator (*admin*), skema kontrol akses berbasis peran (RBAC), skrip deployment, integrasi WAF ModSecurity, aturan Suricata, dan korelasi log Wazuh SIEM.

Untuk dokumentasi arsitektur dan progres menyeluruh proyek PBL-RKS301, silakan merujuk ke berkas [README Utama Proyek](../README.md).

---

## 🚀 Fitur Utama Aplikasi

1. **9 Fitur Customer:**
   - Autentikasi dengan proteksi brute-force (lockout 15 menit setelah 5x gagal berturut-turut).
   - Katalog produk dengan pencarian kata kunci dan penyaringan kategori (*parameterized query* anti-SQLi).
   - Detail spesifikasi produk dan navigasi breadcrumb.
   - Ulasan dan rating produk dengan sanitasi anti-XSS (`html.escape`).
   - Profil pengguna dan unggahan avatar (validasi MIME, ekstensi, batas ukuran 2MB, dan header magic bytes).
   - Keranjang belanja dinamis dan perhitungan kuantitas.
   - Checkout atomik dengan pembuatan nomor invoice unik.
   - Formulir unggah bukti pembayaran transfer bank.
   - Riwayat dan pelacakan status pesanan real-time.

2. **4 Fitur Administrator (RBAC Terproteksi):**
   - Manajemen katalog produk (CRUD produk, harga, stok, spesifikasi).
   - Manajemen akun pengguna (aktivasi/deaktivasi akun tanpa mengekspos hash kata sandi).
   - Dashboard analitik ringkasan transaksi dan total omzet.
   - Approval bukti pembayaran pesanan pelanggan.

---

## 📁 Struktur Direktori `itcorner-id/`

```text
itcorner-id/
├── app/
│   ├── app.py                # Inisialisasi Flask, blueprint routing, & error handling
│   ├── dummy_db.py           # In-memory storage fallback untuk unit testing mandiri
│   ├── extensions.py         # Ekstensi Flask
│   ├── models/               # Model data database (db.py, order.py, product.py, dll.)
│   ├── routes/               # Blueprint pengendali alur (customer.py, admin.py)
│   ├── static/               # File CSS, JavaScript, dan direktori uploads/
│   ├── templates/            # Template tampilan HTML Jinja2
│   └── utils/                # Utilitas keamanan (hashing, sanitasi XSS, validasi upload)
├── config/
│   ├── nginx/                # Konfigurasi reverse proxy TLS (itcorner.conf)
│   ├── suricata/             # Rule IDS/IPS kustom (itcorner-local.rules)
│   ├── waf/                  # ModSecurity v3 + OWASP CRS (modsecurity-crs.conf)
│   └── wazuh/                # Rule Wazuh (local_rules.xml) & integrasi Telegram
├── scripts/
│   ├── create_admin.py       # Pembuatan akun administrator awal
│   ├── deploy.sh             # Skrip deploy otomatis via SSH dengan auto-rollback
│   └── healthcheck.sh        # Pemeriksaan respons HTTP /health
├── tests/
│   ├── security/             # threat_matrix_soc.md & test_waf_attacks.sh
│   └── unit/                 # Pengujian unit pytest (test_app.py)
├── Dockerfile                # Dockerfile Python 3.10-slim + Gunicorn WSGI
├── docker-compose.yml        # Orkestrasi layanan itcorner_web & itcorner_db
└── requirements.txt          # Daftar paket dependensi Python
```

---

## ⚙️ Menjalankan Layanan Secara Lokal

### Menggunakan Docker Compose (Direkomendasikan):
```bash
# 1. Jalankan kontainer aplikasi dan basis data
docker compose up -d --build

# 2. Periksa status kontainer
docker compose ps

# 3. Buat akun administrator pertama
docker compose exec itcorner_web python scripts/create_admin.py

# 4. Akses antarmuka web
# Customer: http://localhost:5000/
# Admin   : http://localhost:5000/admin/
```

### Menggunakan Virtual Environment Python Lokal:
```bash
# 1. Buat dan aktifkan virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 2. Instal dependensi
pip install -r requirements.txt

# 3. Jalankan server aplikasi
python -m app.app
```

---

## 🧪 Menjalankan Rangkaian Pengujian & Audit Keamanan

```bash
# 1. Unit Testing & RBAC Access Testing
pytest tests/unit/test_app.py -v

# 2. Pemindaian Celah Keamanan Kode (SAST)
bandit -r app/ -ll

# 3. Pemeriksaan Kerentanan Dependensi (SCA)
pip-audit -r requirements.txt

# 4. Simulasi Serangan WAF (jika Nginx + ModSecurity aktif)
bash tests/security/test_waf_attacks.sh
```

---

## 🔐 Standar Keamanan Pengembangan (Secure Coding Checklist)

- [x] **Anti-SQL Injection:** Menggunakan *parameterized query* `%s` pada seluruh pemanggilan `cursor.execute()`.
- [x] **Anti-XSS:** Sanitasi teks masukan menggunakan `html.escape()` sebelum disimpan atau dirender.
- [x] **Anti-CSRF:** Implementasi token validasi formulir POST dan cookie session aman (`HttpOnly`, `SameSite=Lax`).
- [x] **Password Security:** Hashing menggunakan PBKDF2-SHA256 dengan *salt* acak.
- [x] **File Upload Validation:** Whitelist ekstensi, verifikasi MIME type, batasan ukuran 2MB, dan validasi *magic bytes*.
- [x] **Deployment Healthcheck:** Menyediakan endpoint `/health` yang mengembalikan kode `200 OK`.
