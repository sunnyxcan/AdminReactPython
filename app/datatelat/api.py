# backend/app/datatelat/api.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.datatelat.schemas import DataTelat as DataTelatSchema, DataTelatCreate, DataTelatUpdate
from app.datatelat import crud as crud_datatelat
from datetime import date
from sqlalchemy import extract
from app.dataizin import crud as crud_izin
from app.autentikasi.security import get_current_active_user
from app.users.models import User

router = APIRouter()

# Dapatkan semua data telat dengan filter tahun dan limit
@router.get("/", response_model=List[DataTelatSchema])
def get_all_datatelats(
    db: Session = Depends(get_db),
    tahun: Optional[int] = None,
    limit: int = 10  # ✨ Ditambahkan parameter limit
):
    """
    Mengambil semua data telat dengan limit 10 secara default. Filter opsional berdasarkan tahun.
    """
    if tahun:
        datatelats = crud_datatelat.get_datatelats_by_year(db, tahun=tahun, limit=limit) # ✨ Teruskan limit
    else:
        datatelats = crud_datatelat.get_all_datatelats(db, limit=limit) # ✨ Teruskan limit
    return datatelats

# Dapatkan data telat berdasarkan bulan, tahun, dan limit
@router.get("/filter_by_month_year/", response_model=List[DataTelatSchema])
def get_datatelats_by_month_year(
    db: Session = Depends(get_db),
    bulan: Optional[int] = None,
    tahun: Optional[int] = None,
    limit: int = 10 # ✨ Ditambahkan parameter limit
):
    """
    Mengambil data telat dengan filter bulan dan tahun, serta limit 10 secara default.
    """
    datatelats = crud_datatelat.get_datatelats_by_month_year(db, bulan=bulan, tahun=tahun, limit=limit) # ✨ Teruskan limit
    return datatelats

# Dapatkan satu data telat berdasarkan nomor (no)
@router.get("/{dataTelat_no}", response_model=DataTelatSchema)
def get_datatelat_by_id(dataTelat_no: int, db: Session = Depends(get_db)):
    """
    Mengambil satu data telat berdasarkan nomornya.
    """
    db_datatelat = crud_datatelat.get_datatelat_by_no(db, dataTelat_no=dataTelat_no)
    if db_datatelat is None:
        raise HTTPException(status_code=404, detail="Data telat tidak ditemukan")
    return db_datatelat

# Endpoint untuk membuat data telat (ini mungkin tidak digunakan langsung oleh frontend
# karena data telat dibuat otomatis, tapi tetap baik untuk debugging/admin)
@router.post("/", response_model=DataTelatSchema, status_code=status.HTTP_201_CREATED)
def create_new_datatelat(datatelat: DataTelatCreate, db: Session = Depends(get_db)):
    """
    Membuat data telat baru.
    """
    # Perlu diperhatikan:
    # Endpoint ini hanya untuk contoh. Dalam aplikasi nyata, data telat
    # dibuat otomatis saat izin kembali lewat waktu, bukan dibuat secara manual.
    izin = crud_izin.get_izin(db, datatelat.izin_no)
    if not izin:
        raise HTTPException(status_code=404, detail="Izin tidak ditemukan.")
        
    return crud_datatelat.create_datatelat_manual(db=db, datatelat=datatelat)

# Perbarui data telat
@router.put("/{dataTelat_no}", response_model=DataTelatSchema)
def update_existing_datatelat(
    dataTelat_no: int,
    datatelat_update: DataTelatUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Ambil objek user dari dependensi
):
    """
    Memperbarui data telat yang sudah ada dan mencatat siapa yang memperbarui.
    """
    # Langsung panggil fungsi CRUD dan kirimkan user UID
    db_datatelat = crud_datatelat.update_datatelat(
        db, 
        dataTelat_no=dataTelat_no, 
        datatelat_update=datatelat_update,
        current_user_uid=current_user.uid
    )
    if db_datatelat is None:
        raise HTTPException(status_code=404, detail="Data telat tidak ditemukan")
    return db_datatelat

# Hapus data telat
@router.delete("/{dataTelat_no}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_datatelat(dataTelat_no: int, db: Session = Depends(get_db)):
    """
    Menghapus data telat.
    """
    success = crud_datatelat.delete_datatelat(db, dataTelat_no=dataTelat_no)
    if not success:
        raise HTTPException(status_code=404, detail="Data telat tidak ditemukan")
    return {"message": "Data telat berhasil dihapus"}