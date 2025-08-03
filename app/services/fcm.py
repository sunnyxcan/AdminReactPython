# backend/app/services/fcm.py

import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings
import logging

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

def send_fcm_message(token: str, title: str, body: str) -> bool:
    message = messaging.Message(
        data={
            "title": title,
            "body": body,
            "icon": "/vite.svg",
            "click_action": "/dashboard",
        },
        token=token,
    )
    try:
        response = messaging.send(message)
        logging.info(f"Berhasil mengirim pesan ke {token}: {response}")
        return True
    except Exception as e:
        logging.error(f"Gagal mengirim pesan ke {token}: {e}")
        return False

# Fungsi send_notification_with_data tidak lagi diperlukan. Anda bisa menghapusnya.

def subscribe_to_topic(tokens: list, topic: str):
    try:
        response = messaging.subscribe_to_topic(tokens, topic)
        if response.success_count > 0:
            logging.info(f"Berhasil berlangganan {response.success_count} token ke topik {topic}")
        if response.failure_count > 0:
            logging.error(f"Gagal berlangganan {response.failure_count} token ke topik {topic}: {response.errors}")
    except Exception as e:
        logging.error(f"Error saat mencoba berlangganan token ke topik {topic}: {e}")