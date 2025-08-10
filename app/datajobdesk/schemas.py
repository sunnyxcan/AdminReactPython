# app/datajobdesk/schemas.py

from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List, Optional

from app.users.schemas import UserInDB
from app.listjob.schemas import ListJobCategoryInDB 
from app.datashift.schemas import ShiftInDB # Import ShiftInDB

class JobdeskBase(BaseModel):
    tanggal: date
    user_uid: str
    listjob_category_ids: List[int] # <-- Biarkan ini di sini untuk input (Create/Update)
    shift_no: Optional[int] = None

class JobdeskCreate(JobdeskBase):
    pass

class JobdeskUpdate(BaseModel):
    tanggal: Optional[date] = None
    user_uid: Optional[str] = None
    listjob_category_ids: Optional[List[int]] = None # <-- Biarkan ini di sini untuk input (Update)
    shift_no: Optional[int] = None

class JobdeskInDB(BaseModel): # <-- UBAH: Tidak mewarisi dari JobdeskBase lagi
    no: int
    tanggal: date # <-- TAMBAHKAN KEMBALI: Karena tidak mewarisi dari JobdeskBase
    user_uid: str # <-- TAMBAHKAN KEMBALI: Karena tidak mewarisi dari JobdeskBase

    createdBy_uid: str
    modifiedBy_uid: Optional[str] = None
    createdOn: datetime
    modifiedOn: Optional[datetime] = None
    
    user: UserInDB
    created_by_user: UserInDB
    modified_by_user: Optional[UserInDB] = None
    
    # Kunci perbaikan: Hapus 'listjob_category_ids'. 
    # 'categories' adalah representasi output yang benar untuk relasi many-to-many.
    categories: List[ListJobCategoryInDB] # Ini akan mengisi dirinya sendiri dari relasi ORM
    
    shift: Optional[ShiftInDB] = None 

    model_config = ConfigDict(from_attributes=True)

JobdeskInDB.model_rebuild()