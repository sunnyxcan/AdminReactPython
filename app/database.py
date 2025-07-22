# backend/app/database.py

from sqlalchemy import create_engine, text # Tambahkan 'text' di sini
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL

logger.info(f"Attempting to connect to database using URL (first few chars): {DATABASE_URL[:30]}...")

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
    with engine.connect() as connection:
        # Ubah baris ini:
        connection.execute(text("SELECT 1")) # Gunakan text() untuk kueri SQL mentah di SQLAlchemy 2.0+
        logger.info("Database connection test successful.")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}", exc_info=True)
    raise RuntimeError(f"Could not connect to the database: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()