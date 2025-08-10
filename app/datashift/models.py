# app/datashift/models.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime # Tambahkan DateTime di sini karena Jobdesk menggunakannya
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Shift(Base):
    __tablename__ = "dataShift" # Nama tabel di database

    no = Column(Integer, primary_key=True, index=True)
    user_uid = Column(String, ForeignKey('users.uid'), nullable=False)
    
    tanggalMulai = Column(Date, nullable=False)
    tanggalAkhir = Column(Date, nullable=False)
    
    jamMasuk = Column(String, nullable=True)
    jamPulang = Column(String, nullable=True)
    
    jamMasukDoubleShift = Column(String, nullable=True)
    jamPulangDoubleShift = Column(String, nullable=True)
    
    jadwal = Column(String, nullable=True)
    keterangan = Column(String, nullable=True)
    
    createdBy_uid = Column(String, ForeignKey('users.uid'), nullable=False) 
    
    createOn = Column(Date, server_default=func.now()) 
    modifiedOn = Column(Date, server_default=func.now(), onupdate=func.now()) 

    user = relationship("User", back_populates="shift", foreign_keys=[user_uid])
    created_by_user = relationship("User", foreign_keys=[createdBy_uid], back_populates="created_shifts")

    # --- Tambahkan ini untuk relasi ke Jobdesk ---
    jobdesks = relationship("Jobdesk", back_populates="shift") # Tambahkan relasi ini
    # --- Akhir penambahan ---

    def __repr__(self):
        return f"<Shift(no={self.no}, user_uid='{self.user_uid}', tanggalMulai='{self.tanggalMulai}')>"