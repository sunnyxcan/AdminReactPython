# app/core/firebase.py
import firebase_admin
from firebase_admin import credentials, auth
import os
import logging
import json
from app.core.config import settings

logger = logging.getLogger(__name__)

def initialize_firebase_admin():
    if not firebase_admin._apps:
        logger.info("Firebase Admin SDK belum diinisialisasi. Mencoba inisialisasi...")
        try:
            # Dapatkan konten JSON langsung dari settings
            # PERBAIKAN DI SINI: Gunakan nama atribut yang benar
            firebase_service_account_json_str = settings.FIREBASE_SERVICE_ACCOUNT_JSON_CONTENT

            if not firebase_service_account_json_str:
                logger.critical("Firebase ERROR: Variabel lingkungan FIREBASE_SERVICE_ACCOUNT_JSON tidak ditemukan atau kosong.")
                raise ValueError("Firebase service account JSON content is missing.")

            logger.info(f"DEBUG Firebase: Mengurai konten JSON untuk Firebase Admin SDK.")

            # Coba parse JSON dari string
            try:
                cred_json = json.loads(firebase_service_account_json_str)
                logger.info("DEBUG Firebase: Konten JSON kunci layanan berhasil diurai.")
            except json.JSONDecodeError as e:
                logger.critical(f"Firebase ERROR: Gagal mengurai JSON dari variabel lingkungan FIREBASE_SERVICE_ACCOUNT_JSON. Pastikan isinya adalah JSON yang valid: {e}", exc_info=True)
                # Log 500 karakter pertama dari string yang gagal diurai untuk debugging
                logger.critical(f"Firebase ERROR: Konten yang gagal diurai (potongan pertama): {firebase_service_account_json_str[:500]}...")
                raise RuntimeError(f"Failed to initialize Firebase Admin SDK: JSON parsing error from environment variable - {e}")
            except Exception as e:
                logger.critical(f"Firebase ERROR: Kesalahan tak terduga saat mengurai JSON: {e}", exc_info=True)
                raise RuntimeError(f"Failed to initialize Firebase Admin SDK: JSON read error - {e}")

            # Inisialisasi Firebase menggunakan kredensial dari JSON yang sudah diurai
            cred = credentials.Certificate(cred_json)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK berhasil diinisialisasi.")

        except Exception as e:
            logger.critical(f"Firebase ERROR: Kesalahan umum saat inisialisasi Firebase: {e}", exc_info=True)
            raise RuntimeError(f"Firebase Admin SDK initialization failed. Menghentikan aplikasi.") from e
    else:
        logger.info("Firebase Admin SDK sudah diinisialisasi (tidak perlu inisialisasi ulang).")

def get_firebase_auth():
    if not firebase_admin._apps:
        logger.warning("Firebase Admin SDK belum diinisialisasi saat get_firebase_auth dipanggil. Mencoba inisialisasi ulang.")
        initialize_firebase_admin()
    return auth