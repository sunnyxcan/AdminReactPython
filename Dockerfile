# Gunakan image Python resmi sebagai base image
FROM python:3.11-slim-buster

# Atur direktori kerja di dalam container
WORKDIR /app

# Salin file requirements.txt ke direktori kerja
COPY requirements.txt .

# Instal dependensi Python
RUN pip install --no-cache-dir -r requirements.txt

# Pastikan gunicorn dan uvicorn terinstal.
RUN pip install --no-cache-dir gunicorn uvicorn

# Salin semua file proyek ke direktori kerja
COPY . .

# Expose port yang digunakan aplikasi FastAPI (tidak terlalu penting untuk Koyeb, tapi baik untuk dokumentasi)
EXPOSE 8000

# === PERBAIKI BARIS INI ===
# Gunakan CMD dalam bentuk shell untuk memastikan evaluasi variabel lingkungan $PORT
# Ini akan menjalankan perintah melalui /bin/sh -c, memungkinkan $PORT dievaluasi.
CMD gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 4 --worker-class uvicorn.workers.UvicornWorker --log-level debug app.main:app
# === AKHIR PERBAIKAN ===