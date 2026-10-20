from datetime import datetime

# ==========================================
# DATA DUMMY / MOCK DATABASE SEMENTARA
# ==========================================
products_db = [
    {"id": 1, "sku": "LAP-ASU-A1404", "name": "ASUS Vivobook 14 A1404", "category": "Laptop", "brand": "ASUS", "price_num": 8499000, "stock": 12, "description": "Laptop ringan harian."},
    {"id": 2, "sku": "AKS-LOG-M331", "name": "Logitech M331 Silent", "category": "Aksessori", "brand": "Logitech", "price_num": 249000, "stock": 38, "description": "Mouse silent click."},
    {"id": 3, "sku": "MON-SAM-S24R", "name": "Samsung Monitor 24\" S24R", "category": "Monitor", "brand": "Samsung", "price_num": 1699000, "stock": 9, "description": "Monitor Full HD IPS."},
    {"id": 4, "sku": "AUD-HYP-CS2", "name": "HyperX Cloud Stinger 2", "category": "Audio", "brand": "HyperX", "price_num": 699000, "stock": 0, "description": "Headset gaming berkabel."}
]

users_db = [
    {"id": 1, "name": "Budi Santoso", "email": "budi@gmail.com", "password": "user1234","role": "Pelanggan", "joined": "12 Okt 2026", "status": "Aktif"},
    {"id": 2, "name": "Siti Aminah", "email": "siti@gmail.com", "password": "user0234","role": "Pelanggan", "joined": "15 Okt 2026", "status": "Aktif"},
    {"id": 3, "name": "Laila Rezky", "email": "laila@itcorner.id", "password": "admin1234", "role": "Admin", "joined": "01 Jan 2026", "status": "Aktif"},
    {"id": 4, "name": "Syika arjuna", "email": "syika@itcorner.id", "password": "admin0234", "role": "Admin", "joined": "03 Jan 2026", "status": "Aktif"}
]

payments_db = []
orders_db = []

# ==========================================
# HELPER FUNCTIONS (REAL-TIME & FORMATTING)
# ==========================================
def format_rupiah(amount):
    return f"Rp{amount:,.0f}".replace(',', '.')

def get_current_date_indo():
    bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    now = datetime.now()
    return f"{now.day} {bulan_indo[now.month - 1]} {now.year}"

