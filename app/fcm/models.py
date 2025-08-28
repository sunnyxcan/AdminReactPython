# backend/app/fcm/models.py

from sqlalchemy import Column, String, ForeignKey, Date, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class FCMToken(Base):
    """
    Model ini merepresentasikan tabel untuk menyimpan token FCM pengguna.
    Satu pengguna dapat memiliki banyak token untuk berbagai perangkat.
    """
    __tablename__ = "fcm_tokens"

    user_uid = Column(String, ForeignKey("users.uid"), nullable=False, index=True)
    fcm_token = Column(String, primary_key=True, index=True, nullable=False)
    device = Column(String, nullable=True)
    createOn = Column("createOn", Date, server_default=func.current_date())

    # Menambahkan relationship untuk akses balik
    user = relationship("User", back_populates="fcm_tokens")