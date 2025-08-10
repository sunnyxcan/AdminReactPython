# app/listjob/crud.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict, Tuple
import re 

from app.listjob import models, schemas

ALL_BANKS = {
    "BCA": "Bank BCA",
    "BNI": "Bank BNI",
    "MANDIRI": "Bank Mandiri",
    "BRI": "Bank BRI",
    "BANK KECIL": "bank kecil", 
}

ALL_EWALLETS = {
    "DANA": "E-wallet DANA",
    "OVO": "E-wallet OVO",
    "LINK": "E-wallet LinkAja", 
    "LINKAJA": "E-wallet LinkAja",
    "GOPAY": "E-wallet GoPay",
}


def get_list_job_category(db: Session, category_id: int):
    """
    Mengambil satu kategori list job berdasarkan ID dengan eager loading relasi user pembuat dan pengubah.
    """
    return db.query(models.ListJobCategory)\
             .options(joinedload(models.ListJobCategory.created_by_user))\
             .options(joinedload(models.ListJobCategory.modified_by_user))\
             .filter(models.ListJobCategory.id == category_id).first()

def get_list_job_category_by_name(db: Session, nama: str):
    """
    Mengambil satu kategori list job berdasarkan nama.
    """
    return db.query(models.ListJobCategory).filter(models.ListJobCategory.nama == nama).first()

def get_list_job_categories(db: Session, skip: int = 0, limit: int = 100):
    """
    Mengambil daftar semua kategori list job dengan paginasi,
    serta eager loading relasi user pembuat dan pengubah.
    """
    return db.query(models.ListJobCategory)\
             .options(joinedload(models.ListJobCategory.created_by_user))\
             .options(joinedload(models.ListJobCategory.modified_by_user))\
             .offset(skip).limit(limit).all()

def generate_dynamic_description(category_name: str) -> Optional[str]:
    """
    Membangun deskripsi otomatis untuk DEPO/WD berdasarkan bank/e-wallet yang ditemukan,
    dengan urutan yang sesuai dengan kemunculan di nama kategori.
    """
    name_upper = category_name.upper()
    
    transaction_type = None
    if "DEPO" in name_upper:
        transaction_type = "deposit"
    elif "WD" in name_upper:
        transaction_type = "withdrawal"
    
    if not transaction_type:
        return None 

    all_entities_map = {**ALL_BANKS, **ALL_EWALLETS}
    
    found_entities_with_index: Dict[str, int] = {} 

    sorted_entity_keys = sorted(all_entities_map.keys(), key=len, reverse=True)

    for entity_key in sorted_entity_keys:
        for match in re.finditer(r'\b' + re.escape(entity_key) + r'\b', name_upper):
            description = all_entities_map[entity_key]
            if description not in found_entities_with_index or match.start() < found_entities_with_index[description]:
                found_entities_with_index[description] = match.start()
    
    sorted_found_entities = sorted(found_entities_with_index.items(), key=lambda item: item[1])
    found_entities_ordered = [desc for desc, _ in sorted_found_entities]

    if found_entities_ordered:
        if len(found_entities_ordered) == 1:
            entities_str = found_entities_ordered[0]
        elif len(found_entities_ordered) == 2:
            entities_str = f"{found_entities_ordered[0]} dan {found_entities_ordered[1]}"
        else:
            entities_str = ", ".join(found_entities_ordered[:-1]) + f", dan {found_entities_ordered[-1]}"
        
        return f"Tugas khusus {transaction_type} via {entities_str}."
    
    return None 

