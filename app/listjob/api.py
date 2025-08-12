# app/listjob/api.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.listjob import crud, schemas, models
from app.autentikasi.security import get_current_active_user as get_current_user
from app.users.schemas import User  # <-- PERBAIKI: Ganti UserDetail dengan User

router = APIRouter()

# Endpoint: Mendapatkan semua kategori list job
@router.get("/", response_model=List[schemas.ListJobCategoryInDB])
def read_all_list_job_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # <-- PERBAIKI
):
    """
    Mengambil daftar semua kategori list job. Dapat diakses oleh semua user yang terautentikasi.
    """
    categories = crud.get_list_job_categories(db, skip=skip, limit=limit)
    return categories

# Endpoint: Membuat kategori list job baru
@router.post("/", response_model=schemas.ListJobCategoryInDB, status_code=status.HTTP_201_CREATED)
def create_new_list_job_category(
    category: schemas.ListJobCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # <-- PERBAIKI
):
    """
    Membuat kategori list job baru. Dapat diakses oleh semua peran KECUALI Staff.
    """
    if current_user.role.name == "Staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki izin untuk membuat kategori list job. Peran Staff tidak diizinkan."
        )
    
    db_category = crud.get_list_job_category_by_name(db, nama=category.nama)
    if db_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nama kategori sudah ada.")

    created_category = crud.create_list_job_category(db=db, category=category, createdBy_uid=current_user.uid)
    return created_category

# Endpoint: Mendapatkan kategori list job berdasarkan ID
@router.get("/{category_id}", response_model=schemas.ListJobCategoryInDB)
def read_list_job_category_by_id(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # <-- PERBAIKI
):
    """
    Mengambil satu kategori list job berdasarkan ID. Dapat diakses oleh semua user yang terautentikasi.
    """
    db_category = crud.get_list_job_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori list job tidak ditemukan")
    return db_category

# Endpoint: Memperbarui kategori list job
@router.put("/{category_id}", response_model=schemas.ListJobCategoryInDB)
def update_existing_list_job_category(
    category_id: int,
    category_update: schemas.ListJobCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # <-- PERBAIKI
):
    """
    Memperbarui kategori list job yang ada. Hanya untuk admin.
    """
    if current_user.role.name != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki izin untuk memperbarui kategori list job."
        )

    db_category = crud.get_list_job_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori list job tidak ditemukan")

    if category_update.nama and category_update.nama != db_category.nama:
        existing_category = crud.get_list_job_category_by_name(db, nama=category_update.nama)
        if existing_category and existing_category.id != category_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nama kategori sudah digunakan oleh kategori lain.")

    updated_category = crud.update_list_job_category(
        db=db,
        category_id=category_id,
        category_update=category_update,
        modifiedBy_uid=current_user.uid
    )
    return updated_category

# Endpoint: Menghapus kategori list job
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_list_job_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # <-- PERBAIKI
):
    """
    Menghapus kategori list job. Hanya untuk admin.
    """
    if current_user.role.name != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki izin untuk menghapus kategori list job."
        )

    db_category = crud.get_list_job_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori list job tidak ditemukan")

    crud.delete_list_job_category(db=db, category_id=category_id)
    return {"message": "Kategori list job berhasil dihapus"}