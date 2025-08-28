# backend/app/fcm/crud.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.fcm.models import FCMToken as FCMTokenModel
from typing import List
import json  # 👈 Tambahkan import ini

def create_fcm_token(db: Session, user_uid: str, fcm_token: str, device_info: dict):
    """
    Membuat entri token FCM baru atau memperbarui user_uid jika token sudah ada.
    """
    try:
        # Serialisasi dict device_info menjadi JSON string
        device_info_json = json.dumps(device_info)

        # Coba ambil token yang sudah ada menggunakan fcm_token sebagai primary key
        existing_token = db.get(FCMTokenModel, fcm_token)
        if existing_token:
            # Perbarui user_uid dan device_info jika berbeda
            if existing_token.user_uid != user_uid:
                existing_token.user_uid = user_uid
            existing_token.device = device_info_json  # 👈 Gunakan JSON string
            db.commit()
            db.refresh(existing_token)
            return existing_token

        # Jika token belum ada, buat entri baru
        db_fcm_token = FCMTokenModel(
            user_uid=user_uid, 
            fcm_token=fcm_token,
            device=device_info_json  # 👈 Gunakan JSON string
        )
        db.add(db_fcm_token)
        db.commit()
        db.refresh(db_fcm_token)
        
        return db_fcm_token
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Gagal menyimpan token.")

def get_fcm_tokens_by_user(db: Session, user_uid: str) -> List[str]:
    """
    Mengambil semua token FCM untuk pengguna tertentu.
    """
    fcm_tokens = db.query(FCMTokenModel).filter(FCMTokenModel.user_uid == user_uid).all()
    return [token.fcm_token for token in fcm_tokens]
    
def delete_fcm_token(db: Session, fcm_token: str):
    """
    Menghapus token FCM yang tidak valid dari database.
    """
    db_token = db.get(FCMTokenModel, fcm_token)
    if db_token:
        db.delete(db_token)
        db.commit()
        return True
    return False