# backend/app/datatelat/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DataTelat(Base):
    __tablename__ = "dataTelat"
    no = Column(Integer, primary_key=True, index=True, autoincrement=True)
    izin_no = Column(Integer, ForeignKey('dataIzin.no'), nullable=False) 
    user_uid = Column(String, ForeignKey('users.uid'), nullable=False)
    sanksi = Column(String, nullable=True)
    denda = Column(String, nullable=True)
    status = Column(String, default="Pending")
    keterangan = Column(String, nullable=True)
    jam = Column(String, nullable=True)
    by = Column(String, ForeignKey('users.uid'), nullable=True)
    createOn = Column(DateTime(timezone=True), server_default=func.now())
    modifiedOn = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Perbaikan: Sesuaikan relasi `izin` untuk menunjuk kembali ke `telats` di Izin model
    izin = relationship("Izin", back_populates="telats")
    user = relationship("User", foreign_keys=[user_uid], back_populates="telats")
    approved_by = relationship("User", foreign_keys=[by])