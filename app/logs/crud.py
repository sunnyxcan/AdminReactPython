# app/logs/crud.py

from sqlalchemy.orm import Session
from app.logs.models import Log as LogModel
from app.logs.schemas import LogCreate

def create_log(db: Session, log_data: LogCreate):
    """
    Membuat entri log baru di database.
    """
    db_log = LogModel(**log_data.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

# 🆕 Tambahkan fungsi untuk mengambil log
def get_logs(db: Session, skip: int = 0, limit: int = 100):
    """
    Mengambil semua entri log dari database.
    """
    return db.query(LogModel).offset(skip).limit(limit).all()