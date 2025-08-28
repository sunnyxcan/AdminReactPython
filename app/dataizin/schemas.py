# backend/app/dataizin/schemas.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.users.schemas import User

class IzinBase(BaseModel):
    user_uid: str

class IzinCreate(IzinBase):
    pass

class IzinUpdate(BaseModel):
    status: Optional[str] = None
    jamKembali: Optional[datetime] = None
    ipKembali: Optional[str] = None
    durasi: Optional[str] = None

class Izin(IzinBase):
    no: int
    tanggal: datetime
    jamKeluar: Optional[datetime] = None
    ipKeluar: Optional[str] = None
    jamKembali: Optional[datetime] = None
    ipKembali: Optional[str] = None
    durasi: Optional[str] = None
    status: str
    createOn: datetime
    modifiedOn: datetime
    
    user: Optional[User] = None

    model_config = ConfigDict(from_attributes=True)