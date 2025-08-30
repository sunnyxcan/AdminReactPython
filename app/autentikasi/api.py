# app/autentikasi/api.py

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from firebase_admin import auth 
from app.core.firebase import get_firebase_auth

from app.core.database import get_db
from app.users import schemas as user_schemas
from app.users import crud as user_crud
from app.users import models as user_models
from app.roles import crud as role_crud
from app.autentikasi import security as auth_security
from app.logs.schemas import LogCreate
from app.logs.crud import create_log
from app.utils.ip_utils import get_request_ip
from app.utils.device_utils import detect_device_info

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"],
)

def get_firebase_auth_instance():
    return get_firebase_auth()

@router.post("/register_user/", response_model=user_schemas.UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user_from_firebase_signup(user_data: user_schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_by_uid = user_crud.get_user(db, user_data.uid)
    if db_user_by_uid:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pengguna dengan UID ini sudah terdaftar di database lokal.")

    db_user_by_email = user_crud.get_user_by_email(db, user_data.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pengguna dengan email ini sudah terdaftar di database lokal.")

    role = role_crud.get_role(db, role_id=user_data.role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID peran tidak valid diberikan.")

    new_user = user_crud.create_user(db=db, user=user_data)
    if not new_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal mendaftarkan pengguna di database lokal.")
    
    return new_user

@router.post("/login-with-log/", response_model=user_schemas.UserInDB)
async def login_with_log(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # 🆕 Dapatkan IP dan informasi perangkat dari request
    ip_address = get_request_ip(request)
    user_agent = request.headers.get("User-Agent")
    device_info = detect_device_info(user_agent)

    try:
        user_record = auth.get_user_by_email(form_data.username)
        db_user = user_crud.get_user_by_email(db, email=form_data.username)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Pengguna tidak ditemukan di database lokal.")

        # 🆕 Sertakan data IP dan perangkat saat membuat log
        log_data = LogCreate(
            action="LOGIN_SUCCESS",
            entity_name="User",
            entity_id=db_user.uid,
            details=f"Login berhasil untuk pengguna: {db_user.email}",
            created_by=db_user.uid,
            ip_address=ip_address,
            device_info=device_info
        )
        create_log(db, log_data)
        logger.info(f"Log login berhasil dibuat untuk user {db_user.uid}.")
        return db_user
    
    except auth.UserNotFoundError:
        # 🆕 Sertakan data IP dan perangkat saat membuat log gagal
        log_data_fail = LogCreate(
            action="LOGIN_FAILED",
            entity_name="User",
            entity_id="N/A",
            details=f"Login gagal: Pengguna dengan email {form_data.username} tidak ditemukan di Firebase.",
            ip_address=ip_address,
            device_info=device_info
        )
        create_log(db, log_data_fail)
        logger.warning(f"Percobaan login gagal untuk email: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kredensial tidak valid.")
    
    except Exception as e:
        # 🆕 Sertakan data IP dan perangkat saat membuat log gagal
        log_data_fail = LogCreate(
            action="LOGIN_FAILED",
            entity_name="User",
            entity_id="N/A",
            details=f"Login gagal untuk email {form_data.username}: {e}",
            ip_address=ip_address,
            device_info=device_info
        )
        create_log(db, log_data_fail)
        logger.error(f"Error saat login untuk email {form_data.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Terjadi kesalahan saat mencoba login.")

@router.post("/login/", response_model=user_schemas.UserInDB)
async def login(
    request: Request,
    current_user: user_models.User = Depends(auth_security.get_current_active_user),
    db: Session = Depends(get_db)
):
    # Endpoint ini sekarang hanya mengembalikan data pengguna,
    # log sudah ditangani oleh fungsi login-with-log
    return current_user

@router.get("/verify-auth/", response_model=user_schemas.UserInDB)
async def verify_auth_status(
    current_user: user_models.User = Depends(auth_security.get_current_active_user)
):
    return current_user

@router.post("/admin/create_user/", response_model=user_schemas.UserInDB, status_code=status.HTTP_201_CREATED)
async def create_new_user_by_admin(
    user_data: user_schemas.UserCreateByAdmin,
    db: Session = Depends(get_db),
    firebase_auth = Depends(get_firebase_auth_instance)
):
    db_user_by_email_local = user_crud.get_user_by_email(db, email=user_data.email)
    if db_user_by_email_local:
        raise HTTPException(status_code=400, detail="Email ini sudah terdaftar di database lokal.")

    db_role = role_crud.get_role(db, role_id=user_data.role_id)
    if not db_role:
        raise HTTPException(status_code=400, detail="Invalid role_id provided")

    new_uid = None
    try:
        firebase_user_record = auth.create_user(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.fullname,
            email_verified=False,
            disabled=False
        )
        new_uid = firebase_user_record.uid
        logger.info(f"Pengguna Firebase baru dibuat: {new_uid}")

    except auth.EmailAlreadyExistsError:
        logger.warning(f"Percobaan membuat pengguna dengan email yang sudah ada di Firebase: {user_data.email}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ini sudah terdaftar di Firebase.")
    except Exception as e:
        logger.error(f"Gagal membuat akun Firebase: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal membuat akun Firebase: {e}")

    try:
        user_create_data = user_schemas.UserCreate(
            uid=new_uid,
            email=user_data.email,
            imageUrl=user_data.imageUrl,
            fullname=user_data.fullname,
            nickname=user_data.nickname,
            gender=user_data.gender,
            jabatan=user_data.jabatan,
            joinDate=user_data.joinDate,
            grupDate=user_data.grupDate,
            role_id=user_data.role_id,
            status=user_data.status,
        )
        created_user_in_db = user_crud.create_user(db=db, user=user_create_data)
        logger.info(f"Pengguna berhasil disimpan ke database lokal: {created_user_in_db.uid}")
        return created_user_in_db

    except Exception as e:
        logger.error(f"Gagal menyimpan data pengguna ke database lokal setelah membuat di Firebase: {e}", exc_info=True)
        if new_uid:
            try:
                auth.delete_user(new_uid)
                logger.warning(f"User {new_uid} dihapus dari Firebase Auth karena gagal disimpan ke DB lokal.")
            except Exception as delete_e:
                logger.error(f"Gagal menghapus user {new_uid} dari Firebase Auth setelah error DB lokal: {delete_e}")
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan data pengguna ke database lokal: {e}")