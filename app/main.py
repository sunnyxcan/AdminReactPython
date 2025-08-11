# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine

# Import endpoint (router) dari setiap modul
from app.dataizin import api as izin_endpoints
from app.izin_rules import api as izin_rules_endpoints
from app.users import api as user_endpoints
from app.roles import api as role_endpoints
from app.services import ip as ip_endpoints
from app.datatelat.api import router as datatelat_router

# --- PERUBAHAN BARU ---
from app.datajobdesk.api import router as datajobdesk_router
from app.datashift.api import router as datashift_router
from app.listjob.api import router as listjob_router
# --- AKHIR PERUBAHAN BARU ---

# ⭐ TAMBAHKAN INI UNTUK CUTI
from app.datacuti.api import router as datacuti_router

# Import model-model untuk pembuatan tabel
from app.fcm import models as fcm_models
from app.dataizin import models as izin_models
from app.users import models as user_models
from app.izin_rules import models as izin_rules_models
from app.roles import models as role_models
from app.datatelat import models as datatelat_models
# --- PERUBAHAN BARU ---
from app.datajobdesk import models as datajobdesk_models
from app.datashift import models as datashift_models
from app.listjob import models as listjob_models
# --- AKHIR PERUBAHAN BARU ---

# ⭐ TAMBAHKAN INI UNTUK MODEL CUTI
from app.datacuti import models as datacuti_models

# Membuat tabel di database (jika belum ada).
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
app.include_router(role_endpoints.router, prefix="/api/roles", tags=["Roles"])
app.include_router(ip_endpoints.router, prefix="/api/ip", tags=["IP"])
app.include_router(izin_endpoints.router, prefix="/api/izin", tags=["Izin"])
app.include_router(izin_rules_endpoints.router, prefix="/api/izin_rules", tags=["Izin_Rules"])
app.include_router(datatelat_router, prefix="/api/datatelat", tags=["datatelat"])

# --- PERUBAHAN BARU ---
app.include_router(datajobdesk_router, prefix="/api/datajobdesk", tags=["DataJobdesk"])
app.include_router(datashift_router, prefix="/api/datashift", tags=["DataShift"])
app.include_router(listjob_router, prefix="/api/listjob", tags=["ListJob"])
# --- AKHIR PERUBAHAN BARU ---

# ⭐ TAMBAHKAN INI UNTUK ROUTER CUTI
app.include_router(datacuti_router, prefix="/api/datacuti", tags=["DataCuti"])

@app.get("/")
def read_root():
    return {"message": "Selamat datang di Admin Panel API"}