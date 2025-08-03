# backend/app/users/models.py

from sqlalchemy import Column, Integer, String, Date, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship 
from app.core.database import Base

from app.roles.models import Role 

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
    createOn = Column("createOn", Date, server_default=func.current_date())
    modifiedOn = Column("modifiedOn", DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- TAMBAHKAN BARIS INI ---
    # Mendefinisikan relasi ke model Role
    role = relationship("Role", backref="users", lazy="joined")
    # -----------------------------

    fcm_tokens = relationship("FCMToken", back_populates="user", cascade="all, delete-orphan")