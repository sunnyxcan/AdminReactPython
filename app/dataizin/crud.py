# backend/app/dataizin/crud.py (Versi yang Dioptimalkan dan Diperbarui)

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.dataizin.models import Izin as IzinModel
from app.users.models import User as UserModel
from app.dataizin.schemas import IzinCreate
from datetime import datetime, timedelta, date
from app.core.config import settings
from app.datatelat.crud import create_data_telat

# --- Fungsi baru untuk validasi rules ---

def get_izin_count_for_user_today(db: Session, user_uid: str):
    """
    Menghitung jumlah izin yang sudah diajukan oleh seorang pengguna hari ini.
    """
    today = date.today()
    return db.query(IzinModel).filter(
        IzinModel.user_uid == user_uid,
        func.date(IzinModel.createOn) == today
    ).count()
    
# --- FUNGSI INI DIHAPUS ---
# def get_pending_izins_by_jabatan(db: Session, jabatan: str):
#     """
#     Mengambil daftar izin yang sedang pending berdasarkan jabatan.
#     """
#     return db.query(IzinModel).filter(
#         IzinModel.status == "Pending",
#         func.lower(IzinModel.jabatan) == jabatan
#     ).all()

# --- Fungsi yang sudah ada, tapi dimodifikasi ---

def get_izin(db: Session, no: int):
    return db.query(IzinModel).filter(IzinModel.no == no).first()

def get_izins(db: Session, skip: int = 0, limit: int = 100):
    return db.query(IzinModel).offset(skip).limit(limit).all()

def get_izins_by_user(db: Session, user_uid: str):
    return db.query(IzinModel).options(joinedload(IzinModel.user)).filter(IzinModel.user_uid == user_uid).all()

def create_izin_keluar(db: Session, izin: IzinCreate, ip_keluar: str):
    jam_keluar_now = datetime.now().replace(microsecond=0)
    tanggal_izin = datetime.now(settings.TIMEZONE).date() 
    
    db_izin = IzinModel(
        user_uid=izin.user_uid,
        tanggal=tanggal_izin,
        jamKeluar=jam_keluar_now,
        ipKeluar=ip_keluar,
        status="Pending"
    )
    db.add(db_izin)
    db.commit()
    db.refresh(db_izin)
    return db_izin

def update_izin_kembali(db: Session, izin: IzinModel, ip_kembali: str, max_duration_seconds: int):
    jam_kembali_now = datetime.now().replace(microsecond=0)
    
    jam_keluar_naive = izin.jamKeluar.replace(tzinfo=None) if izin.jamKeluar.tzinfo else izin.jamKeluar
    durasi_td: timedelta = jam_kembali_now - jam_keluar_naive

    total_seconds = durasi_td.total_seconds()
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    durasi_str_parts = []
    if hours > 0:
        durasi_str_parts.append(f"{hours} Jam")
    if minutes > 0:
        durasi_str_parts.append(f"{minutes} Menit")
    if seconds > 0:
        durasi_str_parts.append(f"{seconds} Detik")
    
    if not durasi_str_parts:
        durasi_str_parts.append("Kurang dari 1 Detik")

    durasi_formatted = " ".join(durasi_str_parts)

    status_izin = "Tepat Waktu"
    if max_duration_seconds > 0 and total_seconds > max_duration_seconds:
        status_izin = "Lewat Waktu"
        
        lewat_waktu_seconds = total_seconds - max_duration_seconds
        create_data_telat(
            db, 
            izin=izin, 
            lewat_waktu_seconds=lewat_waktu_seconds,
            durasi_formatted=durasi_formatted
        )
        
    izin.jamKembali = jam_kembali_now
    izin.ipKembali = ip_kembali
    izin.durasi = durasi_formatted
    izin.status = status_izin
    
    db.commit()
    db.refresh(izin)
    return izin

def get_pending_izins(db: Session):
    return db.query(IzinModel).filter(IzinModel.status == "Pending").options(joinedload(IzinModel.user)).all()

def get_izins_by_user_today(db: Session, user_uid: str):
    """
    Mengambil semua data izin untuk user tertentu pada hari ini.
    """
    today = datetime.now(settings.TIMEZONE).date()

    return db.query(IzinModel).options(
        joinedload(IzinModel.user)
    ).filter(
        IzinModel.user_uid == user_uid,
        IzinModel.tanggal == today
    ).all()

def get_overdue_izins(db: Session):
    """
    Mengambil semua data izin yang statusnya "Lewat Waktu" untuk hari ini.
    """
    today = date.today()
    return db.query(IzinModel).filter(
        IzinModel.status == "Lewat Waktu",
        func.date(IzinModel.createOn) == today
    ).options(joinedload(IzinModel.user)).all()