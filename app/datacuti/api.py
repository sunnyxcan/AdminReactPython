# app/datacuti/api.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
import json
import logging

from app.core.database import get_db
from app.datacuti import schemas, crud, models
from app.autentikasi.security import verify_firebase_token
# Perbaikan: Mengganti get_user dengan nama fungsi yang benar get_user_by_uid
from app.users.crud import get_user_by_uid
from app.users import models as user_models

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

def get_user_role(db: Session, user_uid: str) -> Optional[str]:
    """Mengambil nama peran (role) pengguna dari database."""
    # Perbaikan: Menggunakan fungsi yang benar
    db_user = get_user_by_uid(db, user_uid)
    if db_user and db_user.role:
        return db_user.role.name
    return None

@router.post("/", response_model=schemas.CutiInDB, status_code=status.HTTP_201_CREATED)
def create_new_cuti(
    cuti: schemas.CutiCreate,
    db: Session = Depends(get_db),
    current_user_token: dict = Depends(verify_firebase_token)
):
    """
    Membuat pengajuan cuti baru.
    Pengajuan hanya bisa dibuat untuk user ID yang sedang login.
    """
    if cuti.user_uid != current_user_token.get('uid'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda hanya dapat membuat pengajuan cuti untuk ID pengguna Anda sendiri."
        )

    # Perbaikan: Menggunakan fungsi yang benar
    db_user = get_user_by_uid(db, cuti.user_uid)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID Pengguna tidak ditemukan.")

    if cuti.tanggal_mulai < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tanggal mulai cuti tidak boleh di masa lalu."
        )

    masa_kerja_years = crud.calculate_masa_kerja_years(db_user.joinDate)
    masa_kerja_months = crud.calculate_masa_kerja_months(db_user.joinDate)
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

    if cuti.masa_cuti_tambahan is not None and cuti.masa_cuti_tambahan > 0:
        if cuti.potongan_gaji_opsi is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Opsi potongan gaji harus dipilih jika ada masa cuti tambahan."
            )
        masa_cuti_dari_jatah = cuti.masa_cuti - cuti.masa_cuti_tambahan
        if masa_cuti_dari_jatah < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Masa cuti dari jatah tidak boleh negatif. Pastikan masa cuti tambahan tidak melebihi total masa cuti yang diajukan."
            )
        if masa_cuti_dari_jatah > jatah_cuti_dasar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Jumlah hari cuti dari jatah ({masa_cuti_dari_jatah} hari) melebihi jatah yang tersedia ({jatah_cuti_dasar} hari)."
            )
    elif cuti.masa_cuti_tambahan is not None and cuti.masa_cuti_tambahan == 0:
        if cuti.potongan_gaji_opsi is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Masa cuti tambahan tidak boleh nol jika opsi potongan gaji dipilih."
            )
        if cuti.masa_cuti > jatah_cuti_dasar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Jumlah hari cuti yang diajukan ({cuti.masa_cuti} hari) melebihi jatah yang tersedia ({jatah_cuti_dasar} hari)."
            )
    else:
        if cuti.potongan_gaji_opsi is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Masa cuti tambahan harus diisi jika opsi potongan gaji dipilih."
            )
        if cuti.masa_cuti > jatah_cuti_dasar and cuti.jenis_cuti != "Cuti Melahirkan":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Jumlah hari cuti yang diajukan ({cuti.masa_cuti} hari) melebihi jatah yang tersedia ({jatah_cuti_dasar} hari)."
            )

    if cuti.jenis_cuti == "Mix":
        if not cuti.detail_mix_cuti:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Detail mix cuti harus disediakan jika jenis cuti adalah 'Mix'."
            )

        total_non_maternity_mix_cuti = 0
        min_start_date_mix = date(9999, 12, 31)
        max_end_date_mix = date(1, 1, 1)

        for i, detail in enumerate(cuti.detail_mix_cuti):
            if detail.jenis not in ["Cuti Kerja", "Cuti Lokal", "Cuti Indonesia", "Cuti Melahirkan"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Jenis cuti tidak valid dalam detail mix cuti ke-{i+1}.")

            if detail.tanggal_mulai_sub > detail.tanggal_akhir_sub:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tanggal mulai sub-cuti ke-{i+1} tidak boleh setelah tanggal akhir sub-cuti.")

            calculated_masa_cuti_sub = (detail.tanggal_akhir_sub - detail.tanggal_mulai_sub).days + 1
            if detail.masa_cuti_sub != calculated_masa_cuti_sub:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                     detail=f"Masa cuti sub-cuti ke-{i+1} ({detail.masa_cuti_sub} hari) tidak konsisten dengan tanggal ({calculated_masa_cuti_sub} hari).")

            if detail.jenis == "Cuti Melahirkan":
                if detail.masa_cuti_sub != 90:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Masa cuti untuk Cuti Melahirkan dalam Mix harus 90 hari (detail ke-{i+1}).")
                if detail.passport_sub is not True:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Untuk Cuti Melahirkan dalam Mix, ambil passport harus bernilai True (detail ke-{i+1}).")
            elif detail.jenis == "Cuti Indonesia":
                if detail.passport_sub is not True:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Untuk Cuti Indonesia dalam Mix, ambil passport harus bernilai True (detail ke-{i+1}).")
            elif detail.jenis in ["Cuti Kerja", "Cuti Lokal"]:
                if detail.passport_sub not in [True, False, None]:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Untuk {detail.jenis} dalam Mix, pilihan passport tidak valid. Harusnya True, False, atau null (detail ke-{i+1}).")

            if detail.jenis != "Cuti Melahirkan":
                total_non_maternity_mix_cuti += detail.masa_cuti_sub

            if detail.tanggal_mulai_sub < min_start_date_mix:
                min_start_date_mix = detail.tanggal_mulai_sub
            if detail.tanggal_akhir_sub > max_end_date_mix:
                max_end_date_mix = detail.tanggal_akhir_sub

        if total_non_maternity_mix_cuti > jatah_cuti_dasar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total masa cuti (non-Melahirkan) dalam Mix ({total_non_maternity_mix_cuti} hari) melebihi jatah yang tersedia ({jatah_cuti_dasar} hari)."
            )

        if cuti.tanggal_mulai != min_start_date_mix:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tanggal mulai cuti global harus sama dengan tanggal mulai sub-cuti paling awal dalam Mix."
            )

        global_total_days = cuti.masa_cuti
        calculated_global_end_date = cuti.tanggal_mulai + timedelta(days=global_total_days - 1)

        if calculated_global_end_date != max_end_date_mix:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tanggal akhir cuti global tidak konsisten dengan rentang sub-cuti paling akhir dalam Mix."
            )

    elif cuti.jenis_cuti == "Cuti Melahirkan":
        if cuti.masa_cuti != 90:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Masa cuti untuk Cuti Melahirkan harus 90 hari.")
        if cuti.passport is not True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Untuk {cuti.jenis_cuti}, ambil passport harus bernilai True."
            )
    elif cuti.jenis_cuti == "Cuti Indonesia":
        if cuti.passport is not True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Untuk {cuti.jenis_cuti}, ambil passport harus bernilai True."
            )
    elif cuti.jenis_cuti in ["Cuti Kerja", "Cuti Lokal"]:
        if cuti.passport not in [True, False, None]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Untuk {cuti.jenis_cuti}, pilihan passport tidak valid. Harusnya True, False, atau null."
            )

    if cuti.jenis_cuti != "Mix" and cuti.detail_mix_cuti is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Detail mix cuti hanya diizinkan jika jenis_cuti adalah 'Mix'."
        )

    db_cuti = crud.create_cuti(db=db, cuti=cuti)
    if not db_cuti:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal membuat pengajuan cuti.")
    return db_cuti

