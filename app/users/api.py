# backend/app/users/api.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.users.schemas import User # Import the full User schema
from app.users import crud as crud_user
from app.fcm import crud as fcm_crud
from app.fcm.schemas import FCMTokenCreate
from pydantic import BaseModel

router = APIRouter()

class FCMSubscribe(BaseModel):
    fcm_token: str
    user_uid: str

@router.get("/{user_uid}", response_model=User) # Use the full User schema here
def read_user_by_uid(user_uid: str, db: Session = Depends(get_db)):
    db_user = crud_user.get_user_by_uid(db, user_uid=user_uid)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/fcm_token/subscribe")
def subscribe_fcm_token(
    fcm_data: FCMSubscribe,
    db: Session = Depends(get_db)
):
    try:
        fcm_crud.create_fcm_token_and_subscribe(db, fcm_data.user_uid, fcm_data.fcm_token)
        return {"message": "Token berhasil disimpan dan berlangganan ke topik."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))