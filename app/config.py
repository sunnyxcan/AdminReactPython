# backend/app/config.py

import os
from pydantic_settings import BaseSettings, SettingsConfigDict # Gunakan pydantic-settings

class Settings(BaseSettings):
    DATABASE_URL: str
    FIREBASE_SERVICE_ACCOUNT_KEY: str # Ini akan kita ambil dari env var

    # Menggunakan .env untuk pengembangan lokal
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()