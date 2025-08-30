# backend/app/dataizin/crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_
from app.dataizin.models import Izin as IzinModel
from app.users.models import User as UserModel
from app.dataizin.schemas import IzinCreate
from datetime import datetime, timedelta, date
from app.core.config import settings
from app.datatelat.crud import create_data_telat
import pytz
import logging
from typing import List

WIB_TIMEZONE = pytz.timezone('Asia/Jakarta')
UTC_TIMEZONE = pytz.timezone('UTC')

def convert_to_wib(izin: IzinModel):
    if izin.tanggal:
        izin.tanggal = izin.tanggal.astimezone(WIB_TIMEZONE)
    if izin.jamKeluar:
        izin.jamKeluar = izin.jamKeluar.astimezone(WIB_TIMEZONE)
    if izin.jamKembali:
        izin.jamKembali = izin.jamKembali.astimezone(WIB_TIMEZONE)
    if izin.createOn:
        izin.createOn = izin.createOn.astimezone(WIB_TIMEZONE)
    if izin.modifiedOn:
        izin.modifiedOn = izin.modifiedOn.astimezone(WIB_TIMEZONE)
    
    return izin

def get_izin_count_for_user_today(db: Session, user_uid: str):
    now_wib = datetime.now(WIB_TIMEZONE)
    start_of_today_wib = now_wib.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today_wib = now_wib.replace(hour=23, minute=59, second=59, microsecond=999999)

    start_of_today_utc = start_of_today_wib.astimezone(pytz.utc)
    end_of_today_utc = end_of_today_wib.astimezone(pytz.utc)

    return db.query(IzinModel).filter(
        IzinModel.user_uid == user_uid,
        IzinModel.tanggal >= start_of_today_utc,
        IzinModel.tanggal <= end_of_today_utc
    ).count()

def get_izin(db: Session, no: int):
    izin = db.query(IzinModel).filter(IzinModel.no == no).first()
    if izin:
        return convert_to_wib(izin)
    return None

def get_izins(db: Session, skip: int = 0, limit: int = 100) -> List[IzinModel]:
    izins = db.query(IzinModel).offset(skip).limit(limit).all()
    return [convert_to_wib(izin) for izin in izins]

def get_izins_by_user(db: Session, user_uid: str) -> List[IzinModel]:
    izins = db.query(IzinModel).options(joinedload(IzinModel.user)).filter(IzinModel.user_uid == user_uid).all()
    return [convert_to_wib(izin) for izin in izins]

def create_izin_keluar(db: Session, izin: IzinCreate, ip_keluar: str):
    now_utc = datetime.now(UTC_TIMEZONE).replace(microsecond=0)

    db_izin = IzinModel(
        user_uid=izin.user_uid,
        tanggal=now_utc,
        jamKeluar=now_utc,
        ipKeluar=ip_keluar,
        status="Pending"
    )
    db.add(db_izin)
    db.commit()
    db.refresh(db_izin)
    return convert_to_wib(db_izin)

def update_izin_kembali(db: Session, izin: IzinModel, ip_kembali: str, max_duration_seconds: int):
    now_utc = datetime.now(UTC_TIMEZONE).replace(microsecond=0)
    
    if not izin.jamKeluar.tzinfo:
        izin.jamKeluar = UTC_TIMEZONE.localize(izin.jamKeluar)
        
    durasi_td: timedelta = now_utc - izin.jamKeluar

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
            izin_no=izin.no,
            user_uid=izin.user_uid,
            lewat_waktu_seconds=lewat_waktu_seconds
        )

    izin.jamKembali = now_utc
    izin.ipKembali = ip_kembali
    izin.durasi = durasi_formatted
    izin.status = status_izin

    db.commit()
    db.refresh(izin)
    return convert_to_wib(izin)

def get_pending_izins(db: Session) -> List[IzinModel]:
    izins = db.query(IzinModel).options(
        joinedload(IzinModel.user)
    ).filter(
        IzinModel.status == "Pending"
    ).order_by(
        desc(IzinModel.tanggal)
    ).all()

    return [convert_to_wib(izin) for izin in izins]

def get_izins_by_user_today(db: Session, user_uid: str) -> List[IzinModel]:
    now_wib = datetime.now(WIB_TIMEZONE)
    start_of_today_wib = now_wib.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today_wib = now_wib.replace(hour=23, minute=59, second=59, microsecond=999999)

    start_of_today_utc = start_of_today_wib.astimezone(UTC_TIMEZONE)
    end_of_today_utc = end_of_today_wib.astimezone(UTC_TIMEZONE)

    izins = db.query(IzinModel).options(
        joinedload(IzinModel.user)
    ).filter(
        IzinModel.user_uid == user_uid,
        IzinModel.tanggal >= start_of_today_utc,
        IzinModel.tanggal <= end_of_today_utc
    ).all()

    return [convert_to_wib(izin) for izin in izins]

def get_overdue_izins(db: Session) -> List[IzinModel]:
    today_wib_date = datetime.now(WIB_TIMEZONE).date()

    izins = db.query(IzinModel).filter(
        IzinModel.status == "Lewat Waktu",
        func.date(func.timezone('Asia/Jakarta', IzinModel.tanggal)) == today_wib_date
    ).options(joinedload(IzinModel.user)).all()

    return [convert_to_wib(izin) for izin in izins]

def get_izins_by_year_and_date(db: Session, year: int, tanggal: str = None) -> List[IzinModel]:
    query = db.query(IzinModel).options(joinedload(IzinModel.user))

    conditions = [
        func.extract('year', func.timezone('Asia/Jakarta', IzinModel.tanggal)) == year
    ]

    if tanggal:
        try:
            filter_date = datetime.strptime(tanggal, '%Y-%m-%d').date()
            conditions.append(
                func.date(func.timezone('Asia/Jakarta', IzinModel.tanggal)) == filter_date
            )
        except ValueError:
            pass

    query = query.filter(and_(*conditions))
    query = query.order_by(desc(IzinModel.tanggal))

    izins = query.all()
    return [convert_to_wib(izin) for izin in izins]