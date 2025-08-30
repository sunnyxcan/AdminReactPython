# app/logs/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    entity_name = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    details = Column(String, nullable=True)
    
    # 🆕 Kolom baru untuk informasi IP dan perangkat
    ip_address = Column(String, nullable=True)
    device_info = Column(JSON, nullable=True) # Gunakan tipe JSON untuk menyimpan informasi terstruktur
    
    created_by = Column(String, ForeignKey("users.uid"), nullable=True)
    
    createOn = Column("createOn", DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", back_populates="created_logs", foreign_keys=[created_by])