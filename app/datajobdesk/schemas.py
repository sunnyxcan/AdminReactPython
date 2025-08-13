# app/datajobdesk/schemas.py

from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List, Optional

from app.users.schemas import UserInDB
from app.listjob.schemas import ListJobCategoryInDB 
from app.datashift.schemas import ShiftInDB

class JobdeskBase(BaseModel):
    tanggal: date
    user_uid: str
    listjob_category_ids: List[int]
    shift_no: Optional[int] = None

class JobdeskCreate(JobdeskBase):
    pass

class JobdeskUpdate(BaseModel):
    tanggal: Optional[date] = None
    user_uid: Optional[str] = None
    listjob_category_ids: Optional[List[int]] = None
    shift_no: Optional[int] = None

class JobdeskInDB(BaseModel):
    no: int
    tanggal: date
    user_uid: str

    createdBy_uid: str
    modifiedBy_uid: Optional[str] = None
    createdOn: datetime
    modifiedOn: Optional[datetime] = None
    
    user: UserInDB
    created_by_user: UserInDB
    modified_by_user: Optional[UserInDB] = None
    
    categories: List[ListJobCategoryInDB]
    shift: Optional[ShiftInDB] = None 

    model_config = ConfigDict(from_attributes=True)

JobdeskInDB.model_rebuild()