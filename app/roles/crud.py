# backend/app/roles/crud.py
from sqlalchemy.orm import Session
from app.roles.models import Role as RoleModel
from app.roles.schemas import RoleCreate
from typing import List

def get_role_by_id(db: Session, role_id: int):
    """
    Mengambil role berdasarkan ID.
    """
    return db.query(RoleModel).filter(RoleModel.id == role_id).first()

def get_role_by_name(db: Session, name: str):
    """
    Mengambil role berdasarkan nama.
    """
    return db.query(RoleModel).filter(RoleModel.name == name).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[RoleModel]:
    """
    Mengambil daftar semua role.
    """
    return db.query(RoleModel).offset(skip).limit(limit).all()

def create_role(db: Session, role: RoleCreate) -> RoleModel:
    """
    Membuat role baru.
    """
    db_role = RoleModel(name=role.name, description=role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_role(db: Session, role_id: int, role_data: RoleCreate) -> RoleModel:
    """
    Memperbarui role yang sudah ada.
    """
    db_role = get_role_by_id(db, role_id)
    if db_role:
        db_role.name = role_data.name
        db_role.description = role_data.description
        db.commit()
        db.refresh(db_role)
    return db_role

def delete_role(db: Session, role_id: int) -> bool:
    """
    Menghapus role berdasarkan ID.
    """
    db_role = get_role_by_id(db, role_id)
    if db_role:
        db.delete(db_role)
        db.commit()
        return True
    return False