@router.get("/", response_model=List[schemas.CutiInDB])
def read_all_cuti(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[schemas.CutiStatus] = None,
    db: Session = Depends(get_db),
    current_user_token: dict = Depends(verify_firebase_token)
):
    """
    Mengambil semua pengajuan cuti.
    Semua pengguna dapat melihat daftar cuti.
    """
    try:
        all_cuti = crud.get_all_cuti(db, skip=skip, limit=limit, status=status_filter)
        if not all_cuti:
            logger.info("Tidak ada pengajuan cuti ditemukan.")
            return []
        return all_cuti
    except Exception as e:
        logger.error(f"Error saat mengambil semua pengajuan cuti: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Terjadi kesalahan saat mengambil data cuti.")

@router.get("/{cuti_id}", response_model=schemas.CutiInDB)
def read_cuti_by_id(
    cuti_id: int,
    db: Session = Depends(get_db),
    current_user_token: dict = Depends(verify_firebase_token)
):
    """Mengambil detail pengajuan cuti berdasarkan ID."""
    db_cuti = crud.get_cuti(db, cuti_id=cuti_id)
    if db_cuti is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pengajuan cuti tidak ditemukan")

    current_user_role = get_user_role(db, current_user_token.get('uid'))
    can_view_cuti = (
        db_cuti.user_uid == current_user_token.get('uid') or
        current_user_role in ["Admin", "SuperAdmin", "Leader", "Manager"]
    )

    if not can_view_cuti:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Anda tidak berwenang melihat pengajuan cuti ini.")

    return db_cuti

