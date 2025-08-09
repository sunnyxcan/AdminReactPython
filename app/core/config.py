# backend/app/core/config.py

import os
from dotenv import load_dotenv
from pytz import timezone

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Admin Panel API"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH")

    TIMEZONE = timezone('Asia/Jakarta')

settings = Settings()