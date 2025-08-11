# app/cuti/crud.py
from sqlalchemy.orm import Session
from app.datacuti import models, schemas
from app.users import models as user_models
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
# Hapus import json karena kita tidak lagi melakukan dumps/loads manual untuk JSONB

def get_cuti(db: Session, cuti_id: int):
    return db.query(models.Cuti).filter(models.Cuti.id == cuti_id).first()

def get_cuti_by_user_uid(db: Session, user_uid: str, skip: int = 0, limit: int = 100):
    return db.query(models.Cuti).filter(models.Cuti.user_uid == user_uid).offset(skip).limit(limit).all()

def get_all_cuti(db: Session, skip: int = 0, limit: int = 100, status: str = None):
    query = db.query(models.Cuti)
    if status:
        query = query.filter(models.Cuti.status == status)
    return query.offset(skip).limit(limit).all()

def calculate_masa_kerja_years(join_date: date) -> int:
    """Menghitung masa kerja dalam tahun."""
    today = date.today()
    return relativedelta(today, join_date).years

def calculate_masa_kerja_months(join_date: date) -> int:
    """Menghitung masa kerja dalam bulan."""
    today = date.today()
    return (today.year - join_date.year) * 12 + (today.month - join_date.month)

def create_cuti(db: Session, cuti: schemas.CutiCreate):
    db_user = db.query(user_models.User).filter(user_models.User.uid == cuti.user_uid).first()
    if not db_user:
        return None

    masa_kerja_years = calculate_masa_kerja_years(db_user.joinDate)
    masa_kerja_months = calculate_masa_kerja_months(db_user.joinDate)

    jatah_cuti_dasar = 0
    if masa_kerja_years == 0 and masa_kerja_months < 12:
        jatah_cuti_dasar = 25
    elif masa_kerja_years >= 1 or (masa_kerja_years == 0 and masa_kerja_months >= 18):
        if db_user.jabatan == "Kasir":
            jatah_cuti_dasar = 12
        elif db_user.jabatan in ["Kapten", "Operator"]:
            jatah_cuti_dasar = 14
        else:
            jatah_cuti_dasar = 10

    total_masa_cuti_diajukan = cuti.masa_cuti
    if cuti.masa_cuti_tambahan:
        total_masa_cuti_diajukan -= cuti.masa_cuti_tambahan

    if total_masa_cuti_diajukan > jatah_cuti_dasar and cuti.masa_cuti_tambahan is None:
        pass

    final_passport_status = None
    if cuti.jenis_cuti in ["Cuti Indonesia", "Cuti Melahirkan"]:
        final_passport_status = True
    elif cuti.jenis_cuti in ["Cuti Kerja", "Cuti Lokal"]:
        final_passport_status = cuti.passport
    elif cuti.jenis_cuti == "Mix":
        final_passport_status = False
        for detail in cuti.detail_mix_cuti:
            if detail.jenis in ["Cuti Indonesia", "Cuti Melahirkan"]:
                final_passport_status = True
                break
        
        min_start_date = min(d.tanggal_mulai_sub for d in cuti.detail_mix_cuti)
        max_end_date = max(d.tanggal_akhir_sub for d in cuti.detail_mix_cuti)

        if cuti.tanggal_mulai != min_start_date or cuti.tanggal_akhir != max_end_date:
            pass

    tanggal_akhir_otomatis = cuti.tanggal_mulai + timedelta(days=cuti.masa_cuti - 1)

    # --- PERUBAHAN DI SINI ---
    # Jika detail_mix_cuti ada, ubah menjadi list of dictionaries menggunakan .model_dump()
    # SQLAlchemy dengan JSONB akan mengurus serialisasi dan deserialisasi.
    detail_mix_cuti_for_db = None
    if cuti.detail_mix_cuti:
        detail_mix_cuti_for_db = [d.model_dump() for d in cuti.detail_mix_cuti]
    # --- AKHIR PERUBAHAN ---

    db_cuti = models.Cuti(
        user_uid=cuti.user_uid,
        tanggal_mulai=cuti.tanggal_mulai,
        tanggal_akhir=tanggal_akhir_otomatis,
        masa_cuti=cuti.masa_cuti,
        jenis_cuti=cuti.jenis_cuti,
        passport=final_passport_status,
        keterangan=cuti.keterangan,
        status="Pending",
        masa_cuti_tambahan=cuti.masa_cuti_tambahan,
        potongan_gaji_opsi=cuti.potongan_gaji_opsi,
        # Gunakan detail_mix_cuti_for_db yang sudah berupa list of dictionaries
        detail_mix_cuti=detail_mix_cuti_for_db,
        modified_on=datetime.now()
    )
    db.add(db_cuti)
    db.commit()
    db.refresh(db_cuti)
    return db_cuti

