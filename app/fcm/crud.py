# backend/app/fcm/crud.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.fcm.models import FCMToken as FCMTokenModel
from typing import List
# Hapus impor subscribe_to_topic

def create_fcm_token_and_subscribe(db: Session, user_uid: str, fcm_token: str):
    """
    Membuat entri token FCM baru dan tidak lagi berlangganan ke topik apa pun.
    """
    try:
        existing_token = db.query(FCMTokenModel).filter(FCMTokenModel.fcm_token == fcm_token).first()
        if existing_token:
            if existing_token.user_uid != user_uid:
                existing_token.user_uid = user_uid
                db.commit()
                db.refresh(existing_token)
            return existing_token

        db_fcm_token = FCMTokenModel(user_uid=user_uid, fcm_token=fcm_token)
        db.add(db_fcm_token)
        db.commit()
        db.refresh(db_fcm_token)
        
        return db_fcm_token
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"FCM token already exists for this user/device.")

def get_fcm_tokens_by_user(db: Session, user_uid: str) -> List[str]:
    """
    Mengambil semua token FCM untuk pengguna tertentu.
    """
    fcm_tokens = db.query(FCMTokenModel).filter(FCMTokenModel.user_uid == user_uid).all()
    return [token.fcm_token for token in fcm_tokens]