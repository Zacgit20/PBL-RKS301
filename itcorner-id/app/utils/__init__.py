from datetime import datetime


def format_rupiah(amount):
    return f"Rp{amount:,.0f}".replace(',', '.')

def get_current_date_indo():
    bulan_indo = [
        "Januari", "Februari", "Maret",
        "April", "Mei", "Juni",
        "Juli", "Agustus", "September",
        "Oktober", "November", "Desember"
    ]

    now = datetime.now()

    return f"{now.day} {bulan_indo[now.month - 1]} {now.year}"