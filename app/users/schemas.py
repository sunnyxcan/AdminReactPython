# backend/app/users/schemas.py

from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    uid: str
    fullname: str
    jabatan: Optional[str] = None
    email: str

    class Config:
        from_attributes = True