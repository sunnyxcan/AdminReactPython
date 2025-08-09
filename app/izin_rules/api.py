# backend/izin_rules/api.py
# (Tidak ada perubahan, kode ini sudah benar)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.database import get_db
from . import crud, schemas, models
from datetime import date

router = APIRouter()

@router.get("/", response_model=List[schemas.IzinRuleInDB])
def read_izin_rules(db: Session = Depends(get_db)):
    """
    Mengambil daftar semua aturan izin. Karena hanya satu aturan yang diizinkan, ini akan mengembalikan daftar berisi 0 atau 1 aturan.
    """
    rules = crud.get_izin_rules(db)
    return rules

@router.get("/{rule_id}", response_model=schemas.IzinRuleInDB)
def read_izin_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Mengambil detail aturan izin berdasarkan ID.
    """
    db_rule = crud.get_izin_rule(db, rule_id=rule_id)
    if db_rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Izin Rule not found")
    return db_rule

@router.post("/", response_model=schemas.IzinRuleInDB, status_code=status.HTTP_201_CREATED)
def create_new_izin_rule(rule: schemas.IzinRuleCreate, db: Session = Depends(get_db)):
    """
    Membuat aturan izin baru. Hanya satu aturan yang diizinkan. Jika sudah ada, akan mengembalikan aturan yang sudah ada.
    """
    existing_rule = db.query(models.IzinRule).first()
    if existing_rule:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Izin Rule already exists. Only one rule is allowed.")
    return crud.create_izin_rule(db=db, rule=rule)


@router.put("/{rule_id}", response_model=schemas.IzinRuleInDB)
def update_existing_izin_rule(rule_id: int, rule: schemas.IzinRuleCreate, db: Session = Depends(get_db)):
    """
    Memperbarui aturan izin yang sudah ada berdasarkan ID.
    """
    db_rule = crud.update_izin_rule(db, rule_id=rule_id, rule_update=rule)
    if db_rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Izin Rule not found")
    return db_rule

@router.delete("/{rule_id}", status_code=status.HTTP_200_OK, response_model=Dict[str, str])
def delete_existing_izin_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Menghapus aturan izin berdasarkan ID.
    """
    success = crud.delete_izin_rule(db, rule_id=rule_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Izin Rule not found")
    return {"message": "Izin Rule deleted successfully"}