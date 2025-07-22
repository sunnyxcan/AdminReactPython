# schemas.py

from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional

class EmployeeBase(BaseModel):
    name: str
    position: str

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int

    class Config:
        orm_mode = True # Untuk mengizinkan ORM models

class AttendanceBase(BaseModel):
    employee_id: int
    date: date
    check_in: time
    check_out: Optional[time] = None

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True