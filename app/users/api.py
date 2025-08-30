# backend/app/users/api.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.users.schemas import User, UserCreate, UserUpdate, UserCreateByAdmin, PasswordUpdate
from app.users import crud as crud_user
from app.fcm import crud as fcm_crud
from app.fcm.schemas import FCMTokenCreate
from pydantic import BaseModel
from typing import List, Optional
from firebase_admin import auth
from app.core.firebase import get_firebase_auth
from app.utils.device_utils import detect_device_info

router = APIRouter()

def get_firebase_auth_instance():
    return get_firebase_auth()

@router.get("/", response_model=List[User])
def read_all_users(db: Session = Depends(get_db), skip: int = 0, limit: Optional[int] = None):
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_uid}", response_model=User)
def read_user_by_uid(user_uid: str, db: Session = Depends(get_db)):
    db_user = crud_user.get_user_by_uid(db, user_uid=user_uid)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_new_user(user_data: UserCreateByAdmin, db: Session = Depends(get_db), firebase_auth = Depends(get_firebase_auth_instance)):
    db_user_by_email_local = crud_user.get_user_by_email(db, email=user_data.email)
    if db_user_by_email_local:
        raise HTTPException(status_code=400, detail="Email ini sudah terdaftar di database lokal.")

    if not user_data.role_id:
        raise HTTPException(status_code=400, detail="Role ID must be provided")

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
    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ini sudah terdaftar di Firebase.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membuat akun Firebase: {e}")

    try:
        user_create_data = UserCreate(
            uid=new_uid,
            fullname=user_data.fullname,
            nickname=user_data.nickname,
            gender=user_data.gender,
            jabatan=user_data.jabatan,
            imageUrl=user_data.imageUrl,
            email=user_data.email,
            role_id=user_data.role_id,
            status=user_data.status,
            joinDate=user_data.joinDate,
            grupDate=user_data.grupDate,
            tanggalAkhirCuti=user_data.tanggalAkhirCuti,
            no_passport=user_data.no_passport
        )
        created_user_in_db = crud_user.create_user_by_admin(db=db, user_data=user_create_data)
        return created_user_in_db
    except Exception as e:
        if new_uid:
            try:
                auth.delete_user(new_uid)
            except Exception as delete_e:
                pass
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan data pengguna ke database lokal: {e}")

@router.put("/{user_id}", response_model=User)
def update_existing_user(user_id: str, user_data: UserUpdate, db: Session = Depends(get_db)):
    db_user = crud_user.get_user_by_uid(db, user_uid=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return crud_user.update_user(db=db, db_user=db_user, user_data=user_data)

@router.put("/{user_id}/password-reset")
def reset_user_password(
    user_id: str, 
    password_data: PasswordUpdate, 
    firebase_auth = Depends(get_firebase_auth_instance)
):
    try:
        auth.update_user(user_id, password=password_data.password)
        return {"message": "Password updated successfully"}
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan di Firebase.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mereset kata sandi: {e}")

@router.delete("/{user_id}")
def delete_user_by_id(user_id: str, db: Session = Depends(get_db)):
    db_user = crud_user.get_user_by_uid(db, user_uid=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    crud_user.delete_user(db=db, db_user=db_user)
    
    try:
        auth.delete_user(user_id)
    except auth.UserNotFoundError:
        pass
    except Exception as e:
        pass
        
    return {"message": "User deleted successfully"}

@router.post("/fcm_token/subscribe")
def subscribe_fcm_token(
    fcm_data: FCMTokenCreate,
    db: Session = Depends(get_db),
    request: Request = None
):
    try:
        user_agent_string = request.headers.get("User-Agent")
        device_info = detect_device_info(user_agent_string)
        
        fcm_crud.create_fcm_token(db, fcm_data.user_uid, fcm_data.fcm_token, device_info)
        
        return {"message": "Token berhasil disimpan."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))