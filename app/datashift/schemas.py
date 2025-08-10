# app/datashift/schemas.py

from pydantic import BaseModel, Field, field_validator, ConfigDict # <--- ADD ConfigDict here
from datetime import datetime, date
from typing import Optional, List

from app.users.schemas import UserInDB
from app.listjob.schemas import ListJobCategoryInDB 

# Helper function to format time string
def format_time_to_hh_mm(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str) and len(value) == 5 and value[2] == ':':
        return value
    try:
        dt_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt_obj.strftime("%H:%M")
    except ValueError:
        return value

class JobdeskForShiftInDB(BaseModel):
    no: int
    tanggal: date
    user_uid: str
    categories: List[ListJobCategoryInDB] 
    shift_no: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True) # <--- ConfigDict is now defined

class ShiftBase(BaseModel):
    user_uid: str
    tanggalMulai: date
    tanggalAkhir: date
    jamMasuk: Optional[str] = None
    jamPulang: Optional[str] = None
    jamMasukDoubleShift: Optional[str] = None
    jamPulangDoubleShift: Optional[str] = None
    jadwal: Optional[str] = None
    keterangan: Optional[str] = None

    @field_validator('jamMasuk', 'jamPulang', 'jamMasukDoubleShift', 'jamPulangDoubleShift', mode='before')
    @classmethod
    def validate_and_format_time_fields(cls, v: Optional[str]) -> Optional[str]:
        return format_time_to_hh_mm(v)

class ShiftCreate(ShiftBase):
    pass 

class ShiftUpdate(BaseModel):
    user_uid: Optional[str] = None
    tanggalMulai: Optional[date] = None
    tanggalAkhir: Optional[date] = None
    jamMasuk: Optional[str] = None
    jamPulang: Optional[str] = None
    jamMasukDoubleShift: Optional[str] = None
    jamPulangDoubleShift: Optional[str] = None
    jadwal: Optional[str] = None
    keterangan: Optional[str] = None

    @field_validator('jamMasuk', 'jamPulang', 'jamMasukDoubleShift', 'jamPulangDoubleShift', mode='before')
    @classmethod
    def validate_and_format_time_fields(cls, v: Optional[str]) -> Optional[str]:
        return format_time_to_hh_mm(v)

class ShiftInDB(ShiftBase):
    no: int
    createdBy_uid: str
    createOn: date
    modifiedOn: Optional[date] = None
    
    user_detail: Optional[UserInDB] = Field(None, alias='user')
    created_by_user_detail: Optional[UserInDB] = Field(None, alias='created_by_user')
    
    jobdesks: List[JobdeskForShiftInDB] = [] 

    @field_validator('jamMasuk', 'jamPulang', 'jamMasukDoubleShift', 'jamPulangDoubleShift', mode='after')
    @classmethod
    def format_time_output(cls, v: Optional[str]) -> Optional[str]:
        return format_time_to_hh_mm(v)

    model_config = ConfigDict(from_attributes=True) # <--- ConfigDict is now defined