# app/datajobdesk/api.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.datajobdesk import crud, schemas, models
from app.autentikasi.security import get_current_active_user as get_current_user
from app.users.schemas import User
from app.listjob import crud as listjob_category_crud

router = APIRouter()

### Endpoint untuk membuat data jobdesk baru

@router.post("/", response_model=schemas.JobdeskInDB, status_code=status.HTTP_201_CREATED)
def create_new_jobdesk(
    jobdesk: schemas.JobdeskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Membuat data jobdesk baru. Hanya Admin, SuperAdmin, atau staff yang bisa membuat jobdesk untuk dirinya sendiri.
    """
    # Aturan otorisasi:
    if current_user.role.name not in ["Admin", "SuperAdmin"] and jobdesk.user_uid != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sebagai Staff, Anda hanya dapat membuat jobdesk untuk diri Anda sendiri."
        )

    # Memastikan listjob_category_ids tidak mengandung duplikasi
    jobdesk.listjob_category_ids = list(set(jobdesk.listjob_category_ids))

    try:
        new_jobdesk = crud.create_jobdesk(
            db=db, 
            jobdesk_create=jobdesk, 
            createdBy_uid=current_user.uid
        )
        return new_jobdesk
    except ValueError as e:
        # Menangkap kesalahan validasi, termasuk duplikasi
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError as e:
        db.rollback()
        # Periksa detail kesalahan IntegrityError untuk memberikan pesan yang lebih spesifik
        if "unique constraint" in str(e).lower() and "kategori_jobdesk" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Kategori yang sama telah ditambahkan ke jobdesk ini."
            )
        
        # Penanganan kesalahan umum lainnya
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan server saat menyimpan data."
        )

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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
):
    """
    Mengambil satu data jobdesk berdasarkan nomor (no).
    """
    db_jobdesk = crud.get_jobdesk(db, jobdesk_no=jobdesk_no)
    if db_jobdesk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jobdesk tidak ditemukan")

    if current_user.role.name == "Staff":
        if db_jobdesk.user_uid != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sebagai Staff, Anda hanya memiliki izin untuk melihat jobdesk Anda sendiri."
            )
    
    return db_jobdesk

### Endpoint untuk memperbarui data jobdesk

@router.put("/{jobdesk_no}", response_model=schemas.JobdeskInDB)
def update_existing_jobdesk(
    jobdesk_no: int,
    jobdesk: schemas.JobdeskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Memperbarui data jobdesk yang ada.
    """
    db_jobdesk = crud.get_jobdesk(db, jobdesk_no=jobdesk_no)
    if db_jobdesk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jobdesk tidak ditemukan")

    if current_user.role.name == "Staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sebagai Staff, Anda tidak memiliki izin untuk memperbarui jobdesk."
        )
    
    if current_user.role.name != "Admin" and jobdesk.user_uid is not None and jobdesk.user_uid != db_jobdesk.user_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya Admin yang dapat mengubah pemilik jobdesk."
        )

    try:
        updated_jobdesk = crud.update_jobdesk(
            db=db,
            jobdesk_no=jobdesk_no,
            jobdesk_update=jobdesk,
            modifiedBy_uid=current_user.uid
        )
        return updated_jobdesk
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Terjadi kesalahan saat menyimpan data. Pastikan tidak ada duplikasi entri."
        )

### Endpoint untuk menghapus data jobdesk

@router.delete("/{jobdesk_no}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_jobdesk(
    jobdesk_no: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Menghapus data jobdesk.
    """
    db_jobdesk = crud.get_jobdesk(db, jobdesk_no=jobdesk_no)
    if db_jobdesk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jobdesk tidak ditemukan")

    # Logika otorisasi yang diperbarui
    if current_user.role.name not in ["SuperAdmin", "Admin"] and db_jobdesk.user_uid != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak memiliki izin untuk menghapus jobdesk ini."
        )

    crud.delete_jobdesk(db=db, jobdesk_no=jobdesk_no)
    return {"message": "Jobdesk berhasil dihapus"}