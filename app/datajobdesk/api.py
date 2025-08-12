# app/datajobdesk/api.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.datajobdesk import crud, schemas, models
from app.autentikasi.security import get_current_active_user as get_current_user
from app.users.schemas import User # <-- PERBAIKI: Ganti UserDetail dengan User
from app.listjob import crud as listjob_category_crud

router = APIRouter()

### Endpoint untuk membuat data jobdesk baru

@router.post("/", response_model=schemas.JobdeskInDB, status_code=status.HTTP_201_CREATED)
def create_new_jobdesk(
    jobdesk: schemas.JobdeskCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <-- PERBAIKI
):
    """
    Membuat data jobdesk baru.
    """
    if current_user.role.name == "Staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sebagai Staff, Anda tidak memiliki izin untuk membuat jobdesk."
        )

    for cat_id in jobdesk.listjob_category_ids:
        category_exists = listjob_category_crud.get_list_job_category(db, cat_id)
        if not category_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kategori jobdesk dengan ID {cat_id} tidak ditemukan."
            )

    db_jobdesk = crud.create_jobdesk(db=db, jobdesk=jobdesk, createdBy_uid=current_user.uid)
    return db_jobdesk

### Endpoint untuk mendapatkan semua data jobdesk

@router.get("/", response_model=List[schemas.JobdeskInDB])
def read_all_jobdesks(
    skip: int = 0,
    limit: int = 100,
    user_uid: Optional[str] = None,
    tanggal: Optional[date] = None,
    listjob_category_id: Optional[int] = None,
    search: Optional[str] = None,
    jabatan: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <-- PERBAIKI
):
    """
    Mengambil daftar semua data jobdesk dengan opsi filter dan paginasi.
    """
    if current_user.role.name != "Admin":
        if user_uid is not None and current_user.uid != user_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda hanya dapat melihat jobdesk milik Anda sendiri atau semua jobdesk."
            )

    jobdesks = crud.get_jobdesks(
        db,
        skip=skip,
        limit=limit,
        user_uid=user_uid,
        tanggal_efektif_mulai=tanggal,
        tanggal_efektif_akhir=tanggal,
        listjob_category_id=listjob_category_id,
        search_query=search,
        jabatan=jabatan
    )
    return jobdesks

### Endpoint untuk mendapatkan data jobdesk berdasarkan no

@router.get("/{jobdesk_no}", response_model=schemas.JobdeskInDB)
def read_jobdesk_by_no(
    jobdesk_no: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <-- PERBAIKI
):
    """
    Mengambil satu data jobdesk berdasarkan nomor (no).
    """
    db_jobdesk = crud.get_jobdesk(db, jobdesk_no=jobdesk_no)
    if db_jobdesk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jobdesk tidak ditemukan")

    if current_user.role.name != "Admin" and db_jobdesk.user_uid != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak memiliki izin untuk mengakses jobdesk ini."
        )

    return db_jobdesk

### Endpoint untuk memperbarui data jobdesk

@router.put("/{jobdesk_no}", response_model=schemas.JobdeskInDB)
def update_existing_jobdesk(
    jobdesk_no: int,
    jobdesk: schemas.JobdeskUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <-- PERBAIKI
):
    """
    Memperbarui data jobdesk yang ada.
    """
    db_jobdesk = crud.get_jobdesk(db, jobdesk_no=jobdesk_no)
    if db_jobdesk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jobdesk tidak ditemukan")

    if current_user.role.name != "Admin" and db_jobdesk.user_uid != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak memiliki izin untuk memperbarui jobdesk ini."
        )

    if current_user.role.name != "Admin" and jobdesk.user_uid is not None and jobdesk.user_uid != db_jobdesk.user_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak dapat mengubah pemilik jobdesk."
        )

    if jobdesk.listjob_category_ids is not None:
        for cat_id in jobdesk.listjob_category_ids:
            category_exists = listjob_category_crud.get_list_job_category(db, cat_id)
            if not category_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Kategori jobdesk dengan ID {cat_id} tidak ditemukan."
                )

    updated_jobdesk = crud.update_jobdesk(
        db=db,
        jobdesk_no=jobdesk_no,
        jobdesk_update=jobdesk,
        modifiedBy_uid=current_user.uid
    )
    return updated_jobdesk

### Endpoint untuk menghapus data jobdesk

@router.delete("/{jobdesk_no}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_jobdesk(
    jobdesk_no: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <-- PERBAIKI
):
    """
    Menghapus data jobdesk.
    """
    db_jobdesk = crud.get_jobdesk(db, jobdesk_no=jobdesk_no)
    if db_jobdesk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jobdesk tidak ditemukan")

    if current_user.role.name != "Admin" and db_jobdesk.user_uid != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak memiliki izin untuk menghapus jobdesk ini."
        )

    crud.delete_jobdesk(db=db, jobdesk_no=jobdesk_no)
    return {"message": "Jobdesk berhasil dihapus"}