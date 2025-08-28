# app/dataresign/crud.py

from sqlalchemy.orm import Session, joinedload
from app.dataresign.models import DataResign as DataResignModel
from app.dataresign.schemas import DataResignCreate, DataResignUpdate, DataResignApprove
from typing import List, Optional

def get_resignations(db: Session, skip: int = 0, limit: int = 100) -> List[DataResignModel]:
    """Mengambil daftar pengajuan resign dengan relasi yang dimuat."""
    return db.query(DataResignModel).options(
        joinedload(DataResignModel.user),
        joinedload(DataResignModel.approved_by_user),
        joinedload(DataResignModel.created_by_user),
        joinedload(DataResignModel.edited_by_user)
    ).offset(skip).limit(limit).all()

def get_resignation_by_id(db: Session, resignation_id: int) -> Optional[DataResignModel]:
    """Mengambil satu pengajuan resign berdasarkan ID."""
    return db.query(DataResignModel).options(
        joinedload(DataResignModel.user),
        joinedload(DataResignModel.approved_by_user),
        joinedload(DataResignModel.created_by_user),
        joinedload(DataResignModel.edited_by_user)
    ).filter(DataResignModel.id == resignation_id).first()

def create_resignation(db: Session, resignation_data: DataResignCreate) -> DataResignModel:
    """Membuat pengajuan resign baru."""
    db_resignation = DataResignModel(**resignation_data.model_dump())
    db.add(db_resignation)
    db.commit()
    db.refresh(db_resignation)
    return db_resignation

def update_resignation(db: Session, db_resignation: DataResignModel, resignation_data: DataResignUpdate) -> DataResignModel:
    """Memperbarui pengajuan resign yang sudah ada."""
    update_data = resignation_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_resignation, key, value)
    db.commit()
    db.refresh(db_resignation)
    return db_resignation

def approve_resignation(db: Session, db_resignation: DataResignModel, approval_data: DataResignApprove) -> DataResignModel:
    """Memperbarui status pengajuan resign."""
    db_resignation.status = approval_data.status
    db_resignation.by = approval_data.by
    db_resignation.tanggal = approval_data.tanggal # ⭐ Kolom baru
    db.commit()
    db.refresh(db_resignation)
    return db_resignation

def delete_resignation(db: Session, db_resignation: DataResignModel):
    """Menghapus pengajuan resign."""
    db.delete(db_resignation)
    db.commit()
    return