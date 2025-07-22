# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Menggunakan DATABASE_URL dari pengaturan
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Buat engine SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

# Buat sesi database lokal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base untuk model deklaratif SQLAlchemy
Base = declarative_base()

# Dependency untuk mendapatkan sesi database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()