# app/datajobdesk/models.py

from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.users.models import User
from app.listjob.models import ListJobCategory
from app.datashift.models import Shift # Pastikan ini diimpor jika digunakan di tempat lain

# Tabel perantara untuk hubungan Many-to-Many antara Jobdesk dan ListJobCategory
kategoriJobdesk = Table(
    'kategoriJobdesk', Base.metadata,
    Column('jobdesk_no', Integer, ForeignKey('dataJobdesk.no'), primary_key=True),
    Column('listjob_category_id', Integer, ForeignKey('listJob.id'), primary_key=True)
)

class Jobdesk(Base):
    __tablename__ = "dataJobdesk"

    no = Column(Integer, primary_key=True, index=True)
    tanggal = Column(Date, nullable=False)
    user_uid = Column(String, ForeignKey("users.uid"), nullable=False)
    # listjob_category_id = Column(Integer, ForeignKey("listJob.id"), nullable=False) # Hapus baris ini

    shift_no = Column(Integer, ForeignKey("dataShift.no"), nullable=True)

    createdBy_uid = Column(String, ForeignKey("users.uid"), nullable=False)
    modifiedBy_uid = Column(String, ForeignKey("users.uid"), nullable=True)
    createdOn = Column("createdOn", DateTime(timezone=True), server_default=func.now())
    modifiedOn = Column("modifiedOn", DateTime(timezone=True), onupdate=func.now())

    # Relasi ORM
    user = relationship("User", foreign_keys=[user_uid], back_populates="jobdesks")
    created_by_user = relationship("User", foreign_keys=[createdBy_uid], back_populates="created_jobdesks")
    modified_by_user = relationship("User", foreign_keys=[modifiedBy_uid], back_populates="modified_jobdesks")

    # Relasi ke ListJobCategory (Many-to-Many)
    categories = relationship(
        "ListJobCategory",
        secondary=kategoriJobdesk,
        back_populates="jobdesks"
    )

    shift = relationship("Shift", back_populates="jobdesks")