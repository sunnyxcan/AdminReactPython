# backend/app/device/schemas.py

from pydantic import BaseModel

class DeviceInfo(BaseModel):
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
    device: DeviceInfo
    os: OSInfo
    browser: BrowserInfo