# backend/izin_rules/models.py
# (Tidak ada perubahan, kode ini sudah benar)
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class IzinRule(Base):
    __tablename__ = "izin_rules"

    id = Column(Integer, primary_key=True, index=True)
    max_daily_izin = Column(Integer, default=4, nullable=False)
    max_duration_seconds = Column(Integer, default=900, nullable=False)

    is_double_shift_rule = Column(Boolean, default=False, nullable=False)
    max_daily_double_shift = Column(Integer, default=None, nullable=True)
    double_shift_day = Column(String, default=None, nullable=True)
    
    max_concurrent_izin = Column(Integer, default=0, nullable=False)
    max_izin_operator = Column(Integer, default=0, nullable=False)
    max_izin_kapten = Column(Integer, default=0, nullable=False)
    max_izin_kasir = Column(Integer, default=0, nullable=False)
    max_izin_kasir_lokal = Column(Integer, default=0, nullable=False)

    createOn = Column(DateTime(timezone=True), server_default=func.now())
    modifiedOn = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<IzinRule(id={self.id}, max_daily_izin={self.max_daily_izin})>"