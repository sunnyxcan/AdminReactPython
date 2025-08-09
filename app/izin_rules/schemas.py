# backend/izin_rules/schemas.py
# (Tidak ada perubahan, kode ini sudah benar)
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional, Any

class IzinRuleBase(BaseModel):
    max_daily_izin: int = Field(default=4, ge=0)
    max_duration_seconds: int = Field(default=900, ge=0)

    is_double_shift_rule: bool = Field(default=False)
    # Gunakan None sebagai default agar konsisten
    max_daily_double_shift: Optional[int] = Field(default=None, ge=0) 
    double_shift_day: Optional[str] = Field(default=None)

    max_concurrent_izin: int = Field(default=0, ge=0)
    max_izin_operator: int = Field(default=0, ge=0)
    max_izin_kapten: int = Field(default=0, ge=0)
    max_izin_kasir: int = Field(default=0, ge=0)
    max_izin_kasir_lokal: int = Field(default=0, ge=0)

    @model_validator(mode='before')
    @classmethod
    def validate_double_shift_rule(cls, values: Any) -> Any:
        # Pengecekan untuk dict atau objek Pydantic
        is_double_shift = values.get('is_double_shift_rule') if isinstance(values, dict) else getattr(values, 'is_double_shift_rule', False)
        max_double_shift = values.get('max_daily_double_shift') if isinstance(values, dict) else getattr(values, 'max_daily_double_shift', None)
        double_shift_day = values.get('double_shift_day') if isinstance(values, dict) else getattr(values, 'double_shift_day', None)

        if is_double_shift:
            if max_double_shift is None:
                raise ValueError("max_daily_double_shift cannot be null when is_double_shift_rule is True.")
            if double_shift_day is None or double_shift_day == "":
                raise ValueError("double_shift_day cannot be null or empty when is_double_shift_rule is True.")
        else:
            # Pastikan nilai-nilai ini diatur ke None secara eksplisit
            # Ini sudah dilakukan oleh validator, jadi kodenya sudah benar
            if isinstance(values, dict):
                values['max_daily_double_shift'] = None
                values['double_shift_day'] = None

        return values

class IzinRuleCreate(IzinRuleBase):
    pass

class IzinRuleInDB(IzinRuleBase):
    id: int
    createOn: datetime
    modifiedOn: Optional[datetime] = None

    class Config:
        from_attributes = True