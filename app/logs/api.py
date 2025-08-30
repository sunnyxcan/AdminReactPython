# app/logs/api.py

from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.logs import crud as log_crud
from app.logs import schemas as log_schemas
from app.users import models as user_models # Diperlukan untuk Depends
from app.autentikasi import security as auth_security # Diperlukan untuk Depends

router = APIRouter()

logger = logging.getLogger(__name__)

# Endpoint untuk membuat log baru
@router.post("/", response_model=log_schemas.Log, status_code=status.HTTP_201_CREATED)
async def create_new_log(
    log_data: log_schemas.LogCreate,
    db: Session = Depends(get_db),
    # Anda mungkin ingin melindungi endpoint ini agar hanya bisa diakses oleh pengguna terotentikasi.
    # Misalnya:
    # current_user: user_models.User = Depends(auth_security.get_current_active_user)
):
    """
    Membuat entri log baru di database.
    """
    try:
        new_log = log_crud.create_log(db=db, log_data=log_data)
        logger.info(f"Log baru berhasil dibuat: {new_log.action} - {new_log.details}")
        return new_log
    except Exception as e:
        logger.error(f"Gagal membuat log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal membuat log: {e}"
        )

# Endpoint untuk mengambil semua log (opsional, untuk halaman admin)
@router.get("/", response_model=List[log_schemas.Log])
async def read_logs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Mengambil daftar semua log.
    """
    logs = log_crud.get_logs(db, skip=skip, limit=limit)
    return logs