# backend/app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    FIREBASE_SERVICE_ACCOUNT_PATH: str
    # Tambahkan ini jika Anda akan membuat JWT sendiri di backend (tidak wajib jika hanya mengandalkan Firebase ID Token)
    # SECRET_KEY: str = "your_super_secret_key_change_me" # Ganti ini di .env atau di sini
    # ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Pastikan file service account ada
if not os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
    raise FileNotFoundError(f"Firebase service account file not found at: {settings.FIREBASE_SERVICE_ACCOUNT_PATH}")