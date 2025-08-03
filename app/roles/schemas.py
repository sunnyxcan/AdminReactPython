# backend/app/roles/schemas.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    createOn: datetime
    modifiedOn: datetime

    class Config:
        from_attributes = True