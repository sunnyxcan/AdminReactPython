# backend/app/schemas.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    position: str

class EmployeeCreate(EmployeeBase):
    # Ketika membuat karyawan baru, kita mungkin tidak langsung punya firebase_uid
    # tetapi bisa diupdate nanti atau langsung di set jika sudah ada user Firebase
    pass

class EmployeeUpdate(EmployeeBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    position: Optional[str] = None
    is_admin: Optional[bool] = None
    firebase_uid: Optional[str] = None # Untuk mengaitkan dengan user Firebase yang sudah ada

class Employee(EmployeeBase):
    id: int
    firebase_uid: Optional[str] = None
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Dulu orm_mode = True di Pydantic v1

class AttendanceBase(BaseModel):
    employee_id: int
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    status: Optional[str] = "Present"
    notes: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(AttendanceBase):
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class Attendance(AttendanceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Skema untuk otentikasi
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    position: str
    is_admin: Optional[bool] = False # default tidak admin