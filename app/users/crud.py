# backend/app/users/crud.py

from sqlalchemy.orm import Session, joinedload
from app.users.models import User as UserModel
from typing import List

def get_user_by_uid(db: Session, user_uid: str):
    """
    Mengambil satu pengguna berdasarkan UID, memuat relasi role.
    """
    return db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.uid == user_uid).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    Mengambil daftar pengguna dengan paginasi, memuat relasi role.
    """
    return db.query(UserModel).options(joinedload(UserModel.role)).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    """
    Mengambil satu pengguna berdasarkan email, memuat relasi role.
    """
    return db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.email == email).first()

def create_user(db: Session, user_uid: str, email: str, fullname: str, jabatan: str):
    """
    Membuat pengguna baru di database.
    """
    db_user = UserModel(uid=user_uid, email=email, fullname=fullname, jabatan=jabatan)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
