# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings # Asumsikan settings ada di sini atau impor

import logging

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mengambil DATABASE_URL dari settings
DATABASE_URL = settings.DATABASE_URL

# Tambahkan logging untuk melihat DATABASE_URL (HATI-HATI: jangan log kredensial sensitif di produksi)
logger.info(f"Attempting to connect to database using URL (first few chars): {DATABASE_URL[:30]}...") # Log sebagian URL

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True, # Memastikan koneksi sehat
        # pool_recycle=3600 # Opsional: Daur ulang koneksi setiap jam
    )
    # Coba koneksi sederhana untuk validasi awal
    with engine.connect() as connection:
        connection.execute(f"SELECT 1") # Gunakan text() untuk SQLAlchemy 2.0+ jika ini SQL mentah
        logger.info("Database connection test successful.")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}", exc_info=True)
    # Penting: Jika koneksi gagal, aplikasi TIDAK BOLEH berjalan
    raise RuntimeError(f"Could not connect to the database: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()