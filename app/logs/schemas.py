# app/logs/schemas.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DeviceInfoBase(BaseModel):
    is_mobile: bool
    is_tablet: bool
    is_pc: bool
    is_touch_capable: bool
    is_bot: bool
    
class OSInfo(BaseModel):
    family: str
    version_string: str

class BrowserInfo(BaseModel):
    family: str
    version_string: str

class DeviceInfoResponse(BaseModel):
    device: DeviceInfoBase
    os: OSInfo
    browser: BrowserInfo

class LogBase(BaseModel):
    action: str
    entity_name: str
    entity_id: str
    details: Optional[str] = None
    created_by: Optional[str] = None
    # 🆕 Tambahkan kolom baru
    ip_address: Optional[str] = None
    device_info: Optional[dict] = None # Gunakan `dict` untuk data JSON

class LogCreate(LogBase):
    pass

class Log(LogBase):
    id: int
    createOn: datetime

    class Config:
        from_attributes = True