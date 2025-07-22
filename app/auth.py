# backend/app/auth.py

import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2Bearer
from .config import settings
from .database import get_db
from sqlalchemy.orm import Session
from . import crud, models, schemas
import os

# Inisialisasi Firebase Admin SDK
# Pastikan file service account JSON ada
try:
    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    # Jika ini terjadi saat startup, ada masalah serius
    # Anda bisa memilih untuk raise exception atau log dan lanjutkan dengan functionalitas terbatas
    raise RuntimeError(f"Failed to initialize Firebase Admin SDK: {e}")

oauth2_scheme = OAuth2Bearer(tokenUrl="token") # tokenUrl tidak digunakan di sini untuk login, tapi untuk swagger docs

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