# backend/app/datatelat/crud.py

from sqlalchemy.orm import Session, joinedload
from app.datatelat.models import DataTelat
from app.datatelat.schemas import DataTelatCreate, DataTelatUpdate
from app.dataizin.models import Izin as IzinModel
from sqlalchemy import extract, desc
from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import and_

# --- Fungsi yang sudah ada (create_data_telat) ---
def create_data_telat(
    db: Session,
    izin_no: int,
    user_uid: str,
    lewat_waktu_seconds: float,
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
        izin_no=izin_no,
        user_uid=user_uid,
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

# Mengambil semua data telat dengan limit
def get_all_datatelats(db: Session, limit: int = 10): # ✨ Tambahkan parameter limit
    """
    Mengambil semua data telat dengan limit 10 secara default.
    """
    return db.query(DataTelat).options(
        joinedload(DataTelat.izin),
        joinedload(DataTelat.user),
        joinedload(DataTelat.approved_by)
    ).order_by(desc(DataTelat.no)).limit(limit).all() # ✨ Tambahkan .order_by() dan .limit()

# Mengambil satu data telat berdasarkan nomor
def get_datatelat_by_no(db: Session, dataTelat_no: int):
    return db.query(DataTelat).options(
        joinedload(DataTelat.izin),
        joinedload(DataTelat.user),
        joinedload(DataTelat.approved_by)
    ).filter(DataTelat.no == dataTelat_no).first()

# Mengambil data telat berdasarkan tahun DARI TANGGAL IZIN dengan limit
def get_datatelats_by_year(db: Session, tahun: int, limit: int = 10): # ✨ Tambahkan parameter limit
    """
    Mengambil data telat berdasarkan tahun dari tanggal izin, dengan limit 10 secara default.
    """
    query = db.query(DataTelat)
    query = query.join(IzinModel, DataTelat.izin_no == IzinModel.no)
    
    query = query.filter(extract('year', IzinModel.tanggal) == tahun)
    
    query = query.options(
        joinedload(DataTelat.izin),
        joinedload(DataTelat.user),
        joinedload(DataTelat.approved_by)
    )
    
    query = query.order_by(desc(IzinModel.tanggal)).limit(limit) # ✨ Tambahkan .order_by() dan .limit()
    
    return query.all()

# Mengambil data telat berdasarkan bulan dan tahun DARI TANGGAL IZIN dengan limit
def get_datatelats_by_month_year(db: Session, bulan: Optional[int] = None, tahun: Optional[int] = None, limit: int = 10): # ✨ Tambahkan parameter limit
    """
    Mengambil data telat berdasarkan bulan dan tahun dari tanggal izin, dengan limit 10 secara default.
    """
    query = db.query(DataTelat)
    query = query.join(IzinModel, DataTelat.izin_no == IzinModel.no)
    
    conditions = []
    if bulan is not None:
        conditions.append(extract('month', IzinModel.tanggal) == bulan)
    if tahun is not None:
        conditions.append(extract('year', IzinModel.tanggal) == tahun)
    
    if conditions:
        query = query.filter(and_(*conditions))
    
    query = query.options(
        joinedload(DataTelat.izin),
        joinedload(DataTelat.user),
        joinedload(DataTelat.approved_by)
    )
    
    query = query.order_by(desc(IzinModel.tanggal)).limit(limit) # ✨ Tambahkan .order_by() dan .limit()
    
    return query.all()

def create_datatelat_manual(db: Session, datatelat: DataTelatCreate):
    db_datatelat = DataTelat(**datatelat.model_dump(exclude_unset=True))
    db.add(db_datatelat)
    db.commit()
    db.refresh(db_datatelat)
    return db_datatelat

def update_datatelat(db: Session, dataTelat_no: int, datatelat_update: DataTelatUpdate, current_user_uid: str = None):
    db_datatelat = db.query(DataTelat).filter(DataTelat.no == dataTelat_no).first()
    if not db_datatelat:
        return None
    
    update_data = datatelat_update.model_dump(exclude_unset=True)
    old_status = db_datatelat.status

    if "status" in update_data and update_data["status"] != old_status and current_user_uid:
        db_datatelat.by = current_user_uid

    new_status = update_data.get("status")
    current_time_str = datetime.now().strftime("%H:%M:%S")

    if "jam" not in update_data or (update_data.get("jam") is None and new_status != old_status):
        db_datatelat.jam = current_time_str
    elif "jam" in update_data and update_data["jam"] is not None:
        db_datatelat.jam = update_data["jam"]
    
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
    
    for key, value in update_data.items():
        if key not in ["by", "jam", "keterangan", "status"]:
            setattr(db_datatelat, key, value)

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