# backend/app/dataizin/api.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.dataizin.schemas import Izin as IzinSchema, IzinCreate
from app.dataizin import crud as crud_izin
from app.services.fcm import send_fcm_message
from app.fcm import crud as fcm_crud
from app.utils.ip_utils import get_request_ip
import logging
from app.users import crud as crud_user # <-- Impor crud user

router = APIRouter()

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
    db_izin = crud_izin.create_izin_keluar(db=db, izin=izin, ip_keluar=ip_address)

    # Ambil UID dari pengguna yang mengajukan izin
    user_pengirim_uid = izin.user_uid

    # Ambil semua user kecuali user pengirim
    all_users = crud_user.get_users(db)
    target_users = [user.uid for user in all_users if user.uid != user_pengirim_uid]

    # Kirim notifikasi ke semua user yang ditargetkan
    for target_user_uid in target_users:
        target_fcm_tokens = fcm_crud.get_fcm_tokens_by_user(db, user_uid=target_user_uid)
        for token in target_fcm_tokens:
            try:
                send_fcm_message(
                    token=token,
                    title="Ada Permintaan Izin Baru",
                    body=f"Pengguna {izin.nama} telah mengajukan izin keluar."
                )
                logging.info(f"Notifikasi izin keluar berhasil dikirim ke token: {token}")
            except Exception as e:
                logging.error(f"Gagal mengirim notifikasi izin keluar ke token {token}: {e}")

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

    ip_address = get_request_ip(request)
    db_izin_updated = crud_izin.update_izin_kembali(db=db, izin=db_izin, ip_kembali=ip_address)

    # Ambil UID dari pengguna yang kembali
    user_pengirim_uid = db_izin_updated.user_uid

    # Ambil semua user kecuali user pengirim
    all_users = crud_user.get_users(db)
    target_users = [user.uid for user in all_users if user.uid != user_pengirim_uid]

    # Kirim notifikasi ke semua user yang ditargetkan
    for target_user_uid in target_users:
        target_fcm_tokens = fcm_crud.get_fcm_tokens_by_user(db, user_uid=target_user_uid)
        for token in target_fcm_tokens:
            try:
                send_fcm_message(
                    token=token,
                    title="Pemberitahuan Izin Kembali",
                    body=f"Pengguna {db_izin_updated.nama} telah kembali."
                )
                logging.info(f"Notifikasi izin kembali berhasil dikirim ke token: {token}")
            except Exception as e:
                logging.error(f"Gagal mengirim notifikasi izin kembali ke token {token}: {e}")

    return db_izin_updated