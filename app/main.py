# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.dataizin import api as izin_endpoints
from app.users import api as user_endpoints
from app.services import ip as ip_endpoints
from app.fcm import models as fcm_models # <-- Tambahkan baris ini

# Membuat tabel di database (jika belum ada)
# Sekarang, create_all akan melihat model FCMToken karena sudah diimpor
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Admin Panel API")

origins = [
    "http://localhost:5173",
    "http://localhost:8000",
    "https://adminreachpython.web.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(izin_endpoints.router, prefix="/api/izin", tags=["Izin"])
app.include_router(user_endpoints.router, prefix="/api/users", tags=["Users"])
app.include_router(ip_endpoints.router, prefix="/api/ip", tags=["IP"])

@app.get("/")
def read_root():
    return {"message": "Selamat datang di Admin Panel API"}