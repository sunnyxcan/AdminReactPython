# app/datacuti/models.py

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Cuti(Base):
    __tablename__ = "dataCuti"

    id = Column(Integer, primary_key=True, index=True)
    user_uid = Column(String, ForeignKey("users.uid"), nullable=False)
    tanggal_mulai = Column(Date, nullable=False)
    tanggal_akhir = Column(Date, nullable=False)
    masa_cuti = Column(Integer, nullable=False)
    jenis_cuti = Column(String, nullable=False)
    passport = Column(Boolean, nullable=True)
    keterangan = Column(Text, nullable=True)
    status = Column(String, default="Pending", nullable=False)
    tanggal = Column(Date, server_default=func.current_date(), nullable=False)
    by = Column(String, ForeignKey("users.uid"), nullable=True)
    masa_cuti_tambahan = Column(Integer, nullable=True)
    potongan_gaji_opsi = Column(String, nullable=True)
    detail_mix_cuti = Column(JSONB, nullable=True)
    edit_by = Column(String, ForeignKey("users.uid"), nullable=True)
    modified_on = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # ⭐ PERBAIKAN: Ubah back_populates dari "izin_cuti" menjadi "datacuti"
    user = relationship("User", back_populates="datacuti", foreign_keys=[user_uid])
    approved_by_user = relationship("User", back_populates="cuti_disetujui", foreign_keys=[by])
    edited_by_user = relationship("User", back_populates="cuti_diedit", foreign_keys=[edit_by])