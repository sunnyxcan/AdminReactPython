# backend/app/services/fcm.py

from firebase_admin import messaging
import logging

def send_fcm_message(token: str, title: str, body: str, click_action_url: str) -> bool:
    """
    Mengirim pesan FCM ke token tertentu dan menangani error.
    Mengembalikan True jika berhasil, False jika token tidak valid.
    """
    message = messaging.Message(
        data={
            "title": title,
            "body": body,
            "icon": "/vite.svg",
            "url": click_action_url,  # ✨ Menggunakan 'url' sebagai key
        },
        token=token,
    )
    try:
        response = messaging.send(message)
        logging.info(f"Berhasil mengirim pesan ke token '{token}': {response}")
        return True
    except messaging.UnregisteredError:
        logging.error(f"Gagal mengirim pesan ke '{token}': Token tidak terdaftar atau tidak valid.")
        return False
    except Exception as e:
        logging.error(f"Gagal mengirim pesan ke '{token}': {e}")
        return False

def subscribe_to_topic(tokens: list, topic: str):
    try:
        response = messaging.subscribe_to_topic(tokens, topic)
        if response.success_count > 0:
            logging.info(f"Berhasil berlangganan {response.success_count} token ke topik {topic}")
        if response.failure_count > 0:
            logging.error(f"Gagal berlangganan {response.failure_count} token ke topik {topic}: {response.errors}")
    except Exception as e:
        logging.error(f"Error saat mencoba berlangganan token ke topik {topic}: {e}")