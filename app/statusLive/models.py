# app/statusLive/models.py

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class BackendStatus(Base):
    __tablename__ = "statusLive"

    id = Column(Integer, primary_key=True, index=True)
    last_active = Column(DateTime, server_default=func.now(), onupdate=func.now())