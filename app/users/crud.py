# backend/app/users/crud.py

from sqlalchemy.orm import Session, joinedload
from app.users.models import User as UserModel
from app.users.schemas import UserCreate, UserUpdate
from typing import List, Optional

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

def create_user_by_admin(db: Session, user_data: UserCreate):
    """
    Membuat pengguna baru di database dengan data lengkap, menggunakan objek UserCreate.
    """
    db_user = UserModel(**user_data.model_dump())
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Fungsi UPDATE baru
def update_user(db: Session, db_user: UserModel, user_data: UserUpdate):
    """
    Memperbarui data pengguna yang sudah ada.
    """
    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Fungsi DELETE baru
def delete_user(db: Session, db_user: UserModel):
    """
    Menghapus pengguna dari database.
    """
    db.delete(db_user)
    db.commit()
    return