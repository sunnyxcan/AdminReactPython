# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.dataizin import api as izin_endpoints
from app.izin_rules import api as izin_rules_endpoints
from app.users import api as user_endpoints
from app.services import ip as ip_endpoints
from app.fcm import models as fcm_models

# Tambahkan impor eksplisit untuk model-model yang ingin Anda buat tabelnya.
# Ini memastikan SQLAlchemy melihat semua model saat create_all dipanggil.
from app.dataizin import models as izin_models
from app.users import models as user_models
from app.izin_rules import models as izin_rules_models # <-- Ini yang paling penting
from app.datatelat.api import router as datatelat_router

# Membuat tabel di database (jika belum ada).
# Baris ini akan berjalan saat server dimulai dan membuat tabel untuk semua model yang diimpor.
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

app.include_router(user_endpoints.router, prefix="/api/users", tags=["Users"])
app.include_router(ip_endpoints.router, prefix="/api/ip", tags=["IP"])
app.include_router(izin_endpoints.router, prefix="/api/izin", tags=["Izin"])
app.include_router(izin_rules_endpoints.router, prefix="/api/izin_rules", tags=["Izin_Rules"])
app.include_router(datatelat_router, prefix="/api/datatelat", tags=["datatelat"])

@app.get("/")
def read_root():
    return {"message": "Selamat datang di Admin Panel API"}