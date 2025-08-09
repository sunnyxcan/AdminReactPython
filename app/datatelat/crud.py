# backend/app/datatelat/crud.py

from sqlalchemy.orm import Session, joinedload
from app.datatelat.models import DataTelat
from app.datatelat.schemas import DataTelatCreate, DataTelatUpdate 
from app.dataizin.models import Izin as IzinModel
from sqlalchemy import extract
from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status

# --- Fungsi yang sudah ada (create_data_telat) ---
def create_data_telat(
    db: Session, 
    izin: IzinModel, 
    lewat_waktu_seconds: float, 
    durasi_formatted: str
):
    """
    Membuat entri data telat secara otomatis berdasarkan data izin yang lewat waktu.
    """
    sanksi = None
    denda = None
    keterangan = None

    if lewat_waktu_seconds <= 3 * 60:
        sanksi = "Kutip sampah"
        denda = "0"
        keterangan = f"Melebihi batas izin selama {lewat_waktu_seconds:.0f} detik."
    else:
        sanksi = "Kutip sampah / Bersihkan PC / Bersihkan meja"
        denda = "300"
        keterangan = f"Melebihi batas izin selama {lewat_waktu_seconds:.0f} detik."
    
    telat_payload = DataTelatCreate(
        izin_no=izin.no,
        user_uid=izin.user_uid,
        sanksi=sanksi,
        denda=denda,
        keterangan=keterangan,
    )
    
    db_telat = DataTelat(**telat_payload.model_dump())
    db.add(db_telat)
    db.commit()
    db.refresh(db_telat)
    return db_telat

# --- Fungsi CRUD baru ---

# Mengambil semua data telat
def get_all_datatelats(db: Session):
    # Memuat relasi 'izin', 'user', dan 'approved_by'
    return db.query(DataTelat).options(
        joinedload(DataTelat.izin), 
        joinedload(DataTelat.user),
        joinedload(DataTelat.approved_by) # <-- Tambahkan baris ini
    ).all()

# Mengambil satu data telat berdasarkan nomor
def get_datatelat_by_no(db: Session, dataTelat_no: int):
    # Memuat relasi 'izin', 'user', dan 'approved_by'
    return db.query(DataTelat).options(
        joinedload(DataTelat.izin), 
        joinedload(DataTelat.user),
        joinedload(DataTelat.approved_by) # <-- Tambahkan baris ini
    ).filter(DataTelat.no == dataTelat_no).first()

# Mengambil data telat berdasarkan tahun
def get_datatelats_by_year(db: Session, tahun: int):
    # Memuat relasi 'izin', 'user', dan 'approved_by'
    return db.query(DataTelat).options(
        joinedload(DataTelat.izin), 
        joinedload(DataTelat.user),
        joinedload(DataTelat.approved_by) # <-- Tambahkan baris ini
    ).filter(extract('year', DataTelat.createOn) == tahun).all()

# Mengambil data telat berdasarkan bulan dan tahun DARI TANGGAL IZIN
def get_datatelats_by_month_year(db: Session, bulan: Optional[int] = None, tahun: Optional[int] = None):
    # Memulai query dari DataTelat
    query = db.query(DataTelat)
    
    # Melakukan join ke tabel Izin untuk mengakses kolom 'tanggal'
    query = query.join(IzinModel, DataTelat.izin_no == IzinModel.no)
    
    if bulan is not None:
        query = query.filter(extract('month', IzinModel.tanggal) == bulan)
    if tahun is not None:
        query = query.filter(extract('year', IzinModel.tanggal) == tahun)
    
    # Memuat relasi 'izin', 'user', dan 'approved_by' setelah filter
    query = query.options(
        joinedload(DataTelat.izin), 
        joinedload(DataTelat.user),
        joinedload(DataTelat.approved_by)
    )
    
    return query.all()

def create_datatelat_manual(db: Session, datatelat: DataTelatCreate):
    db_datatelat = DataTelat(**datatelat.model_dump(exclude_unset=True))
    db.add(db_datatelat)
    db.commit()
    db.refresh(db_datatelat)
    return db_datatelat

def update_datatelat(db: Session, dataTelat_no: int, datatelat_update: DataTelatUpdate, current_user_uid: str = None):
    """
    Memperbarui data telat yang sudah ada dengan logika kondisional untuk 'status', 'keterangan', dan 'jam'.
    """
    db_datatelat = db.query(DataTelat).filter(DataTelat.no == dataTelat_no).first()
    if not db_datatelat:
        return None
    
    update_data = datatelat_update.model_dump(exclude_unset=True)
    old_status = db_datatelat.status

    # Jika 'status' diperbarui, atur 'by' menjadi user yang sedang login
    if "status" in update_data and update_data["status"] != old_status and current_user_uid:
        db_datatelat.by = current_user_uid

    # Logika untuk memperbarui 'jam'
    new_status = update_data.get("status")
    current_time_str = datetime.now().strftime("%H:%M:%S")

    if "jam" not in update_data or (update_data.get("jam") is None and new_status != old_status):
        # Jika 'jam' tidak ada di payload atau dikirim null saat status berubah,
        # atur 'jam' ke waktu saat ini.
        db_datatelat.jam = current_time_str
    elif "jam" in update_data and update_data["jam"] is not None:
        # Jika 'jam' secara eksplisit dikirim, gunakan nilainya.
        # Perbaikan ada di baris ini
        db_datatelat.jam = update_data["jam"]
    
    # Logika untuk memperbarui 'keterangan'
    new_keterangan = update_data.get("keterangan")
    if new_status == "Done":
        db_datatelat.keterangan = new_keterangan if new_keterangan and new_keterangan.strip() else "Done Sanksi"
    elif new_status in ["Izin", "Kendala"]:
        if not new_keterangan or new_keterangan.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Keterangan wajib diisi jika status '{new_status}'."
            )
        db_datatelat.keterangan = new_keterangan
    elif "keterangan" in update_data:
        db_datatelat.keterangan = new_keterangan
    
    # Perbarui semua field lain yang ada di payload
    for key, value in update_data.items():
        if key not in ["by", "jam", "keterangan", "status"]:
            setattr(db_datatelat, key, value)

    # Perbarui status jika ada di payload setelah logika keterangan
    if new_status:
        db_datatelat.status = new_status
    
    db.commit()
    db.refresh(db_datatelat)
    return db_datatelat

def delete_datatelat(db: Session, dataTelat_no: int):
    db_datatelat = db.query(DataTelat).filter(DataTelat.no == dataTelat_no).first()
    if not db_datatelat:
        return False
    db.delete(db_datatelat)
    db.commit()
    return True