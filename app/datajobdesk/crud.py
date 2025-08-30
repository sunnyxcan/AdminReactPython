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

def get_jobdesk_by_user_date_shift(db: Session, user_uid: str, tanggal: date, shift_no: int):
    """
    Mengambil satu jobdesk berdasarkan kombinasi user, tanggal, dan shift.
    """
    return db.query(models.Jobdesk).filter(
        and_(
            models.Jobdesk.user_uid == user_uid,
            models.Jobdesk.tanggal == tanggal,
            models.Jobdesk.shift_no == shift_no
        )
    ).first()

def create_jobdesk(db: Session, jobdesk_create: schemas.JobdeskCreate, createdBy_uid: str):
    """
    Membuat data jobdesk baru dan menghubungkannya dengan kategori yang sesuai.
    """
    # Pastikan semua kategori ada sebelum membuat objek Jobdesk
    categories_to_link = []
    for category_id in jobdesk_create.listjob_category_ids:
        category = listjob_category_crud.get_list_job_category(db, category_id)
        if not category:
            # Jika ada satu kategori pun yang tidak ada, gagal di sini dengan ValueError
            raise ValueError(f"Category with ID {category_id} does not exist.")
        categories_to_link.append(category)

    # Memeriksa duplikasi sebelum membuat
    existing_jobdesk = get_jobdesk_by_user_date_shift(
        db, 
        user_uid=jobdesk_create.user_uid, 
        tanggal=jobdesk_create.tanggal, 
        shift_no=jobdesk_create.shift_no
    )
    if existing_jobdesk:
        raise ValueError("Kombinasi user, tanggal, dan shift sudah memiliki jobdesk.")

    db_jobdesk = models.Jobdesk(
        tanggal=jobdesk_create.tanggal,
        user_uid=jobdesk_create.user_uid,
        shift_no=jobdesk_create.shift_no,
        createdBy_uid=createdBy_uid,
        modifiedBy_uid=None
    )
    
    db.add(db_jobdesk)
    
    # Tambahkan relasi Many-to-Many
    db_jobdesk.categories.extend(categories_to_link)
    
    db.commit()
    db.refresh(db_jobdesk)
    
    return get_jobdesk(db, db_jobdesk.no)

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
    if "listjob_category_ids" in update_data:
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