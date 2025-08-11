# app/users/models.py

from sqlalchemy import Column, Integer, String, Date, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

from app.roles.models import Role
from app.datacuti.models import Cuti # Import model Cuti

class User(Base):
    __tablename__ = "users"

    uid = Column(String, primary_key=True, index=True, unique=True, nullable=False)
    fullname = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    jabatan = Column(String, nullable=True)
    imageUrl = Column("imageUrl", String, nullable=True)
    joinDate = Column("joinDate", Date, nullable=False)
    grupDate = Column("grupDate", Date, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    status = Column(String, nullable=False)
    tanggalAkhirCuti = Column("tanggalAkhirCuti", Date, nullable=True)
    no_passport = Column("no_passport", String, nullable=True)
    createOn = Column("createOn", Date, server_default=func.current_date())
    modifiedOn = Column("modifiedOn", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    role = relationship("Role", backref="users", lazy="joined")
    izins = relationship("Izin", back_populates="user")
    telats = relationship("DataTelat", foreign_keys="[DataTelat.user_uid]", back_populates="user")
    fcm_tokens = relationship("FCMToken", back_populates="user", cascade="all, delete-orphan")
    
    # ⭐ PERBAIKAN: Relasi untuk cuti yang diajukan oleh user ini. back_populates harus sama dengan nama properti di Cuti
    datacuti = relationship("Cuti", back_populates="user", foreign_keys="[Cuti.user_uid]")
    
    # ⭐ PERBAIKAN: Sesuaikan foreign_keys dengan nama kolom di model Cuti
    cuti_disetujui = relationship("Cuti", back_populates="approved_by_user", foreign_keys="[Cuti.by]")
    cuti_diedit = relationship("Cuti", back_populates="edited_by_user", foreign_keys="[Cuti.edit_by]")
    
    shift = relationship("Shift", foreign_keys="[Shift.user_uid]", back_populates="user")
    created_shifts = relationship("Shift", foreign_keys="[Shift.createdBy_uid]", back_populates="created_by_user")
    
    jobdesks = relationship("Jobdesk", foreign_keys="[Jobdesk.user_uid]", back_populates="user")
    created_jobdesks = relationship("Jobdesk", foreign_keys="[Jobdesk.createdBy_uid]", back_populates="created_by_user")
    modified_jobdesks = relationship("Jobdesk", foreign_keys="[Jobdesk.modifiedBy_uid]", back_populates="modified_by_user")

    created_list_job_categories = relationship("ListJobCategory", foreign_keys="[ListJobCategory.createdBy_uid]", back_populates="created_by_user")
    modified_list_job_categories = relationship("ListJobCategory", foreign_keys="[ListJobCategory.modifiedBy_uid]", back_populates="modified_by_user")