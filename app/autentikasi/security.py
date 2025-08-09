# app/autentikasi/security.py

import firebase_admin
from firebase_admin import auth
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.users.models import User
import datetime
import logging

logger = logging.getLogger(__name__)

# Kita akan menggunakan skema HTTPBearer untuk mengambil token dari header
security_scheme = HTTPBearer()

def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    """
    Dependensi untuk memverifikasi token Firebase ID dari header 'Authorization'.
    """
    token = credentials.credentials
    try:
        # Panggil fungsi verifikasi Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get('uid')
        if not uid:
            raise ValueError("UID not found in token.")
        return {'uid': uid}
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token otentikasi tidak valid.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error during Firebase token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Terjadi kesalahan saat memverifikasi token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    token_data: dict = Depends(verify_firebase_token), # Gunakan Depends di sini
    db: Session = Depends(get_db)
) -> User:
    """
    Mengambil pengguna dari database berdasarkan UID yang diverifikasi, dan memeriksa statusnya.
    """
    user_uid = token_data.get('uid')
    if not user_uid:
        raise HTTPException(status_code=400, detail="UID not found in token data.")
    
    user_in_db = db.query(User).filter(User.uid == user_uid).first()
    
    if not user_in_db:
        logger.warning(f"User with UID {user_uid} not found in database.")
        raise HTTPException(status_code=404, detail="User not found in database.")
    
    # Logika pemeriksaan status pengguna
    if user_in_db.status == "Nonaktif":
        raise HTTPException(status_code=403, detail="Akun Anda nonaktif.")

    if user_in_db.status == "Cuti":
        # Perbaiki cara mengonversi tanggal
        if not user_in_db.tanggalAkhirCuti:
            raise HTTPException(status_code=403, detail="Status cuti tidak lengkap.")
        
        try:
            cuti_end_date_obj = datetime.datetime.strptime(str(user_in_db.tanggalAkhirCuti), '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=500, detail="Format tanggal cuti tidak valid.")

        today_date = datetime.date.today()
        if today_date <= cuti_end_date_obj:
            login_possible_date = cuti_end_date_obj + datetime.timedelta(days=1)
            raise HTTPException(status_code=403, detail=f"Anda sedang cuti sampai {cuti_end_date_obj.strftime('%Y-%m-%d')}.")
        else:
            user_in_db.status = "Aktif"
            user_in_db.tanggalAkhirCuti = None
            db.add(user_in_db)
            db.commit()
            db.refresh(user_in_db)
            logger.info(f"Status user {user_uid} diubah menjadi Aktif.")

    return user_in_db