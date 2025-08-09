# backend/izin_rules/crud.py
# (Tidak ada perubahan, kode ini sudah benar)
from sqlalchemy.orm import Session
from . import models, schemas
from datetime import date
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_izin_rule(db: Session, rule_id: int):
    return db.query(models.IzinRule).filter(models.IzinRule.id == rule_id).first()

def get_izin_rules(db: Session, skip: int = 0, limit: int = 100) -> List[models.IzinRule]:
    return db.query(models.IzinRule).offset(skip).limit(limit).all()

def get_active_izin_rule(db: Session) -> Optional[models.IzinRule]:
    rule = db.query(models.IzinRule).first()
    return rule

def create_izin_rule(db: Session, rule: schemas.IzinRuleCreate):
    existing_rule = db.query(models.IzinRule).first()
    if existing_rule:
        logger.warning("Attempted to create a new IzinRule, but one already exists. Returning existing rule.")
        return existing_rule

    # Menggunakan model_dump() untuk mendapatkan semua field dari schema, termasuk yang baru
    db_izin_rule = models.IzinRule(**rule.model_dump())
    db.add(db_izin_rule)
    db.commit()
    db.refresh(db_izin_rule)
    logger.info(f"New IzinRule created with ID: {db_izin_rule.id}")
    return db_izin_rule

def update_izin_rule(db: Session, rule_id: int, rule_update: schemas.IzinRuleCreate):
    db_izin_rule = db.query(models.IzinRule).filter(models.IzinRule.id == rule_id).first()
    if not db_izin_rule:
        return None
    # Menggunakan model_dump(exclude_unset=True) untuk hanya memperbarui field yang disediakan
    for key, value in rule_update.model_dump(exclude_unset=True).items():
        setattr(db_izin_rule, key, value)
    db.add(db_izin_rule)
    db.commit()
    db.refresh(db_izin_rule)
    logger.info(f"IzinRule with ID: {db_izin_rule.id} updated.")
    return db_izin_rule

def delete_izin_rule(db: Session, rule_id: int):
    db_izin_rule = db.query(models.IzinRule).filter(models.IzinRule.id == rule_id).first()
    if db_izin_rule:
        db.delete(db_izin_rule)
        db.commit()
        logger.info(f"IzinRule with ID: {rule_id} deleted.")
        return True
    logger.warning(f"Attempted to delete IzinRule with ID: {rule_id}, but it was not found.")
    return False