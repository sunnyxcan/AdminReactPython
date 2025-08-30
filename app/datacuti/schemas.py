# app/datacuti/schemas.py

from pydantic import BaseModel, Field, validator
from datetime import date, timedelta, datetime
from typing import Optional, Literal, List
import json

CutiJenis = Literal["Cuti Kerja", "Cuti Lokal", "Cuti Indonesia", "Cuti Melahirkan", "Mix"]
CutiStatus = Literal["Pending", "Cancel", "Reject", "Approved", "Done Catat", "Sedang Cuti", "Selesai Cuti"]
PassportOption = Literal[True, False, None]

PotonganGajiOption = Literal["1:1", "1:3", None]

class SubCutiDetail(BaseModel):
    jenis: Literal["Cuti Kerja", "Cuti Lokal", "Cuti Indonesia", "Cuti Melahirkan"]
    tanggal_mulai_sub: date
    tanggal_akhir_sub: date
    masa_cuti_sub: int = Field(..., gt=0, description="Jumlah hari cuti untuk sub-jenis ini.")
    passport_sub: Optional[PassportOption] = None

class CutiBase(BaseModel):
    user_uid: str
    tanggal_mulai: date
    masa_cuti: int = Field(..., gt=0, description="Jumlah hari cuti yang diajukan.")
    jenis_cuti: CutiJenis
    passport: PassportOption = None
    keterangan: Optional[str] = None
    
    masa_cuti_tambahan: Optional[int] = Field(None, ge=0, description="Jumlah hari cuti tambahan di luar jatah.")
    potongan_gaji_opsi: Optional[PotonganGajiOption] = None

    detail_mix_cuti: Optional[List[SubCutiDetail]] = None 

    @validator('detail_mix_cuti', pre=True, always=True)
    def validate_detail_mix_cuti_input(cls, v, values):
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("detail_mix_cuti harus berupa JSON string yang valid jika berupa string.")
        
        if 'jenis_cuti' in values and values['jenis_cuti'] == 'Mix':
            if not v:
                raise ValueError("Detail mix cuti harus disediakan jika jenis_cuti adalah 'Mix'.")
        elif v is not None:
            raise ValueError("Detail mix cuti hanya diizinkan jika jenis_cuti adalah 'Mix'.")
        return v

    @validator('masa_cuti_tambahan', pre=True, always=True)
    def validate_potongan_gaji_opsi_input(cls, v, values):
        if 'potongan_gaji_opsi' in values and values['potongan_gaji_opsi'] is not None and v is None:
            raise ValueError("Masa cuti tambahan harus diisi jika opsi potongan gaji dipilih.")
        elif 'potongan_gaji_opsi' in values and values['potongan_gaji_opsi'] is None and v is not None:
            raise ValueError("Opsi potongan gaji harus dipilih jika masa cuti tambahan diisi.")
        return v

class CutiCreate(CutiBase):
    pass

class CutiUpdate(BaseModel):
    tanggal_mulai: Optional[date] = None
    tanggal_akhir: Optional[date] = None
    masa_cuti: Optional[int] = Field(None, gt=0, description="Jumlah hari cuti yang diajukan.")
    jenis_cuti: Optional[CutiJenis] = None
    passport: Optional[PassportOption] = None
    keterangan: Optional[str] = None
    status: Optional[CutiStatus] = None
    by: Optional[str] = None
    
    masa_cuti_tambahan: Optional[int] = Field(None, ge=0, description="Jumlah hari cuti tambahan di luar jatah.")
    potongan_gaji_opsi: Optional[PotonganGajiOption] = None

    detail_mix_cuti: Optional[List[SubCutiDetail]] = None

    edit_by: Optional[str] = None

    @validator('detail_mix_cuti', pre=True, always=True)
    def validate_detail_mix_cuti_update(cls, v, values):
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("detail_mix_cuti harus berupa JSON string yang valid jika berupa string.")

        if v is not None and ('jenis_cuti' in values and values['jenis_cuti'] != 'Mix'):
            raise ValueError("Detail mix cuti hanya diizinkan jika jenis_cuti adalah 'Mix'.")
        return v

    @validator('masa_cuti_tambahan', pre=True, always=True)
    def validate_potongan_gaji_opsi_update_validator(cls, v, values):
        if v is not None and 'potongan_gaji_opsi' in values and values['potongan_gaji_opsi'] is None:
            raise ValueError("Opsi potongan gaji harus dipilih jika masa cuti tambahan diisi.")
        elif 'potongan_gaji_opsi' in values and values['potongan_gaji_opsi'] is not None and v is None:
            raise ValueError("Masa cuti tambahan harus diisi jika opsi potongan gaji dipilih.")
        return v

class CutiInDB(CutiBase):
    id: int
    tanggal_akhir: date
    status: CutiStatus
    tanggal: date
    by: Optional[str] = None
    
    edit_by: Optional[str] = None
    modified_on: datetime

    class Config:
        from_attributes = True

class CutiDetail(BaseModel):
    id: int
    tanggal_mulai: date
    tanggal_akhir: date
    jenis_cuti: CutiJenis
    status: CutiStatus
    masa_cuti_tambahan: Optional[int] = None
    potongan_gaji_opsi: Optional[PotonganGajiOption] = None
    
    edit_by: Optional[str] = None
    modified_on: datetime

    detail_mix_cuti: Optional[List[SubCutiDetail]] = None

    @validator('detail_mix_cuti', pre=True, always=True)
    def validate_detail_mix_cuti_output(cls, v, values):
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                return None 
        return v

    class Config:
        from_attributes = True