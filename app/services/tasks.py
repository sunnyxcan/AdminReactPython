# backend/app/services/tasks.py

import logging
from app.fcm import crud as fcm_crud
from app.services.fcm import send_fcm_message
from app.users import crud as crud_user
from sqlalchemy.orm import Session

def send_izin_notification_async(db: Session, sender_uid: str, nama: str, title: str, body: str, click_action_url: str):
    """
    Fungsi ini akan dijalankan dalam thread terpisah untuk mengirim notifikasi FCM.
    """
    try:
        all_users = crud_user.get_users(db)
        target_users_uids = [user.uid for user in all_users if user.uid != sender_uid]
        
        for target_user_uid in target_users_uids:
            target_fcm_tokens = fcm_crud.get_fcm_tokens_by_user(db, user_uid=target_user_uid)
            for token in target_fcm_tokens:
                is_sent = send_fcm_message(
                    token=token, 
                    title=title,
                    body=body,
                    click_action_url=click_action_url,  # ✨ Meneruskan URL di sini
                )
                if not is_sent:
                    logging.warning(f"Menghapus token yang tidak valid dari database: {token}")
                    fcm_crud.delete_fcm_token(db, fcm_token=token)
    finally:
        db.close()