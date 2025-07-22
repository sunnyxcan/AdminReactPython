# backend/app/auth.py

import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Perhatikan ini, sebelumnya OAuth2Bearer
from .config import settings # Impor settings dari config.py
from .database import get_db
from sqlalchemy.orm import Session
from . import crud, models, schemas
import os
import json # Tambahkan impor json

# Inisialisasi Firebase Admin SDK
# Ini harus menjadi satu-satunya tempat Firebase diinisialisasi
if not firebase_admin._apps: # Cek jika Firebase sudah diinisialisasi
    try:
        # Dapatkan string JSON kredensial dari variabel lingkungan
        # Pastikan FIREBASE_SERVICE_ACCOUNT_KEY diatur di Vercel
        firebase_config_json = settings.FIREBASE_SERVICE_ACCOUNT_KEY

        if firebase_config_json:
            # Parse string JSON menjadi dictionary
            cred_dict = json.loads(firebase_config_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully from environment variable.")
        else:
            # Ini seharusnya tidak terjadi jika env var diatur di Vercel
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY environment variable not set.")

    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse FIREBASE_SERVICE_ACCOUNT_KEY JSON: {e}")
    except ValueError as e:
        raise RuntimeError(f"Initialization error: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Firebase Admin SDK: {e}")

# Perhatikan: Sesuaikan ini jika Anda menggunakan FastAPI authentication secara penuh
# Untuk demo ini, kita mungkin tidak memerlukannya karena otentikasi ditangani oleh Firebase
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Menggunakan OAuth2PasswordBearer

async def get_current_user_from_firebase(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Verifies Firebase ID token and returns the authenticated user's Employee object.
    If the user does not exist in our database, it creates a new Employee entry for them.
    """
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        firebase_uid = decoded_token['uid']
        user_email = decoded_token.get('email')
        user_name = decoded_token.get('name')

        # Check if user exists in our local database
        db_user = crud.get_employee_by_firebase_uid(db, firebase_uid=firebase_uid)

        if not db_user:
            # If user doesn't exist, create a new entry for them
            if user_email and user_name:
                employee_create = schemas.EmployeeCreate(
                    name=user_name,
                    email=user_email,
                    position="General Staff" # Default position, bisa diubah admin nanti
                )
                db_user = crud.create_employee(db=db, employee=employee_create, firebase_uid=firebase_uid)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials: User not found and email/name missing from token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return db_user
    except firebase_admin.exceptions.FirebaseError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during authentication: {e}"
        )

async def get_current_admin_user(current_user: models.Employee = Depends(get_current_user_from_firebase)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user