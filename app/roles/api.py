# backend/app/roles/api.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.roles.schemas import Role, RoleCreate
from app.roles import crud as role_crud

router = APIRouter()

@router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED)
def create_new_role(role: RoleCreate, db: Session = Depends(get_db)):
    """
    Membuat role baru.
    """
    db_role = role_crud.get_role_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(status_code=400, detail="Role dengan nama ini sudah ada")
    return role_crud.create_role(db=db, role=role)

@router.get("/", response_model=List[Role])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Mengambil daftar semua role.
    """
    roles = role_crud.get_roles(db, skip=skip, limit=limit)
    return roles

@router.get("/{role_id}", response_model=Role)
def read_role(role_id: int, db: Session = Depends(get_db)):
    """
    Mengambil role berdasarkan ID.
    """
    db_role = role_crud.get_role_by_id(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    return db_role

@router.put("/{role_id}", response_model=Role)
def update_existing_role(role_id: int, role: RoleCreate, db: Session = Depends(get_db)):
    """
    Memperbarui role yang sudah ada.
    """
    db_role = role_crud.update_role(db, role_id, role)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    return db_role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_role(role_id: int, db: Session = Depends(get_db)):
    """
    Menghapus role.
    """
    success = role_crud.delete_role(db, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    return {"ok": True}