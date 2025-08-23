# backend/app/dataizin/api.py

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.core.database import get_db
from app.dataizin.schemas import Izin as IzinSchema, IzinCreate
from app.dataizin import crud as crud_izin
from app.services.fcm import send_fcm_message
from app.fcm import crud as fcm_crud
from app.utils.ip_utils import get_request_ip
import logging
from app.users import crud as crud_user # Pastikan ini diimpor
from app.izin_rules import crud as crud_izin_rules
from datetime import date, datetime

from app.datatelat import schemas as datatelat_schemas
from app.datatelat import models as datatelat_models
from app.dataizin.models import Izin as IzinModel
from sqlalchemy import func

router = APIRouter()

HARI_INDONESIA = {
    'monday': 'Senin',
    'tuesday': 'Selasa',
    'wednesday': 'Rabu',
    'thursday': 'Kamis',
    'friday': 'Jumat',
    'saturday': 'Sabtu',
    'sunday': 'Minggu',
}

def send_izin_notification(db: Session, sender_uid: str, nama: str, title: str, body: str):
    all_users = crud_user.get_users(db)
    target_users_uids = [user.uid for user in all_users if user.uid != sender_uid]

    for target_user_uid in target_users_uids:
        target_fcm_tokens = fcm_crud.get_fcm_tokens_by_user(db, user_uid=target_user_uid)
        for token in target_fcm_tokens:
            is_sent = send_fcm_message(
                token=token, 
                title=title,
                body=body
            )
            if not is_sent:
                logging.warning(f"Menghapus token yang tidak valid dari database: {token}")
                fcm_crud.delete_fcm_token(db, fcm_token=token)


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
    # Baris yang diperbaiki
    user_data = crud_user.get_user_by_uid(db, user_uid=izin.user_uid)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan.")

    active_rule = crud_izin_rules.get_active_izin_rule(db)
    if not active_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Aturan izin belum diatur atau tidak aktif."
        )

    today_english = date.today().strftime('%A').lower()
    today_indonesia = HARI_INDONESIA.get(today_english, None)

    print(f"Hari ini: {today_indonesia}")
    print(f"Aturan Double Shift Aktif?: {active_rule.is_double_shift_rule}")
    print(f"Hari Double Shift di DB: {active_rule.double_shift_day}")
    print(f"Max Izin Normal: {active_rule.max_daily_izin}")
    print(f"Max Izin Double Shift: {active_rule.max_daily_double_shift}")

    daily_izin_limit = active_rule.max_daily_izin
    detail_message_limit = active_rule.max_daily_izin

    if (active_rule.is_double_shift_rule and 
        active_rule.double_shift_day and 
        today_indonesia == active_rule.double_shift_day):
        if active_rule.max_daily_double_shift is not None and active_rule.max_daily_double_shift >= 0:
            daily_izin_limit = active_rule.max_daily_double_shift
            detail_message_limit = active_rule.max_daily_double_shift

    print(f"Batas izin yang diterapkan: {daily_izin_limit}")

    if daily_izin_limit > 0:
        today_izin_count = crud_izin.get_izin_count_for_user_today(db, user_uid=izin.user_uid)
        if today_izin_count >= daily_izin_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Anda sudah mencapai batas ({detail_message_limit}x) izin keluar untuk hari ini."
            )

    if active_rule.max_concurrent_izin > 0:
        current_pending_izins = crud_izin.get_pending_izins(db)
        if len(current_pending_izins) >= active_rule.max_concurrent_izin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batas jumlah izin yang sedang berjalan ({active_rule.max_concurrent_izin} izin) sudah tercapai. Silakan tunggu hingga ada yang kembali."
            )
            
    jabatan = user_data.jabatan.lower() if user_data.jabatan else None
    if jabatan:
        pending_izins_by_jabatan = [i for i in crud_izin.get_pending_izins(db) if i.user.jabatan.lower() == jabatan]
        
        if jabatan == "operator" and active_rule.max_izin_operator > 0 and len(pending_izins_by_jabatan) >= active_rule.max_izin_operator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batas izin untuk jabatan 'Operator' ({active_rule.max_izin_operator} izin) sudah tercapai. Silakan tunggu hingga ada yang kembali."
            )
        elif jabatan == "kapten" and active_rule.max_izin_kapten > 0 and len(pending_izins_by_jabatan) >= active_rule.max_izin_kapten:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batas izin untuk jabatan 'Kapten' ({active_rule.max_izin_kapten} izin) sudah tercapai. Silakan tunggu hingga ada yang kembali."
            )
        elif jabatan == "kasir" and active_rule.max_izin_kasir > 0 and len(pending_izins_by_jabatan) >= active_rule.max_izin_kasir:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batas izin untuk jabatan 'Kasir' ({active_rule.max_izin_kasir} izin) sudah tercapai. Silakan tunggu hingga ada yang kembali."
            )
        elif jabatan == "kasir lokal" and active_rule.max_izin_kasir_lokal > 0 and len(pending_izins_by_jabatan) >= active_rule.max_izin_kasir_lokal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batas izin untuk jabatan 'Kasir Lokal' ({active_rule.max_izin_kasir_lokal} izin) sudah tercapai. Silakan tunggu hingga ada yang kembali."
            )

    ip_address = get_request_ip(request)
    db_izin = crud_izin.create_izin_keluar(db=db, izin=izin, ip_keluar=ip_address)

    send_izin_notification(
        db=db,
        sender_uid=izin.user_uid,
        nama=user_data.nama,
        title="Ada Permintaan Izin Baru",
        body=f"Pengguna {user_data.nama} telah mengajukan izin keluar."
    )

    return db_izin


@router.put("/kembali/{no}", response_model=IzinSchema)
def izin_kembali(
    no: int,
    request: Request,
    db: Session = Depends(get_db)
):
    db_izin = crud_izin.get_izin(db, no=no)
    if db_izin is None:
        raise HTTPException(status_code=404, detail="Izin not found")

    if db_izin.status != "Pending":
        raise HTTPException(status_code=400, detail="Silahkan melakukan izin keluar terlebih dahulu.")

    active_rule = crud_izin_rules.get_active_izin_rule(db)
    if active_rule is None:
        raise HTTPException(status_code=404, detail="Aturan izin belum diatur.")
        
    ip_address = get_request_ip(request)
    db_izin_updated = crud_izin.update_izin_kembali(db=db, izin=db_izin, ip_kembali=ip_address, max_duration_seconds=active_rule.max_duration_seconds)

    send_izin_notification(
        db=db,
        sender_uid=db_izin_updated.user_uid,
        nama=db_izin_updated.user.nama,
        title="Pemberitahuan Izin Kembali",
        body=f"Pengguna {db_izin_updated.user.nama} telah kembali."
    )

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

    query = db.query(IzinModel).options(joinedload(IzinModel.user))

    query = query.filter(
        func.extract('year', IzinModel.tanggal) == year
    )

    if tanggal:
        try:
            filter_date = datetime.strptime(tanggal, '%Y-%m-%d').date()
            query = query.filter(func.date(IzinModel.tanggal) == filter_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format tanggal tidak valid. Gunakan format YYYY-MM-DD."
            )

    izins = query.all()
    return izins

@router.get("/overdue", response_model=List[IzinSchema])
def get_overdue_izins(db: Session = Depends(get_db)):
    overdue_izins = crud_izin.get_overdue_izins(db)
    return overdue_izins