def update_cuti(db: Session, cuti_id: int, cuti_update: schemas.CutiUpdate):
    db_cuti = db.query(models.Cuti).filter(models.Cuti.id == cuti_id).first()
    if not db_cuti:
        return None

    update_data = cuti_update.model_dump(exclude_unset=True)
    
    if 'masa_cuti' in update_data and update_data['masa_cuti'] is not None:
        current_tanggal_mulai = update_data.get('tanggal_mulai') or db_cuti.tanggal_mulai
        update_data['tanggal_akhir'] = current_tanggal_mulai + timedelta(days=update_data['masa_cuti'] - 1)
    elif 'tanggal_mulai' in update_data and update_data['tanggal_mulai'] is not None:
        current_masa_cuti = update_data.get('masa_cuti') or db_cuti.masa_cuti
        update_data['tanggal_akhir'] = update_data['tanggal_mulai'] + timedelta(days=current_masa_cuti - 1)

    if 'jenis_cuti' in update_data:
        if update_data['jenis_cuti'] in ["Cuti Indonesia", "Cuti Melahirkan"]:
            update_data['passport'] = True
        elif update_data['jenis_cuti'] in ["Cuti Kerja", "Cuti Lokal"]:
            if update_data.get('passport') is None:
                update_data['passport'] = db_cuti.passport
        elif update_data['jenis_cuti'] == "Mix":
            if 'detail_mix_cuti' in update_data and update_data['detail_mix_cuti']:
                passport_mix = False
                for detail in update_data['detail_mix_cuti']:
                    if detail.jenis in ["Cuti Indonesia", "Cuti Melahirkan"]:
                        passport_mix = True
                        break
                update_data['passport'] = passport_mix
            elif db_cuti.jenis_cuti == "Mix" and db_cuti.detail_mix_cuti:
                passport_mix = False
                # --- PERUBAHAN DI SINI ---
                # db_cuti.detail_mix_cuti sudah berupa list/dict karena tipe JSONB
                # Tidak perlu lagi json.loads()
                for detail in db_cuti.detail_mix_cuti:
                    if detail['jenis'] in ["Cuti Indonesia", "Cuti Melahirkan"]:
                        passport_mix = True
                        break
                # --- AKHIR PERUBAHAN ---
                update_data['passport'] = passport_mix
            else:
                update_data['passport'] = None

    # --- PERUBAHAN DI SINI ---
    # Handle update untuk detail_mix_cuti
    if 'detail_mix_cuti' in update_data and update_data['detail_mix_cuti'] is not None:
        # Pydantic sudah memvalidasi ini sebagai List[SubCutiDetail],
        # jadi kita bisa langsung mengubahnya ke list of dictionaries untuk disimpan.
        update_data['detail_mix_cuti'] = [d.model_dump() for d in update_data['detail_mix_cuti']]
    elif 'jenis_cuti' in update_data and update_data['jenis_cuti'] != 'Mix':
        update_data['detail_mix_cuti'] = None
    # --- AKHIR PERUBAHAN ---
    
    if 'masa_cuti_tambahan' in update_data:
        setattr(db_cuti, 'masa_cuti_tambahan', update_data['masa_cuti_tambahan'])
    if 'potongan_gaji_opsi' in update_data:
        setattr(db_cuti, 'potongan_gaji_opsi', update_data['potongan_gaji_opsi'])

    if 'edit_by' in update_data:
        setattr(db_cuti, 'edit_by', update_data['edit_by'])
    
    for key, value in update_data.items():
        if key not in ['masa_cuti_tambahan', 'potongan_gaji_opsi', 'edit_by']:
            setattr(db_cuti, key, value)
    
    db.add(db_cuti)
    db.commit()
    db.refresh(db_cuti)
    return db_cuti

def delete_cuti(db: Session, cuti_id: int):
    db_cuti = db.query(models.Cuti).filter(models.Cuti.id == cuti_id).first()
    if db_cuti:
        db.delete(db_cuti)
        db.commit()
        return True
    return False