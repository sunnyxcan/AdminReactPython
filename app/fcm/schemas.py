# backend/app/fcm/schemas.py

from pydantic import BaseModel
from typing import Optional

# Skema untuk Token FCM
class FCMTokenBase(BaseModel):
    """Skema dasar untuk token FCM."""
    fcm_token: str

class FCMTokenCreate(FCMTokenBase):
    """Skema untuk membuat token FCM baru. Tidak memerlukan 'id'."""
    pass

class FCMToken(FCMTokenBase):
    """Skema untuk menampilkan token FCM, termasuk ID."""
    id: int
    user_uid: str

    class Config:
        from_attributes = True