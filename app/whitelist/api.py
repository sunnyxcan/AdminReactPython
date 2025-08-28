# app/whitelist/api.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.core.database import get_db
from . import crud, schemas, models
from app.autentikasi.security import get_current_active_user
from app.users.models import User
from fastapi import Body

router = APIRouter()

@router.post("/", response_model=schemas.WhitelistIP, status_code=status.HTTP_201_CREATED)
def create_new_ip(
    ip_address: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_ip = crud.get_ip_by_address(db, ip_address=ip_address)
    if db_ip:
        raise HTTPException(status_code=400, detail="Alamat IP ini sudah ada di whitelist.")
    
    ip_data = schemas.WhitelistIPCreate(
        ip_address=ip_address, 
        created_by=current_user.uid
    )

    return crud.create_ip(db=db, ip_data=ip_data)

@router.get("/", response_model=List[schemas.WhitelistIP])
def read_all_ips(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # ⭐ PERBAIKAN: Gunakan .options(joinedload(...)) untuk memuat data creator dan editor
    ips = db.query(models.WhitelistIP).options(
        joinedload(models.WhitelistIP.creator),
        joinedload(models.WhitelistIP.editor)
    ).offset(skip).limit(limit).all()
    return ips

@router.delete("/{ip_address}")
def delete_ip_by_address(ip_address: str, db: Session = Depends(get_db)):
    db_ip = crud.get_ip_by_address(db, ip_address=ip_address)
    if db_ip is None:
        raise HTTPException(status_code=404, detail="Alamat IP tidak ditemukan di whitelist.")
    
    crud.delete_ip(db=db, db_ip=db_ip)
    return {"message": "Alamat IP berhasil dihapus."}

@router.put("/{ip_address}", response_model=schemas.WhitelistIP)
def update_existing_ip(
    ip_address: str, 
    ip_data: schemas.WhitelistIPUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_ip = crud.get_ip_by_address(db, ip_address=ip_address)
    if db_ip is None:
        raise HTTPException(status_code=404, detail="Alamat IP tidak ditemukan.")

    ip_data.edit_by = current_user.uid
    
    return crud.update_ip(db=db, db_ip=db_ip, ip_data=ip_data)