# app/statusLive/schemas.py

from pydantic import BaseModel
from datetime import datetime

class BackendStatusBase(BaseModel):
    last_active: datetime

class BackendStatus(BackendStatusBase):
    id: int

    class Config:
        from_attributes = True