# app/listjob/schemas.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# Hapus baris ini yang menyebabkan circular import
# from app.listjob.schemas import ListJobCategoryInDB 
# Jika ListJobCategoryInDB adalah skema yang Anda definisikan di sini, 
# maka Anda tidak perlu mengimpornya dari file yang sama.

from app.users.schemas import UserInDB # Pastikan UserInDB diimpor dengan benar jika digunakan

class ListJobCategoryBase(BaseModel):
    nama: str
    deskripsi: Optional[str] = None

class ListJobCategoryCreate(ListJobCategoryBase):
    pass

class ListJobCategoryUpdate(BaseModel):
    nama: Optional[str] = None
    deskripsi: Optional[str] = None

class ListJobCategoryInDB(ListJobCategoryBase):
    id: int
    createdBy_uid: str
    modifiedBy_uid: Optional[str] = None
    createOn: datetime
    modifiedOn: Optional[datetime] = None # Sesuaikan dengan model DateTime di SQLAlchemy

    # Relasi Pydantic
    created_by_user: UserInDB
    modified_by_user: Optional[UserInDB] = None

    model_config = ConfigDict(from_attributes=True)