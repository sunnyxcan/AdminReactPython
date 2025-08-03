# backend/app/users/schemas.py

from pydantic import BaseModel, Field
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
    # Tambahkan baris ini
    class Config:
        from_attributes = True

class User(UserBase):
    createOn: date
    modifiedOn: datetime
    role: Optional[Role] = None

    class Config:
        from_attributes = True