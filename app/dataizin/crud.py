# backend/app/dataizin/crud.py

from sqlalchemy.orm import Session
from app.dataizin.models import Izin as IzinModel
from app.dataizin.schemas import IzinCreate
from datetime import datetime, timedelta

def get_izin(db: Session, no: int):
    return db.query(IzinModel).filter(IzinModel.no == no).first()

def get_izins(db: Session, skip: int = 0, limit: int = 100):
    return db.query(IzinModel).offset(skip).limit(limit).all()

def get_izins_by_user(db: Session, user_uid: str):
    return db.query(IzinModel).filter(IzinModel.user_uid == user_uid).all()

def create_izin_keluar(db: Session, izin: IzinCreate, ip_keluar: str):
    jam_keluar_now = datetime.now().replace(microsecond=0)
    db_izin = IzinModel(
        user_uid=izin.user_uid,
        nama=izin.nama,
        jabatan=izin.jabatan,
        jamKeluar=jam_keluar_now,
        ipKeluar=ip_keluar,
        status="Pending"
    )
    db.add(db_izin)
    db.commit()
    db.refresh(db_izin)
    return db_izin

def update_izin_kembali(db: Session, izin: IzinModel, ip_kembali: str):
    jam_kembali_now = datetime.now().replace(microsecond=0)
    
    if izin.jamKeluar.tzinfo is not None:
        jam_keluar_naive = izin.jamKeluar.replace(tzinfo=None)
    else:
        jam_keluar_naive = izin.jamKeluar
        
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
    if total_seconds > 15 * 60:
        status_izin = "Lewat Waktu"

    izin.jamKembali = jam_kembali_now
    izin.ipKembali = ip_kembali
    izin.durasi = durasi_formatted
    izin.status = status_izin
    
    db.commit()
    db.refresh(izin)
    return izin