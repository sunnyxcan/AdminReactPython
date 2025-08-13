# app/datajobdesk/crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, asc, and_
from datetime import date, datetime
from typing import Optional, List
from app.datajobdesk import models, schemas
from app.listjob import crud as listjob_category_crud
from app.listjob.models import ListJobCategory
from app.datashift.models import Shift
from app.users.models import User

def get_jobdesk(db: Session, jobdesk_no: int):
    """
    Mengambil satu data jobdesk berdasarkan nomor (no) dengan eager loading relasi user, created_by_user, modified_by_user, categories, DAN SHIFT.
    """
    return db.query(models.Jobdesk)\
             .options(joinedload(models.Jobdesk.user))\
             .options(joinedload(models.Jobdesk.created_by_user))\
             .options(joinedload(models.Jobdesk.modified_by_user))\
             .options(joinedload(models.Jobdesk.categories))\
             .options(joinedload(models.Jobdesk.shift)) \
             .filter(models.Jobdesk.no == jobdesk_no).first()

def get_jobdesks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_uid: Optional[str] = None,
    tanggal_efektif_mulai: Optional[date] = None,
    tanggal_efektif_akhir: Optional[date] = None,
    listjob_category_id: Optional[int] = None,
    search_query: Optional[str] = None,
    jabatan: Optional[str] = None
):
    """
    Mengambil daftar data jobdesk dengan opsi filter dan paginasi,
    serta eager loading relasi user, created_by_user, modified_by_user, categories, DAN SHIFT.
    Akan mengurutkan data berdasarkan tanggal efektif dan nama kategori jobdesk (jika difilter).
    """
    query = db.query(models.Jobdesk)\
              .options(joinedload(models.Jobdesk.user))\
              .options(joinedload(models.Jobdesk.created_by_user))\
              .options(joinedload(models.Jobdesk.modified_by_user))\
              .options(joinedload(models.Jobdesk.categories))\
              .options(joinedload(models.Jobdesk.shift))

    if listjob_category_id is not None or search_query:
        query = query.join(models.kategoriJobdesk, models.Jobdesk.no == models.kategoriJobdesk.c.jobdesk_no)
        query = query.join(ListJobCategory, models.kategoriJobdesk.c.listjob_category_id == ListJobCategory.id)

    if search_query or jabatan:
        query = query.join(User, models.Jobdesk.user_uid == User.uid)

    if tanggal_efektif_mulai:
        query = query.filter(models.Jobdesk.tanggal >= tanggal_efektif_mulai)

    if tanggal_efektif_akhir:
        query = query.filter(models.Jobdesk.tanggal <= tanggal_efektif_akhir)

    if user_uid:
        query = query.filter(models.Jobdesk.user_uid == user_uid)

    if listjob_category_id is not None:
        query = query.filter(models.kategoriJobdesk.c.listjob_category_id == listjob_category_id)

    if search_query:
        search_pattern = f"%{search_query.lower()}%"
        query = query.filter(
            (func.lower(User.fullname).like(search_pattern)) |
            (func.lower(ListJobCategory.nama).like(search_pattern))
        )

    if jabatan:
        query = query.filter(func.lower(User.jabatan).like(f"%{jabatan.lower()}%"))
        
    query = query.order_by(
        models.Jobdesk.tanggal.asc(),
        models.Jobdesk.user_uid.asc()
    ).distinct()

    return query.offset(skip).limit(limit).all()

