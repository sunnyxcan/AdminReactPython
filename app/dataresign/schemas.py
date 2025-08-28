# app/dataresign/schemas.py

from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Optional
from app.users.schemas import User

class DataResignBase(BaseModel):
    tanggal_pengajuan: date
    tanggal_resign: Optional[date] = None
    keterangan: str = Field(..., description="Keterangan pengajuan resign, tidak boleh kosong.")
    status: Optional[str] = "Pending"
    tanggal: Optional[date] = None

class DataResignCreate(DataResignBase):
    user_uid: str
    created_by: Optional[str] = None

class DataResignUpdate(BaseModel):
    tanggal_pengajuan: Optional[date] = None
    tanggal_resign: Optional[date] = None
    keterangan: Optional[str] = None
    status: Optional[str] = None
    edit_by: Optional[str] = None

class DataResignApprove(BaseModel):
    tanggal: Optional[date] = None
    status: str
    by: Optional[str] = None

class DataResignInDB(DataResignBase):
    id: int
    user_uid: str
    by: Optional[str] = None
    created_by: Optional[str] = None
    edit_by: Optional[str] = None
    createOn: datetime
    modified_on: datetime

    model_config = ConfigDict(from_attributes=True)

class DataResign(DataResignInDB):
    user: Optional[User] = None
    approved_by_user: Optional[User] = None
    created_by_user: Optional[User] = None
    edited_by_user: Optional[User] = None

    model_config = ConfigDict(from_attributes=True)