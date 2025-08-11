# app/datashift/api.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.datashift import crud, schemas
from app.autentikasi.security import get_current_active_user as get_current_user
from app.users.schemas import User

router = APIRouter()

# Endpoint untuk membuat data shift baru
@router.post("/", response_model=schemas.ShiftInDB, status_code=status.HTTP_201_CREATED)
def create_new_shift(
    shift: schemas.ShiftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_shift = crud.create_shift(db=db, shift=shift, createdBy_uid=current_user.uid)
    return db_shift

# Endpoint untuk mendapatkan semua data shift
@router.get("/", response_model=List[schemas.ShiftInDB])
def read_all_shifts(
    skip: int = 0,
    limit: int = 100,
    user_uid: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    jabatan: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mengambil daftar semua data shift dengan opsi filter.
    """
    # Hapus semua logika otorisasi di sini untuk memungkinkan semua pengguna melihat semua data.
    shifts = crud.get_shifts(db, skip=skip, limit=limit, user_uid=user_uid, start_date=start_date, end_date=end_date, jabatan=jabatan)
    return shifts

# Endpoint untuk mendapatkan data shift berdasarkan no
@router.get("/{shift_no}", response_model=schemas.ShiftInDB)
def read_shift_by_no(
    shift_no: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mengambil satu data shift berdasarkan nomor (no).
    """
    db_shift = crud.get_shift(db, shift_no=shift_no)
    if db_shift is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift tidak ditemukan")

    # Hapus baris ini untuk memungkinkan semua pengguna melihat shift siapa pun
    # if current_user.role.name != "Admin" and db_shift.user_uid != current_user.uid:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Tidak memiliki izin untuk mengakses shift ini."
    #     )

    return db_shift

# Endpoint untuk memperbarui data shift
@router.put("/{shift_no}", response_model=schemas.ShiftInDB)
def update_existing_shift(
    shift_no: int,
    shift: schemas.ShiftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_shift = crud.get_shift(db, shift_no=shift_no)
    if db_shift is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift tidak ditemukan")
    
    if current_user.role.name not in ["Super Admin", "Admin"] and db_shift.user_uid != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak memiliki izin untuk memperbarui shift ini."
        )

    updated_shift = crud.update_shift(db=db, shift_no=shift_no, shift_update=shift)
    return updated_shift

# Endpoint untuk menghapus data shift
@router.delete("/{shift_no}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_shift(
    shift_no: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Menghapus data shift.
    """
    db_shift = crud.get_shift(db, shift_no=shift_no)
    if db_shift is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift tidak ditemukan")

    if current_user.role.name != "Super Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak memiliki izin untuk menghapus shift ini."
        )

    crud.delete_shift(db=db, shift_no=shift_no)
    return {"message": "Shift berhasil dihapus"}