# 1. Gunakan base image Python
FROM python:3.12-slim

# 2. Tentukan direktori kerja utama di dalam kontainer
WORKDIR /app

# 3. Salin file requirements.txt untuk instalasi dependensi
COPY requirements.txt /app/

# 4. Instal pustaka Python tanpa menyimpan cache agar image tetap ringan
RUN pip install --no-cache-dir -r requirements.txt

# 5. Salin seluruh kode aplikasi dari folder app/ lokal ke dalam kontainer
COPY app/ /app/

# 6. Buka port 5000 untuk aplikasi Flask
EXPOSE 5000

# 7. Perintah utama untuk menjalankan aplikasi menggunakan Gunicorn dengan 4 worker dan binding ke port 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]