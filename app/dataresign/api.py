# app/dataresign/api.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dataresign import crud as crud_resign
from app.dataresign.schemas import DataResign, DataResignCreate, DataResignUpdate, DataResignApprove
from typing import List

router = APIRouter()

@router.get("/", response_model=List[DataResign])
def get_all_resignations(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """Mendapatkan daftar semua pengajuan resign."""
    resignations = crud_resign.get_resignations(db, skip=skip, limit=limit)
    return resignations

@router.get("/{resignation_id}", response_model=DataResign)
def get_resignation_by_id(resignation_id: int, db: Session = Depends(get_db)):
    """Mendapatkan pengajuan resign berdasarkan ID."""
    db_resignation = crud_resign.get_resignation_by_id(db, resignation_id)
    if not db_resignation:
        raise HTTPException(status_code=404, detail="Pengajuan resign tidak ditemukan.")
    return db_resignation

@router.post("/", response_model=DataResign, status_code=status.HTTP_201_CREATED)
def create_new_resignation(resignation_data: DataResignCreate, db: Session = Depends(get_db)):
    """Membuat pengajuan resign baru."""
    return crud_resign.create_resignation(db, resignation_data)

@router.put("/{resignation_id}", response_model=DataResign)
def update_existing_resignation(resignation_id: int, resignation_data: DataResignUpdate, db: Session = Depends(get_db)):
    """Memperbarui pengajuan resign yang sudah ada."""
    db_resignation = crud_resign.get_resignation_by_id(db, resignation_id)
    if not db_resignation:
        raise HTTPException(status_code=404, detail="Pengajuan resign tidak ditemukan.")
    return crud_resign.update_resignation(db, db_resignation, resignation_data)

@router.put("/{resignation_id}/approve", response_model=DataResign)
def approve_resignation_request(resignation_id: int, approval_data: DataResignApprove, db: Session = Depends(get_db)):
    """Memperbarui status pengajuan resign menjadi Approved atau Rejected."""
    db_resignation = crud_resign.get_resignation_by_id(db, resignation_id)
    if not db_resignation:
        raise HTTPException(status_code=404, detail="Pengajuan resign tidak ditemukan.")
    return crud_resign.approve_resignation(db, db_resignation, approval_data)

@router.delete("/{resignation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_resignation(resignation_id: int, db: Session = Depends(get_db)):
    """Menghapus pengajuan resign."""
    db_resignation = crud_resign.get_resignation_by_id(db, resignation_id)
    if not db_resignation:
        raise HTTPException(status_code=404, detail="Pengajuan resign tidak ditemukan.")
    crud_resign.delete_resignation(db, db_resignation)
    return