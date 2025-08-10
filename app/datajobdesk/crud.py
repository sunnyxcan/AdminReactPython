# app/datajobdesk/crud.py (Tidak ada perubahan yang diperlukan dari versi sebelumnya yang saya berikan)

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, asc
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
    listjob_category_id: Optional[int] = None, # Tetap sebagai int untuk filter satu kategori
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

    # Selalu join ke ListJobCategory jika ada filter kategori atau search_query yang mempengaruhi nama kategori
    if listjob_category_id is not None or search_query:
        # Gunakan kategoriJobdesk untuk join
        query = query.join(models.kategoriJobdesk, models.Jobdesk.no == models.kategoriJobdesk.c.jobdesk_no)
        query = query.join(ListJobCategory, models.kategoriJobdesk.c.listjob_category_id == ListJobCategory.id)

    # Lakukan join ke tabel User jika ada filter terkait nama atau jabatan
    if search_query or jabatan:
        query = query.join(User, models.Jobdesk.user_uid == User.uid)

    if tanggal_efektif_mulai:
        query = query.filter(models.Jobdesk.tanggal >= tanggal_efektif_mulai)

    if tanggal_efektif_akhir:
        query = query.filter(models.Jobdesk.tanggal <= tanggal_efektif_akhir)

    if listjob_category_id is not None:
        # Filter berdasarkan tabel asosiasi
        query = query.filter(models.kategoriJobdesk.c.listjob_category_id == listjob_category_id)

    if search_query:
        search_pattern = f"%{search_query.lower()}%"
        # Perhatikan bahwa pencarian berdasarkan kategori sekarang melalui ListJobCategory
        query = query.filter(
            (func.lower(User.fullname).like(search_pattern)) |
            (func.lower(ListJobCategory.nama).like(search_pattern))
        )

    if jabatan:
        query = query.filter(func.lower(User.jabatan).like(f"%{jabatan.lower()}%"))

    # Pengurutan: Jika ada join ke ListJobCategory, gunakan nama kategori
    # Jika tidak ada join, hanya urutkan berdasarkan tanggal dan user_uid
    if listjob_category_id is not None or search_query: # Atau jika join ListJobCategory terjadi
        query = query.order_by(
            models.Jobdesk.tanggal.asc(),
            ListJobCategory.nama.asc(), # Urutkan berdasarkan nama kategori
            models.Jobdesk.user_uid.asc()
        )
    else:
        query = query.order_by(
            models.Jobdesk.tanggal.asc(),
            models.Jobdesk.user_uid.asc()
        )

    return query.offset(skip).limit(limit).all()

def create_jobdesk(db: Session, jobdesk: schemas.JobdeskCreate, createdBy_uid: str):
    """
    Membuat data jobdesk baru dengan banyak kategori.
    Setelah pembuatan, jobdesk yang dikembalikan akan memiliki relasi yang sudah di-load.
    """
    # Verifikasi semua kategori yang diberikan ada
    for cat_id in jobdesk.listjob_category_ids:
        category_exists = listjob_category_crud.get_list_job_category(db, cat_id)
        if not category_exists:
            raise ValueError(f"Category with ID {cat_id} does not exist.")

    # Buat instance Jobdesk tanpa kategori terlebih dahulu
    db_jobdesk = models.Jobdesk(
        tanggal=jobdesk.tanggal,
        user_uid=jobdesk.user_uid,
        shift_no=jobdesk.shift_no,
        createdBy_uid=createdBy_uid
    )
    db.add(db_jobdesk)
    db.flush() # Flush untuk mendapatkan 'no' (ID) dari jobdesk baru

    # Tambahkan kategori ke jobdesk melalui relasi Many-to-Many
    for cat_id in jobdesk.listjob_category_ids:
        category = listjob_category_crud.get_list_job_category(db, cat_id)
        if category:
            db_jobdesk.categories.append(category)

    db.commit()
    db.refresh(db_jobdesk)

    # Eager load relasi untuk respons
    db_jobdesk = db.query(models.Jobdesk)\
                    .options(joinedload(models.Jobdesk.user))\
                    .options(joinedload(models.Jobdesk.created_by_user))\
                    .options(joinedload(models.Jobdesk.modified_by_user))\
                    .options(joinedload(models.Jobdesk.categories))\
                    .options(joinedload(models.Jobdesk.shift)) \
                    .filter(models.Jobdesk.no == db_jobdesk.no).first()
    return db_jobdesk

def update_jobdesk(db: Session, jobdesk_no: int, jobdesk_update: schemas.JobdeskUpdate, modifiedBy_uid: str):
    """
    Memperbarui data jobdesk yang ada, termasuk kategori.
    Setelah pembaruan, jobdesk yang dikembalikan akan memiliki relasi yang sudah di-load.
    """
    db_jobdesk = db.query(models.Jobdesk).filter(models.Jobdesk.no == jobdesk_no).first()
    if db_jobdesk:
        update_data = jobdesk_update.model_dump(exclude_unset=True)

        # Tangani pembaruan kategori secara terpisah
        if "listjob_category_ids" in update_data and update_data["listjob_category_ids"] is not None:
            new_category_ids = set(update_data.pop("listjob_category_ids"))
            existing_categories = set(c.id for c in db_jobdesk.categories)

            # Hapus kategori yang tidak lagi ada
            for cat_id in existing_categories - new_category_ids:
                category_to_remove = listjob_category_crud.get_list_job_category(db, cat_id)
                if category_to_remove in db_jobdesk.categories:
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
        db_jobdesk = db.query(models.Jobdesk)\
                        .options(joinedload(models.Jobdesk.user))\
                        .options(joinedload(models.Jobdesk.created_by_user))\
                        .options(joinedload(models.Jobdesk.modified_by_user))\
                        .options(joinedload(models.Jobdesk.categories))\
                        .options(joinedload(models.Jobdesk.shift)) \
                        .filter(models.Jobdesk.no == db_jobdesk.no).first()
    return db_jobdesk

def delete_jobdesk(db: Session, jobdesk_no: int):
    """
    Menghapus data jobdesk berdasarkan nomor (no), termasuk relasi kategorinya.
    """
    db_jobdesk = db.query(models.Jobdesk).filter(models.Jobdesk.no == jobdesk_no).first()
    if db_jobdesk:
        # Hapus semua relasi di tabel asosiasi secara otomatis oleh SQLAlchemy
        # saat objek Jobdesk dihapus, karena CASCADE atau ON DELETE CASCADE di database
        # atau jika SQLAlchemy dikonfigurasi untuk itu.
        # Jika tidak, Anda mungkin perlu menghapus entri dari tabel asosiasi secara manual.
        # Contoh manual (biasanya tidak diperlukan jika konfigurasi ORM benar):
        # db.query(models.kategoriJobdesk).filter(
        #     models.kategoriJobdesk.c.jobdesk_no == jobdesk_no
        # ).delete()

        db.delete(db_jobdesk)
        db.commit()
        return db_jobdesk
    return None