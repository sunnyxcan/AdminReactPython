# backend/app/fcm/models.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class FCMToken(Base):
    """
    Model ini merepresentasikan tabel untuk menyimpan token FCM pengguna.
    Satu pengguna dapat memiliki banyak token untuk berbagai perangkat.
    """
    __tablename__ = "fcm_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_uid = Column(String, ForeignKey("users.uid"), nullable=False)
    fcm_token = Column(String, unique=True, index=True, nullable=False)

    # Menambahkan relationship untuk akses balik
    user = relationship("User", back_populates="fcm_tokens")