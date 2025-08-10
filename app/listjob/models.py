# app/listjob/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.users.models import User

class ListJobCategory(Base):
    __tablename__ = "listJob"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String, unique=True, index=True, nullable=False)
    deskripsi = Column(String, nullable=True)

    createdBy_uid = Column(String, ForeignKey("users.uid"), nullable=False)
    modifiedBy_uid = Column(String, ForeignKey("users.uid"), nullable=True)

    createOn = Column("createOn", DateTime(timezone=True), server_default=func.now())
    modifiedOn = Column("modifiedOn", DateTime(timezone=True), onupdate=func.now())

    # Relasi balik dari Jobdesk (Many-to-Many)
    jobdesks = relationship("Jobdesk", secondary="kategoriJobdesk", back_populates="categories")

    # Relasi ke model User
    created_by_user = relationship("User", foreign_keys=[createdBy_uid], back_populates="created_list_job_categories")
    modified_by_user = relationship("User", foreign_keys=[modifiedBy_uid], back_populates="modified_list_job_categories")