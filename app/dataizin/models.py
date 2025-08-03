# backend/app/dataizin/models.py

from sqlalchemy import Column, Integer, String, Date, DateTime, func, ForeignKey
from app.core.database import Base

class Izin(Base):
    __tablename__ = "dataIzin"
    no = Column(Integer, primary_key=True, index=True)
    user_uid = Column(String, ForeignKey('users.uid'), nullable=False)
    nama = Column(String, nullable=False)
    jabatan = Column(String, nullable=True)
    tanggal = Column(Date, default=func.current_date())

    jamKeluar = Column(DateTime(timezone=True), nullable=True)
    ipKeluar = Column(String, nullable=True)

    jamKembali = Column(DateTime(timezone=True), nullable=True)
    ipKembali = Column(String, nullable=True)

    durasi = Column(String, nullable=True)
    status = Column(String, default="Pending")

    createOn = Column(DateTime(timezone=True), server_default=func.now())
    modifiedOn = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())