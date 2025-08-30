# backend/app/users/crud.py

from sqlalchemy.orm import Session, joinedload
from app.users.models import User as UserModel
from app.users.schemas import UserCreate, UserUpdate
from typing import List, Optional

def get_user_by_uid(db: Session, user_uid: str):
    return db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.uid == user_uid).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(UserModel).options(joinedload(UserModel.role)).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    return db.query(UserModel).options(joinedload(UserModel.role)).filter(UserModel.email == email).first()

def create_user_by_admin(db: Session, user_data: UserCreate):
    db_user = UserModel(**user_data.model_dump())
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: UserModel, user_data: UserUpdate):
    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, db_user: UserModel):
    db.delete(db_user)
    db.commit()
    return