# app/statusLive/api.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.statusLive import models as backend_models
from app.statusLive import schemas as backend_schemas
from datetime import datetime
from zoneinfo import ZoneInfo # Ini modul baru yang perlu diimpor

router = APIRouter()

# Tentukan zona waktu untuk GMT+7
JAKARTA_TZ = ZoneInfo("Asia/Jakarta") # Contoh zona waktu GMT+7

@router.get("/status", response_model=backend_schemas.BackendStatus)
def get_statusLive(db: Session = Depends(get_db)):
    """
    Mengambil status terakhir dari backend dari database.
    """
    status = db.query(backend_models.BackendStatus).first()
    if not status:
        new_status = backend_models.BackendStatus()
        db.add(new_status)
        db.commit()
        db.refresh(new_status)
        status = new_status
    
    # Konversi waktu 'last_active' ke GMT+7 sebelum mengirimkannya
    # Pastikan last_active memiliki informasi timezone (seperti UTC)
    # Jika tidak, Anda perlu membuatnya sadar akan timezone (timezone-aware)
    if status.last_active:
        utc_datetime = status.last_active.replace(tzinfo=ZoneInfo("UTC"))
        status.last_active = utc_datetime.astimezone(JAKARTA_TZ)

    return status

@router.put("/update-active")
def update_statusLive(db: Session = Depends(get_db)):
    """
    Memperbarui timestamp `last_active` di database.
    """
    status = db.query(backend_models.BackendStatus).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status entry not found.")
    
    status.last_active = datetime.utcnow()
    db.commit()
    db.refresh(status)
    return {"message": "Status updated successfully"}