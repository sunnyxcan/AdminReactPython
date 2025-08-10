# app/datashift/crud.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, asc
from datetime import date, datetime
from app.datashift import models, schemas
from app.users import models as user_models # <-- PERBAIKI: Impor model User

def get_shift(db: Session, shift_no: int):
    """
    Mengambil satu data shift berdasarkan nomor (no) dengan eager loading relasi user dan jobdesks.
    """
    return db.query(models.Shift)\
             .options(joinedload(models.Shift.user))\
             .options(joinedload(models.Shift.created_by_user))\
             .options(joinedload(models.Shift.jobdesks)) \
             .filter(models.Shift.no == shift_no).first()

def get_shifts(db: Session, skip: int = 0, limit: int = 100, user_uid: str = None, start_date: date = None, end_date: date = None, jabatan: str = None): # <-- PERBAIKI: Tambahkan parameter jabatan
    """
    Mengambil daftar data shift dengan opsi filter dan paginasi,
    serta eager loading relasi user, created_by_user, dan jobdesks.
    Akan mengurutkan data berdasarkan tanggal mulai, jadwal, jam masuk, dan user_uid.
    """
    query = db.query(models.Shift)\
              .options(joinedload(models.Shift.user))\
              .options(joinedload(models.Shift.created_by_user))\
              .options(joinedload(models.Shift.jobdesks))

    if user_uid:
        query = query.filter(models.Shift.user_uid == user_uid)
    if start_date:
        query = query.filter(models.Shift.tanggalMulai >= start_date)
    if end_date:
        query = query.filter(models.Shift.tanggalAkhir <= end_date)
    if jabatan: # <-- PERBAIKI: Tambahkan filter berdasarkan jabatan
        query = query.join(user_models.User).filter(user_models.User.jabatan == jabatan)
        
    query = query.order_by(
        models.Shift.tanggalMulai.asc(),
        case(
            (models.Shift.jadwal == 'Pagi', 1),
            (models.Shift.jadwal == 'Siang', 2),
            (models.Shift.jadwal == 'Sore', 3),
            (models.Shift.jadwal == 'Malam', 4),
            else_=99
        ).asc(),
        models.Shift.jamMasuk.asc(),
        models.Shift.user_uid.asc()
    )
    
    return query.offset(skip).limit(limit).all()

# Helper function to convert datetime to HH:MM string for database storage
def _convert_time_for_db(time_value):
    if isinstance(time_value, datetime):
        return time_value.strftime("%H:%M")
    elif isinstance(time_value, str) and len(time_value) == 5 and time_value[2] == ':':
        return time_value
    elif isinstance(time_value, str):
        try:
            dt_obj = datetime.fromisoformat(time_value.replace('Z', '+00:00'))
            return dt_obj.strftime("%H:%M")
        except ValueError:
            return time_value
    return None

def create_shift(db: Session, shift: schemas.ShiftCreate, createdBy_uid: str):
    """
    Membuat data shift baru.
    """
    shift_data = shift.model_dump()
    for key in ['jamMasuk', 'jamPulang', 'jamMasukDoubleShift', 'jamPulangDoubleShift']:
        shift_data[key] = _convert_time_for_db(shift_data[key])

    db_shift = models.Shift(**shift_data, createdBy_uid=createdBy_uid)
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    db_shift = db.query(models.Shift)\
                     .options(joinedload(models.Shift.user))\
                     .options(joinedload(models.Shift.created_by_user))\
                     .options(joinedload(models.Shift.jobdesks)) \
                     .filter(models.Shift.no == db_shift.no).first()
    return db_shift

def update_shift(db: Session, shift_no: int, shift_update: schemas.ShiftUpdate):
    """
    Memperbarui data shift yang ada.
    """
    db_shift = db.query(models.Shift).filter(models.Shift.no == shift_no).first()
    if db_shift:
        update_data = shift_update.model_dump(exclude_unset=True)
        for key in ['jamMasuk', 'jamPulang', 'jamMasukDoubleShift', 'jamPulangDoubleShift']:
            if key in update_data:
                update_data[key] = _convert_time_for_db(update_data[key])

        for key, value in update_data.items():
            setattr(db_shift, key, value)
        
        db.commit()
        db.refresh(db_shift)
        db_shift = db.query(models.Shift)\
                         .options(joinedload(models.Shift.user))\
                         .options(joinedload(models.Shift.created_by_user))\
                         .options(joinedload(models.Shift.jobdesks)) \
                         .filter(models.Shift.no == db_shift.no).first()
    return db_shift

def delete_shift(db: Session, shift_no: int):
    """
    Menghapus data shift berdasarkan nomor (no).
    """
    db_shift = db.query(models.Shift).filter(models.Shift.no == shift_no).first()
    if db_shift:
        db.delete(db_shift)
        db.commit()
        return db_shift
    return None