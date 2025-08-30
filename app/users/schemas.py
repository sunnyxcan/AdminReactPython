# app/users/schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from app.roles.schemas import Role

class UserBase(BaseModel):
    uid: str
    fullname: str
    nickname: Optional[str] = None
    gender: Optional[str] = None
    jabatan: Optional[str] = None
    imageUrl: Optional[str] = Field(None, alias="imageUrl")
    email: str
    status: str
    joinDate: date
    grupDate: date
    tanggalAkhirCuti: Optional[date] = None
    no_passport: Optional[str] = None

class UserCreate(BaseModel):
    uid: str
    fullname: str
    nickname: Optional[str] = None
    gender: Optional[str] = None
    jabatan: Optional[str] = None
    imageUrl: Optional[str] = Field(None, alias="imageUrl")
    email: str
    role_id: int
    status: str
    joinDate: date
    grupDate: date
    tanggalAkhirCuti: Optional[date] = None
    no_passport: Optional[str] = None

class UserCreateByAdmin(BaseModel):
    fullname: str
    nickname: Optional[str] = None
    gender: Optional[str] = None
    jabatan: Optional[str] = None
    imageUrl: Optional[str] = Field(None, alias="imageUrl")
    email: str
    role_id: int
    status: str
    joinDate: date
    grupDate: date
    tanggalAkhirCuti: Optional[date] = None
    no_passport: Optional[str] = None
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    nickname: Optional[str] = None
    gender: Optional[str] = None
    jabatan: Optional[str] = None
    imageUrl: Optional[str] = Field(None, alias="imageUrl")
    status: Optional[str] = None
    joinDate: Optional[date] = None
    grupDate: Optional[date] = None
    tanggalAkhirCuti: Optional[date] = None
    no_passport: Optional[str] = None
    role_id: Optional[int] = None

class PasswordUpdate(BaseModel):
    password: str = Field(..., min_length=6)
    
class UserInDB(UserBase):
    createOn: date
    modifiedOn: datetime
    role: Optional[Role] = None

    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    createOn: date
    modifiedOn: datetime
    role: Optional[Role] = None

    model_config = ConfigDict(from_attributes=True)