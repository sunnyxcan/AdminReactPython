# backend/app/dataizin/api.py

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.dataizin.schemas import Izin as IzinSchema, IzinCreate
from app.dataizin import crud as crud_izin
from app.utils.ip_utils import get_request_ip
from app.users import crud as crud_user
from app.izin_rules import crud as crud_izin_rules
from datetime import datetime
import pytz
import threading
from app.services.tasks import send_izin_notification_async

router = APIRouter()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

HARI_INDONESIA = {
    'monday': 'Senin',
    'tuesday': 'Selasa',
    'wednesday': 'Rabu',
    'thursday': 'Kamis',
    'friday': 'Jumat',
    'saturday': 'Sabtu',
    'sunday': 'Minggu',
}

@router.get("/", response_model=List[IzinSchema])
def read_izins(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    izins = crud_izin.get_izins(db, skip=skip, limit=limit)
    return izins

@router.get("/users/{user_uid}", response_model=List[IzinSchema])
def get_izins_by_user(user_uid: str, db: Session = Depends(get_db)):
    izins = crud_izin.get_izins_by_user(db, user_uid=user_uid)
    return izins

@router.post("/keluar", response_model=IzinSchema)
def izin_keluar(
    izin: IzinCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    ip_address = get_request_ip(request)
    logger.info(f"Permintaan POST /izin/keluar dari IP: {ip_address} untuk user UID: {izin.user_uid}")

    user_data = crud_user.get_user_by_uid(db, user_uid=izin.user_uid)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan.")

    active_rule = crud_izin_rules.get_active_izin_rule(db)
    if not active_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aturan izin belum diatur atau tidak aktif."
        )

    wib_timezone = pytz.timezone('Asia/Jakarta')
    today_wib = datetime.now(wib_timezone).date()
    today_english = today_wib.strftime('%A').lower()
    today_indonesia = HARI_INDONESIA.get(today_english, None)

    daily_izin_limit = active_rule.max_daily_izin
    detail_message_limit = active_rule.max_daily_izin
    if (active_rule.is_double_shift_rule and active_rule.double_shift_day and today_indonesia == active_rule.double_shift_day):
        if active_rule.max_daily_double_shift is not None and active_rule.max_daily_double_shift >= 0:
            daily_izin_limit = active_rule.max_daily_double_shift
            detail_message_limit = active_rule.max_daily_double_shift

    if daily_izin_limit is not None and daily_izin_limit >= 0:
        today_izin_count = crud_izin.get_izin_count_for_user_today(db, user_uid=izin.user_uid)
        logger.info(f"User {user_data.fullname} (UID: {izin.user_uid}) sudah izin {today_izin_count}x hari ini. Batas: {daily_izin_limit}x.")
        if today_izin_count >= daily_izin_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Anda sudah mencapai batas ({detail_message_limit}x) izin keluar untuk hari ini."
            )

    if active_rule.max_concurrent_izin is not None and active_rule.max_concurrent_izin >= 0:
        current_pending_izins = crud_izin.get_pending_izins(db)
        logger.info(f"Jumlah izin pending saat ini: {len(current_pending_izins)}. Batas maksimal: {active_rule.max_concurrent_izin}.")
        if len(current_pending_izins) >= active_rule.max_concurrent_izin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batas jumlah izin yang sedang berjalan ({active_rule.max_concurrent_izin} izin) sudah tercapai. Silakan tunggu hingga ada yang kembali."
            )
            
    jabatan = user_data.jabatan.lower() if user_data.jabatan else None
    if jabatan:
        pending_izins_by_jabatan = [i for i in crud_izin.get_pending_izins(db) if i.user.jabatan and i.user.jabatan.lower() == jabatan]
        
        jabatan_limits = {
            "operator": active_rule.max_izin_operator,
            "kapten": active_rule.max_izin_kapten,
            "kasir": active_rule.max_izin_kasir,
            "kasir lokal": active_rule.max_izin_kasir_lokal
        }
        
        if jabatan in jabatan_limits and jabatan_limits[jabatan] is not None and jabatan_limits[jabatan] >= 0:
            logger.info(f"Jumlah izin pending untuk jabatan '{jabatan}': {len(pending_izins_by_jabatan)}. Batas: {jabatan_limits[jabatan]}.")
            if len(pending_izins_by_jabatan) >= jabatan_limits[jabatan]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Batas izin untuk jabatan '{jabatan.title()}' ({jabatan_limits[jabatan]} izin) sudah tercapai. Silakan tunggu hingga ada yang kembali."
                )

    db_izin = crud_izin.create_izin_keluar(db=db, izin=izin, ip_keluar=ip_address)
    logger.info(f"Izin keluar berhasil dibuat untuk user {user_data.fullname} (UID: {izin.user_uid}).")

    thread_db = get_db().__next__()
    notification_thread = threading.Thread(
        target=send_izin_notification_async,
        args=(
            thread_db,
            izin.user_uid,
            user_data.fullname,
            "Ada Permintaan Izin Baru",
            f"Pengguna {user_data.fullname} telah mengajukan izin keluar.",
            "/"
        )
    )
    notification_thread.start()

    return db_izin

