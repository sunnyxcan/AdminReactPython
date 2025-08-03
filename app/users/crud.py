# backend/app/users/crud.py

from sqlalchemy.orm import Session
from app.users.models import User as UserModel
from typing import List

def get_user_by_uid(db: Session, user_uid: str):
    """
    Mengambil satu pengguna berdasarkan UID.
    """
    return db.query(UserModel).filter(UserModel.uid == user_uid).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    Mengambil daftar pengguna dengan paginasi.
    """
    return db.query(UserModel).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    """
    Mengambil satu pengguna berdasarkan email.
    """
    return db.query(UserModel).filter(UserModel.email == email).first()

def create_user(db: Session, user_uid: str, email: str, fullname: str, jabatan: str):
    """
    Membuat pengguna baru di database.
    """
    db_user = UserModel(uid=user_uid, email=email, fullname=fullname, jabatan=jabatan)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
