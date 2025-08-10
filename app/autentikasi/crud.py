# app/autentikasi/crud.py
from sqlalchemy.orm import Session
from app.users import models as user_models
from app.users import schemas as user_schemas

def get_current_user_from_db(db: Session, user_uid: str):
    """
    Mengambil data pengguna dari database berdasarkan UID Supabase.
    """
    # Pastikan metode get_user ada di user_models.User
    # Atau ubah ini menjadi query SQLAlchemy langsung:
    return db.query(user_models.User).filter(user_models.User.uid == user_uid).first()