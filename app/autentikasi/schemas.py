# app/autentikasi/schemas.py

# Misalnya, jika Anda ingin mengirim informasi token dari backend untuk tujuan tertentu
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None