# backend/app/datatelat/schemas.py

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.dataizin.schemas import Izin as IzinSchema
from app.users.schemas import User as UserSchema

class DataTelatBase(BaseModel):
    izin_no: int
    user_uid: str
    sanksi: Optional[str] = None
    denda: Optional[str] = None
    status: Optional[str] = "Pending"
    keterangan: Optional[str] = None
    jam: Optional[str] = None
    by: Optional[str] = None

class DataTelatCreate(DataTelatBase):
    pass

class DataTelatUpdate(DataTelatBase):
    izin_no: Optional[int] = None
    user_uid: Optional[str] = None
    sanksi: Optional[str] = None
    denda: Optional[str] = None
    status: Optional[str] = None
    keterangan: Optional[str] = None
    jam: Optional[str] = None
    by: Optional[str] = None

class DataTelat(DataTelatBase):
    no: int
    createOn: datetime
    modifiedOn: datetime
    
    izin: Optional[IzinSchema] = None
    user: Optional[UserSchema] = None
    approved_by: Optional[UserSchema] = None

    model_config = ConfigDict(from_attributes=True)