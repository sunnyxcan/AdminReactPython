# app/dataresign/models.py

from sqlalchemy import Column, Integer, String, Date, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class DataResign(Base):
    __tablename__ = "dataResign"

    id = Column(Integer, primary_key=True, index=True)
    user_uid = Column(String, ForeignKey("users.uid"), nullable=False)
    tanggal_pengajuan = Column(Date, nullable=False)
    tanggal_resign = Column("tanggal_resign", Date, nullable=True)
    keterangan = Column(Text, nullable=False) # ⭐ Diubah menjadi nullable=False
    status = Column(String, default="Pending", nullable=False)
    tanggal = Column(Date, server_default=func.current_date(), nullable=False) # Ini adalah tanggal_disetujui
    by = Column(String, ForeignKey("users.uid"), nullable=True) # Ini adalah approved_by
    created_by = Column(String, ForeignKey("users.uid"), nullable=True)
    edit_by = Column(String, ForeignKey("users.uid"), nullable=True)
    createOn = Column("createOn", DateTime, server_default=func.now())
    modified_on = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Menambahkan relasi ke tabel User
    user = relationship("User", foreign_keys=[user_uid], back_populates="resignations")
    approved_by_user = relationship("User", foreign_keys=[by], back_populates="approved_resignations")
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="created_resignations")
    edited_by_user = relationship("User", foreign_keys=[edit_by], back_populates="edited_resignations")