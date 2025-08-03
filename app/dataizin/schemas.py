# backend/app/dataizin/schemas.py

from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

class IzinBase(BaseModel):
    user_uid: str
    nama: str
    jabatan: Optional[str] = None

class IzinCreate(IzinBase):
    pass

class IzinUpdate(BaseModel):
    status: str
    jamKembali: Optional[datetime] = None
    ipKembali: Optional[str] = None
    durasi: Optional[str] = None

class Izin(IzinBase):
    no: int
    tanggal: date
    jamKeluar: Optional[datetime] = None
    ipKeluar: Optional[str] = None
    jamKembali: Optional[datetime] = None
    ipKembali: Optional[str] = None
    durasi: Optional[str] = None
    status: str
    createOn: datetime
    modifiedOn: datetime

    model_config = ConfigDict(from_attributes=True)