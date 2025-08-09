# backend/app/dataizin/models.py

from sqlalchemy import Column, Integer, String, Date, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from app.core.database import Base

class Izin(Base):
    __tablename__ = "dataIzin"
    no = Column(Integer, primary_key=True, index=True)
    user_uid = Column(String, ForeignKey('users.uid'), nullable=False)
    tanggal = Column(Date, default=func.current_date())
    jamKeluar = Column(DateTime, nullable=True)
    ipKeluar = Column(String, nullable=True)
    jamKembali = Column(DateTime, nullable=True)
    ipKembali = Column(String, nullable=True)
    durasi = Column(String, nullable=True)
    status = Column(String, default="Pending")
    createOn = Column(DateTime(timezone=True), server_default=func.now())
    modifiedOn = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="izins")
    telat = relationship("DataTelat", uselist=False, back_populates="izin")

    def __repr__(self):
        return f"<Izin(no={self.no}, user_uid='{self.user_uid}', tanggal='{self.tanggal}')>"

    @classmethod
    def create_dynamic_table_model(cls, table_name: str):
        DynamicBase = declarative_base(cls=Base, metadata=Base.metadata)

        class DynamicDataIzin(DynamicBase):
            __tablename__ = table_name
            __table_args__ = ({'extend_existing': True},) 

            no = Column(Integer, primary_key=True, index=True)
            user_uid = Column(String, ForeignKey('users.uid'), nullable=False)
            tanggal = Column(Date, default=func.current_date())
            jamKeluar = Column(DateTime, nullable=True)
            ipKeluar = Column(String, nullable=True)
            jamKembali = Column(DateTime, nullable=True)
            ipKembali = Column(String, nullable=True)
            durasi = Column(String, nullable=True)
            status = Column(String, default="Pending")
            createOn = Column(DateTime(timezone=True), server_default=func.now())
            modifiedOn = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

            user = relationship("User", uselist=False)

            def __repr__(self):
                return f"<DynamicDataIzin(no={self.no}, user_uid='{self.user_uid}', tanggal='{self.tanggal}', table='{self.__tablename__}')>"

        return DynamicDataIzin