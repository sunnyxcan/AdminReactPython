# app/whitelist/crud.py

from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional
from datetime import datetime, timezone

def get_ips(db: Session, skip: int = 0, limit: int = 100) -> List[models.WhitelistIP]:
    """Mengambil daftar semua IP yang di-whitelist."""
    return db.query(models.WhitelistIP).offset(skip).limit(limit).all()

def get_ip_by_address(db: Session, ip_address: str) -> Optional[models.WhitelistIP]:
    """Mengambil satu IP berdasarkan alamatnya."""
    return db.query(models.WhitelistIP).filter(models.WhitelistIP.ip_address == ip_address).first()

def create_ip(db: Session, ip_data: schemas.WhitelistIPCreate) -> models.WhitelistIP:
    """Menambahkan IP baru ke whitelist."""
    db_ip = models.WhitelistIP(
        ip_address=ip_data.ip_address,
        created_by=ip_data.created_by,
        createOn=datetime.now(),
        tanggal=datetime.now(timezone.utc)
    )
    db.add(db_ip)
    db.commit()
    db.refresh(db_ip)
    return db_ip

def delete_ip(db: Session, db_ip: models.WhitelistIP):
    """Menghapus IP dari whitelist."""
    db.delete(db_ip)
    db.commit()

def update_ip(db: Session, db_ip: models.WhitelistIP, ip_data: schemas.WhitelistIPUpdate) -> models.WhitelistIP:
    """Memperbarui alamat IP dan editor."""
    update_data = ip_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ip, key, value)
    
    db.add(db_ip)
    db.commit()
    db.refresh(db_ip)
    return db_ip