def create_jobdesk(db: Session, jobdesk: schemas.JobdeskCreate, createdBy_uid: str):
    """
    Membuat data jobdesk baru dengan banyak kategori atau menambahkan kategori ke entri yang sudah ada.
    Memeriksa duplikasi berdasarkan user, tanggal, dan shift.
    """
    # Periksa apakah entri jobdesk dengan user, tanggal, dan shift yang sama sudah ada
    existing_jobdesk = db.query(models.Jobdesk).filter(
        and_(
            models.Jobdesk.tanggal == jobdesk.tanggal,
            models.Jobdesk.user_uid == jobdesk.user_uid,
            models.Jobdesk.shift_no == jobdesk.shift_no
        )
    ).first()

    if existing_jobdesk:
        # Jika sudah ada, tambahkan kategori baru ke entri yang sudah ada
        unique_category_ids = set(jobdesk.listjob_category_ids)
        existing_category_ids = set(c.id for c in existing_jobdesk.categories)
        new_category_ids_to_add = unique_category_ids - existing_category_ids

        if not new_category_ids_to_add:
            # Jika semua kategori yang diberikan sudah ada, anggap sebagai duplikasi
            raise ValueError("Kombinasi user, tanggal, dan shift sudah ada dan semua kategori yang diberikan sudah terdaftar.")

        for cat_id in new_category_ids_to_add:
            category = listjob_category_crud.get_list_job_category(db, cat_id)
            if category:
                existing_jobdesk.categories.append(category)
            else:
                raise ValueError(f"Category with ID {cat_id} does not exist.")

        existing_jobdesk.modifiedBy_uid = createdBy_uid
        db.commit()
        db.refresh(existing_jobdesk)

        # Eager load relasi untuk respons
        db_jobdesk = get_jobdesk(db, existing_jobdesk.no)
        return db_jobdesk
    else:
        # Jika tidak ada, buat entri baru
        db_jobdesk = models.Jobdesk(
            tanggal=jobdesk.tanggal,
            user_uid=jobdesk.user_uid,
            shift_no=jobdesk.shift_no,
            createdBy_uid=createdBy_uid
        )
        db.add(db_jobdesk)
        db.flush()

        unique_category_ids = set(jobdesk.listjob_category_ids)
        for cat_id in unique_category_ids:
            category = listjob_category_crud.get_list_job_category(db, cat_id)
            if category:
                db_jobdesk.categories.append(category)
            else:
                raise ValueError(f"Category with ID {cat_id} does not exist.")

        db.commit()
        db.refresh(db_jobdesk)
        db_jobdesk = get_jobdesk(db, db_jobdesk.no)
        return db_jobdesk

def update_jobdesk(db: Session, jobdesk_no: int, jobdesk_update: schemas.JobdeskUpdate, modifiedBy_uid: str):
    """
    Memperbarui data jobdesk yang ada, termasuk kategori.
    """
    db_jobdesk = db.query(models.Jobdesk).filter(models.Jobdesk.no == jobdesk_no).first()
    if not db_jobdesk:
        return None

    update_data = jobdesk_update.model_dump(exclude_unset=True)
    
    # Periksa duplikasi jika ada perubahan pada user_uid, tanggal, atau shift_no
    if any(key in update_data for key in ['user_uid', 'tanggal', 'shift_no']):
        new_user_uid = update_data.get('user_uid', db_jobdesk.user_uid)
        new_tanggal = update_data.get('tanggal', db_jobdesk.tanggal)
        new_shift_no = update_data.get('shift_no', db_jobdesk.shift_no)

        existing_duplicate = db.query(models.Jobdesk).filter(
            and_(
                models.Jobdesk.tanggal == new_tanggal,
                models.Jobdesk.user_uid == new_user_uid,
                models.Jobdesk.shift_no == new_shift_no,
                models.Jobdesk.no != jobdesk_no # Pastikan bukan entri yang sedang diupdate
            )
        ).first()

        if existing_duplicate:
            raise ValueError("Kombinasi user, tanggal, dan shift yang diperbarui sudah ada di entri lain.")

    # Tangani pembaruan kategori secara terpisah
    if "listjob_category_ids" in update_data and update_data["listjob_category_ids"] is not None:
        new_category_ids = set(update_data.pop("listjob_category_ids"))
        existing_categories = set(c.id for c in db_jobdesk.categories)

        # Hapus kategori yang tidak lagi ada
        for cat_id in existing_categories - new_category_ids:
            category_to_remove = listjob_category_crud.get_list_job_category(db, cat_id)
            if category_to_remove:
                db_jobdesk.categories.remove(category_to_remove)

        # Tambahkan kategori baru
        for cat_id in new_category_ids - existing_categories:
            category_to_add = listjob_category_crud.get_list_job_category(db, cat_id)
            if not category_to_add:
                raise ValueError(f"Category with ID {cat_id} does not exist.")
            db_jobdesk.categories.append(category_to_add)

    # Perbarui atribut lainnya
    for key, value in update_data.items():
        setattr(db_jobdesk, key, value)

    db_jobdesk.modifiedBy_uid = modifiedBy_uid
    db.commit()
    db.refresh(db_jobdesk)

    # Eager load relasi untuk respons
    return get_jobdesk(db, db_jobdesk.no)

def delete_jobdesk(db: Session, jobdesk_no: int):
    """
    Menghapus data jobdesk berdasarkan nomor (no), termasuk relasi kategorinya.
    """
    db_jobdesk = db.query(models.Jobdesk).filter(models.Jobdesk.no == jobdesk_no).first()
    if db_jobdesk:
        db.delete(db_jobdesk)
        db.commit()
        return db_jobdesk
    return None