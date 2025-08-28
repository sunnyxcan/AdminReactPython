# app/whitelist/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class WhitelistIP(Base):
    __tablename__ = "whitelist_ip"

    no = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tanggal = Column(DateTime(timezone=True), default=func.now())
    ip_address = Column(String, unique=True, index=True, nullable=False)
    created_by = Column(String, ForeignKey("users.uid"), nullable=True)
    edit_by = Column(String, ForeignKey("users.uid"), nullable=True)
    createOn = Column(DateTime(timezone=True), server_default=func.now())
    modifiedOn = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Tetapkan relasi dengan User
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_whitelist_ips")
    editor = relationship("User", foreign_keys=[edit_by], back_populates="edited_whitelist_ips")