# app/whitelist/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import Optional

# ⭐ Skema baru untuk data pengguna yang dibutuhkan
class UserSchema(BaseModel):
    uid: str
    fullname: str
    
    model_config = ConfigDict(from_attributes=True)

class WhitelistIPBase(BaseModel):
    ip_address: str

class WhitelistIPCreate(WhitelistIPBase):
    created_by: str

class WhitelistIPUpdate(BaseModel):
    ip_address: Optional[str] = None
    edit_by: Optional[str] = None

class WhitelistIP(WhitelistIPBase):
    no: int
    tanggal: datetime
    created_by: Optional[str] = None
    edit_by: Optional[str] = None
    createOn: datetime
    modifiedOn: datetime

    # Tambahkan atribut baru untuk relasi
    creator: Optional[UserSchema] = None
    editor: Optional[UserSchema] = None

    model_config = ConfigDict(from_attributes=True)