# backend/app/roles/models.py

# Masukkan kode class Role yang kamu berikan di sini
from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    createOn = Column("createOn", DateTime(timezone=True), server_default=func.now())
    modifiedOn = Column("modifiedOn", DateTime(timezone=True), onupdate=func.now())