def create_list_job_category(db: Session, category: schemas.ListJobCategoryCreate, createdBy_uid: str):
    """
    Membuat kategori list job baru.
    Jika deskripsi tidak diberikan, akan dibuat otomatis berdasarkan nama kategori.
    """
    
    # === PERUBAHAN DI SINI: Tambahkan aturan spesifik untuk "BONUS SCATTER" ===
    static_mapping_rules = [
        {"keywords": ["DURASI", "ANTRIAN", "DEPO"], "description": "Memantau durasi antrian deposit."},
        {"keywords": ["DURASI", "ANTRIAN", "WD"], "description": "Memantau durasi antrian withdrawal."},
        {"keywords": ["OPERATOR"], "description": "Manajemen tugas operator."},
        
        {"keywords": ["BONUS", "SCATTER", "LC"], "description": "Penanganan bonus scatter untuk game 'Lion Coins' (LC)."},
        {"keywords": ["BONUS", "SCATTER", "MARKETING"], "description": "Penanganan bonus scatter yang terkait dengan promosi atau marketing."},
        # Aturan baru untuk BONUS SCATTER yang tidak spesifik LC/MARKETING
        {"keywords": ["BONUS", "SCATTER"], "description": "Penanganan bonus scatter umum."}, 
        {"keywords": ["BONUS", "FREECHIPS"], "description": "Penanganan bonus freechips."},
        {"keywords": ["BUANG DANA"], "description": "Pengawasan saldo bank dan tugas melakukan transfer atau pemindahan dana saldo bank."},
        {"keywords": ["AUTO WD", "WD MANUAL"], "description": "Pengawasan dan eksekusi penarikan dana otomatis dan manual."},
        
        {"keywords": ["DEPO ALL"], "description": "Mengelola semua jenis deposit yang masuk."},
        {"keywords": ["PENDINGAN"], "description": "Tugas untuk menyelesaikan dan menutup pendingan."}, 

        # Aturan umum DEPO/WD/BONUS di paling bawah agar aturan yang lebih spesifik diutamakan
        {"keywords": ["DEPO"], "description": "Tugas umum terkait semua jenis deposit."}, 
        {"keywords": ["WD"], "description": "Tugas umum terkait semua jenis penarikan (withdrawal)."}, 
        {"keywords": ["BONUS"], "description": "Tugas umum terkait semua jenis bonus."},
    ]

    matched_descriptions_with_index: Dict[str, int] = {} 

    if category.deskripsi:
        final_deskripsi = category.deskripsi
    else:
        nama_upper = category.nama.upper()

        dynamic_desc = generate_dynamic_description(category.nama)
        if dynamic_desc:
            matched_descriptions_with_index[dynamic_desc] = 0 

        all_entity_keys_for_check = set(ALL_BANKS.keys()).union(set(ALL_EWALLETS.keys()))

        for rule in static_mapping_rules:
            is_depo_or_wd_general_rule = any(k in ["DEPO", "WD"] for k in rule["keywords"])
            if dynamic_desc and is_depo_or_wd_general_rule and \
               any(re.search(r'\b' + re.escape(ent_key.upper()) + r'\b', nama_upper) for ent_key in all_entity_keys_for_check):
                continue 
            
            is_operator_durasi_related_category = ("OPERATOR" in nama_upper and "DURASI" in nama_upper and "ANTRIAN" in nama_upper)
            if is_operator_durasi_related_category:
                if (("DEPO" in rule["keywords"] and "Memantau durasi antrian deposit." in matched_descriptions_with_index) or
                    ("WD" in rule["keywords"] and "Memantau durasi antrian withdrawal." in matched_descriptions_with_index)):
                    if rule["description"] == "Tugas umum terkait semua jenis deposit." or \
                       rule["description"] == "Tugas umum terkait semua jenis penarikan (withdrawal).":
                        continue

            # === PERUBAHAN DI SINI: Logika pencegahan duplikasi BONUS ===
            # Jika ada aturan BONUS yang lebih spesifik (misal BONUS SCATTER, BONUS FREECHIPS)
            # yang sudah cocok dan ditambahkan, jangan tambahkan aturan BONUS yang umum.
            if "BONUS" in rule["keywords"] and len(rule["keywords"]) == 1: # Ini adalah aturan BONUS umum
                has_specific_bonus_matched = False
                for existing_desc in matched_descriptions_with_index.keys():
                    if "bonus scatter" in existing_desc.lower() or "bonus freechips" in existing_desc.lower():
                        has_specific_bonus_matched = True
                        break
                if has_specific_bonus_matched:
                    continue # Lewati aturan BONUS umum jika yang spesifik sudah ada
            
            min_index = -1
            all_keywords_found = True
            for keyword in rule["keywords"]:
                match = re.search(r'\b' + re.escape(keyword.upper()) + r'\b', nama_upper)
                if not match:
                    all_keywords_found = False
                    break
                if min_index == -1 or match.start() < min_index:
                    min_index = match.start()
            
            if all_keywords_found:
                if rule["description"] not in matched_descriptions_with_index: 
                    # Jika dynamic_desc sudah ada dengan index 0, pastikan rule ini tidak menimpa index 0
                    if min_index == -1 and 0 in matched_descriptions_with_index.values():
                        matched_descriptions_with_index[rule["description"]] = float('inf') 
                    else:
                        matched_descriptions_with_index[rule["description"]] = min_index if min_index != -1 else float('inf')

        sorted_matched_descriptions = sorted(matched_descriptions_with_index.items(), key=lambda item: item[1])
        matched_descriptions_parts = [desc for desc, _ in sorted_matched_descriptions]

        if matched_descriptions_parts:
            if len(matched_descriptions_parts) == 1:
                final_deskripsi = matched_descriptions_parts[0]
            elif len(matched_descriptions_parts) == 2:
                final_deskripsi = f"{matched_descriptions_parts[0]} dan {matched_descriptions_parts[1]}"
            else:
                final_deskripsi = ", ".join(matched_descriptions_parts[:-1]) + f", dan {matched_descriptions_parts[-1]}"
        else:
            final_deskripsi = f"Tugas terkait dengan kategori: {category.nama}."


    db_category = models.ListJobCategory(
        nama=category.nama,
        deskripsi=final_deskripsi, 
        createdBy_uid=createdBy_uid
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    db_category = db.query(models.ListJobCategory)\
                     .options(joinedload(models.ListJobCategory.created_by_user))\
                     .options(joinedload(models.ListJobCategory.modified_by_user))\
                     .filter(models.ListJobCategory.id == db_category.id).first()
    return db_category

def update_list_job_category(db: Session, category_id: int, category_update: schemas.ListJobCategoryUpdate, modifiedBy_uid: str):
    """
    Memperbarui kategori list job yang sudah ada.
    """
    db_category = db.query(models.ListJobCategory).filter(models.ListJobCategory.id == category_id).first()
    if db_category:
        update_data = category_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_category, key, value)
        
        db_category.modifiedBy_uid = modifiedBy_uid 
        
        db.commit()
        db.refresh(db_category)
        db_category = db.query(models.ListJobCategory)\
                         .options(joinedload(models.ListJobCategory.created_by_user))\
                         .options(joinedload(models.ListJobCategory.modified_by_user))\
                         .filter(models.ListJobCategory.id == db_category.id).first()
    return db_category

def delete_list_job_category(db: Session, category_id: int):
    """
    Menghapus kategori list job berdasarkan ID.
    """
    db_category = db.query(models.ListJobCategory).filter(models.ListJobCategory.id == category_id).first()
    if db_category:
        db.delete(db_category)
        db.commit()
        return db_category
    return None