@router.get("/user/{user_uid}", response_model=List[schemas.CutiInDB])
def read_user_cuti(
    user_uid: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user_token: dict = Depends(verify_firebase_token)
):
    """Mengambil semua pengajuan cuti untuk user ID tertentu."""
    current_user_role = get_user_role(db, current_user_token.get('uid'))
    can_view_user_cuti = (
        user_uid == current_user_token.get('uid') or
        current_user_role in ["Admin", "SuperAdmin", "Leader", "Manager"]
    )

    if not can_view_user_cuti:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Anda tidak berwenang melihat pengajuan cuti pengguna ini.")

    cuti_list = crud.get_cuti_by_user_uid(db, user_uid=user_uid, skip=skip, limit=limit)
    return cuti_list

@router.put("/{cuti_id}", response_model=schemas.CutiInDB)
def update_existing_cuti(
    cuti_id: int,
    cuti_update: schemas.CutiUpdate,
    db: Session = Depends(get_db),
    current_user_token: dict = Depends(verify_firebase_token)
):
    """
    Memperbarui pengajuan cuti yang sudah ada.
    Hanya pemilik cuti atau admin/superadmin/leader/manager yang dapat memperbarui.
    Admin/Superadmin/Leader/Manager memiliki kontrol lebih banyak atas field yang dapat diperbarui.
    """
    db_cuti = crud.get_cuti(db, cuti_id=cuti_id)
    if db_cuti is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pengajuan cuti tidak ditemukan")

    current_user_role = get_user_role(db, current_user_token.get('uid'))

    allowed_editor_roles = ["Admin", "SuperAdmin", "Leader", "Manager"]
    is_allowed_editor = current_user_role in allowed_editor_roles

    if db_cuti.user_uid != current_user_token.get('uid') and not is_allowed_editor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Anda tidak berwenang memperbarui pengajuan cuti ini.")

    if not is_allowed_editor:
        if (cuti_update.status is not None or
            cuti_update.by is not None or
            cuti_update.jenis_cuti is not None or
            cuti_update.masa_cuti is not None or
            cuti_update.masa_cuti_tambahan is not None or
            cuti_update.potongan_gaji_opsi is not None or
            cuti_update.detail_mix_cuti is not None or
            cuti_update.edit_by is not None):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                 detail="Sebagai pengguna biasa, Anda hanya dapat mengubah keterangan atau lampiran cuti pending Anda sendiri.")
        if db_cuti.status != "Pending":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Anda hanya dapat mengedit pengajuan cuti yang berstatus 'Pending'.")

    current_masa_cuti = cuti_update.masa_cuti if cuti_update.masa_cuti is not None else db_cuti.masa_cuti
    current_masa_cuti_tambahan = cuti_update.masa_cuti_tambahan if cuti_update.masa_cuti_tambahan is not None else db_cuti.masa_cuti_tambahan
    current_potongan_gaji_opsi = cuti_update.potongan_gaji_opsi if cuti_update.potongan_gaji_opsi is not None else db_cuti.potongan_gaji_opsi

    if current_masa_cuti_tambahan is not None and current_masa_cuti_tambahan > 0:
        if current_potongan_gaji_opsi is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Opsi potongan gaji harus dipilih jika ada masa cuti tambahan."
            )
        masa_cuti_dari_jatah = current_masa_cuti - current_masa_cuti_tambahan
        if masa_cuti_dari_jatah < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Masa cuti dari jatah tidak boleh negatif. Pastikan masa cuti tambahan tidak melebihi total masa cuti yang diajukan."
            )
    elif current_masa_cuti_tambahan is not None and current_masa_cuti_tambahan == 0:
        if current_potongan_gaji_opsi is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Masa cuti tambahan tidak boleh nol jika opsi potongan gaji dipilih."
            )
    else:
        if current_potongan_gaji_opsi is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Masa cuti tambahan harus diisi jika opsi potongan gaji dipilih."
            )

    if current_masa_cuti_tambahan is not None and current_masa_cuti_tambahan < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Masa cuti tambahan tidak boleh negatif."
        )

    # Perbaikan: Menggunakan fungsi yang benar
    db_user = get_user_by_uid(db, db_cuti.user_uid)
    masa_kerja_years = crud.calculate_masa_kerja_years(db_user.joinDate)
    masa_kerja_months = crud.calculate_masa_kerja_months(db_user.joinDate)
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

    masa_cuti_dari_jatah_update = current_masa_cuti - (current_masa_cuti_tambahan if current_masa_cuti_tambahan is not None else 0)

    if db_cuti.jenis_cuti != "Cuti Melahirkan" and masa_cuti_dari_jatah_update > jatah_cuti_dasar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Jumlah hari cuti dari jatah ({masa_cuti_dari_jatah_update} hari) melebihi jatah yang tersedia ({jatah_cuti_dasar} hari)."
        )

    target_jenis_cuti = cuti_update.jenis_cuti if cuti_update.jenis_cuti is not None else db_cuti.jenis_cuti

    if target_jenis_cuti == "Mix":
        current_detail_mix_cuti = cuti_update.detail_mix_cuti
        if current_detail_mix_cuti is None and db_cuti.detail_mix_cuti:
            try:
                current_detail_mix_cuti = [schemas.SubCutiDetail(**d) for d in json.loads(db_cuti.detail_mix_cuti)]
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to parse existing Mix Cuti details for cuti_id {cuti_id}: {e}", exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to parse existing Mix Cuti details.")

        if not current_detail_mix_cuti:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Detail mix cuti harus disediakan jika jenis cuti adalah 'Mix'."
            )

        total_non_maternity_mix_cuti_update = 0
        min_start_date_mix_update = date(9999, 12, 31)
        max_end_date_mix_update = date(1, 1, 1)

        for i, detail in enumerate(current_detail_mix_cuti):
            if detail.jenis not in ["Cuti Kerja", "Cuti Lokal", "Cuti Indonesia", "Cuti Melahirkan"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Jenis cuti tidak valid dalam detail mix cuti ke-{i+1}.")

            if detail.tanggal_mulai_sub > detail.tanggal_akhir_sub:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tanggal mulai sub-cuti ke-{i+1} tidak boleh setelah tanggal akhir sub-cuti.")

            calculated_masa_cuti_sub = (detail.tanggal_akhir_sub - detail.tanggal_mulai_sub).days + 1
            if detail.masa_cuti_sub != calculated_masa_cuti_sub:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                     detail=f"Masa cuti sub-cuti ke-{i+1} ({detail.masa_cuti_sub} hari) tidak konsisten dengan tanggal ({calculated_masa_cuti_sub} hari).")

            if detail.jenis == "Cuti Melahirkan":
                if detail.masa_cuti_sub != 90:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Masa cuti untuk Cuti Melahirkan dalam Mix harus 90 hari (detail ke-{i+1}).")
                if detail.passport_sub is not True:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Untuk Cuti Melahirkan dalam Mix, ambil passport harus bernilai True (detail ke-{i+1}).")
            elif detail.jenis == "Cuti Indonesia":
                if detail.passport_sub is not True:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Untuk Cuti Indonesia dalam Mix, ambil passport harus bernilai True (detail ke-{i+1}).")
            elif detail.jenis in ["Cuti Kerja", "Cuti Lokal"]:
                if detail.passport_sub not in [True, False, None]:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Untuk {detail.jenis} dalam Mix, pilihan passport tidak valid. Harusnya True, False, atau null (detail ke-{i+1}).")

            if detail.jenis != "Cuti Melahirkan":
                total_non_maternity_mix_cuti_update += detail.masa_cuti_sub

            if detail.tanggal_mulai_sub < min_start_date_mix_update:
                min_start_date_mix_update = detail.tanggal_mulai_sub
            if detail.tanggal_akhir_sub > max_end_date_mix_update:
                max_end_date_mix_update = detail.tanggal_akhir_sub

        if total_non_maternity_mix_cuti_update > jatah_cuti_dasar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total masa cuti (non-Melahirkan) dalam Mix ({total_non_maternity_mix_cuti_update} hari) melebihi jatah yang tersedia ({jatah_cuti_dasar} hari)."
            )

        current_global_start_date = cuti_update.tanggal_mulai if cuti_update.tanggal_mulai is not None else db_cuti.tanggal_mulai
        current_global_masa_cuti_total = current_masa_cuti
        calculated_global_end_date = current_global_start_date + timedelta(days=current_global_masa_cuti_total - 1)

        if current_global_start_date != min_start_date_mix_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tanggal mulai cuti global harus sama dengan tanggal mulai sub-cuti paling awal dalam Mix."
            )
        if calculated_global_end_date != max_end_date_mix_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tanggal akhir cuti global tidak konsisten dengan rentang sub-cuti paling akhir dalam Mix."
            )
    elif target_jenis_cuti == "Cuti Melahirkan":
        if cuti_update.masa_cuti is not None and cuti_update.masa_cuti != 90:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Masa cuti untuk Cuti Melahirkan harus 90 hari.")
        if (cuti_update.passport is not None and cuti_update.passport is not True) or \
           (cuti_update.passport is None and db_cuti.passport is not True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Untuk {target_jenis_cuti}, ambil passport harus bernilai True."
            )
    elif target_jenis_cuti == "Cuti Indonesia":
        if (cuti_update.passport is not None and cuti_update.passport is not True) or \
           (cuti_update.passport is None and db_cuti.passport is not True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Untuk {target_jenis_cuti}, ambil passport harus bernilai True."
            )
    elif target_jenis_cuti in ["Cuti Kerja", "Cuti Lokal"]:
        if cuti_update.passport is not None and cuti_update.passport not in [True, False, None]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Untuk {target_jenis_cuti}, pilihan passport tidak valid. Harusnya True, False, atau null."
            )

    if target_jenis_cuti != "Mix" and (cuti_update.detail_mix_cuti is not None or db_cuti.detail_mix_cuti is not None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Detail mix cuti hanya diizinkan jika jenis_cuti adalah 'Mix'."
        )

    if is_allowed_editor and cuti_update.status is not None and cuti_update.status != db_cuti.status:
        cuti_update.by = current_user_token.get('uid')
    elif cuti_update.status is None:
        pass

    cuti_update.edit_by = current_user_token.get('uid')

    updated_cuti = crud.update_cuti(db, cuti_id=cuti_id, cuti_update=cuti_update)
    if updated_cuti is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal memperbarui pengajuan cuti.")
    return updated_cuti

@router.delete("/{cuti_id}", status_code=status.HTTP_200_OK)
def delete_existing_cuti(
    cuti_id: int,
    db: Session = Depends(get_db),
    current_user_token: dict = Depends(verify_firebase_token)
):
    """
    Menghapus pengajuan cuti.
    Hanya pemilik cuti atau admin/superadmin yang dapat menghapus.
    Ada batasan status cuti yang dapat dihapus.
    """
    db_cuti = crud.get_cuti(db, cuti_id=cuti_id)
    if db_cuti is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pengajuan cuti tidak ditemukan")

    current_user_role = get_user_role(db, current_user_token.get('uid'))
    is_admin_or_superadmin = current_user_role in ["Admin", "SuperAdmin"]

    if db_cuti.user_uid != current_user_token.get('uid') and not is_admin_or_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Anda tidak berwenang menghapus pengajuan cuti ini.")

    if db_cuti.status not in ["Pending", "Reject"] and not is_admin_or_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Anda hanya dapat menghapus pengajuan cuti yang berstatus 'Pending' atau 'Reject'.")

    is_deleted = crud.delete_cuti(db, cuti_id=cuti_id)
    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal menghapus pengajuan cuti.")
    return {"message": "Pengajuan cuti berhasil dihapus"}