@router.put("/kembali/{no}", response_model=IzinSchema)
def izin_kembali(
    no: int,
    request: Request,
    db: Session = Depends(get_db)
):
    ip_address = get_request_ip(request)
    logger.info(f"Permintaan PUT /izin/kembali/{no} dari IP: {ip_address}")

    db_izin = crud_izin.get_izin(db, no=no)
    if db_izin is None:
        raise HTTPException(status_code=404, detail="Izin not found")

    if db_izin.status != "Pending":
        raise HTTPException(status_code=400, detail="Silahkan melakukan izin keluar terlebih dahulu.")

    active_rule = crud_izin_rules.get_active_izin_rule(db)
    if active_rule is None:
        raise HTTPException(status_code=404, detail="Aturan izin belum diatur.")
        
    db_izin_updated = crud_izin.update_izin_kembali(db=db, izin=db_izin, ip_kembali=ip_address, max_duration_seconds=active_rule.max_duration_seconds)

    logger.info(f"Izin kembali berhasil untuk user {db_izin_updated.user.fullname} (UID: {db_izin_updated.user_uid}). Durasi: {db_izin_updated.durasi}, Status: {db_izin_updated.status}.")

    thread_db = get_db().__next__()
    notification_thread = threading.Thread(
        target=send_izin_notification_async,
        args=(
            thread_db,
            db_izin_updated.user_uid,
            db_izin_updated.user.fullname,
            "Pemberitahuan Izin Kembali",
            f"Pengguna {db_izin_updated.user.fullname} telah kembali.",
            "/"
        )
    )
    notification_thread.start()

    return db_izin_updated

@router.get("/pending", response_model=List[IzinSchema])
def get_pending_izins(db: Session = Depends(get_db)):
    pending_izins = crud_izin.get_pending_izins(db)
    return pending_izins

@router.get("/users/{user_uid}/today", response_model=List[IzinSchema])
def get_izins_by_user_today(user_uid: str, db: Session = Depends(get_db)):
    izins = crud_izin.get_izins_by_user_today(db, user_uid=user_uid)
    if not izins:
        return []
    return izins

@router.get("/by_year_and_date", response_model=List[IzinSchema])
def get_izins_by_year_and_date(
    db: Session = Depends(get_db),
    year: int = None,
    tanggal: str = None
):
    if not year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameter 'year' harus disediakan."
        )
    izins = crud_izin.get_izins_by_year_and_date(db, year=year, tanggal=tanggal)
    return izins

@router.get("/overdue", response_model=List[IzinSchema])
def get_overdue_izins(db: Session = Depends(get_db)):
    overdue_izins = crud_izin.get_overdue_izins(db)
    return overdue_izins