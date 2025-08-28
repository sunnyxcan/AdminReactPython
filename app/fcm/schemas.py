# backend/app/fcm/schemas.py

from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.device.schemas import DeviceInfoResponse

# Skema untuk Token FCM
class FCMTokenBase(BaseModel):
    """Skema dasar untuk token FCM."""
    fcm_token: str

class FCMTokenCreate(FCMTokenBase):
    """Skema untuk membuat token FCM baru. Sekarang memerlukan 'user_uid' dan 'device_info'."""
    user_uid: str

class FCMToken(FCMTokenBase):
    """Skema untuk menampilkan token FCM."""
    user_uid: str
    device: Optional[str]
    createOn: date

    class Config:
        from_attributes = True