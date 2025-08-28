# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine

# Import semua endpoint dan model di sini
from app.dataizin import api as izin_endpoints
from app.izin_rules import api as izin_rules_endpoints
from app.users import api as user_endpoints
from app.roles import api as role_endpoints
from app.services import ip as ip_endpoints
from app.datatelat.api import router as datatelat_router
from app.datajobdesk.api import router as datajobdesk_router
from app.datashift.api import router as datashift_router
from app.listjob.api import router as listjob_router
from app.datacuti.api import router as datacuti_router
from app.dataresign import api as dataresign_endpoints
from app.whitelist import api as whitelist_endpoints
from app.statusLive import api as statuslive_endpoints
from app.autentikasi import api as auth_endpoints

# --- Pastikan semua impor model berada di sini ---
from app.fcm import models as fcm_models
from app.dataizin import models as izin_models
from app.users import models as user_models
from app.izin_rules import models as izin_rules_models
from app.roles import models as role_models
from app.datatelat import models as datatelat_models
from app.datajobdesk import models as datajobdesk_models
from app.datashift import models as datashift_models
from app.listjob import models as listjob_models
from app.datacuti import models as datacuti_models
from app.dataresign import models as dataresign_models
from app.whitelist import models as whitelist_models
from app.statusLive import models as statuslive_models

# --- Tambahan untuk Firebase ---
import firebase_admin
from firebase_admin import credentials
from app.core.config import settings

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK berhasil diinisialisasi.")
    except Exception as e:
        print(f"Gagal menginisialisasi Firebase Admin SDK: {e}")
# ------------------------------

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Admin Panel API",
    docs_url="/dokumentasi",
    redoc_url="/dokumentasi-api"
)

origins = [
    "http://localhost:5173",
    "http://localhost:8000",
    "https://adminreachpython.web.app",
    "https://bosjokopermit.web.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ⭐ Tambahkan baris ini untuk menyertakan router autentikasi
app.include_router(auth_endpoints.router, prefix="/api/auth", tags=["Auth"])
app.include_router(user_endpoints.router, prefix="/api/users", tags=["Users"])
app.include_router(role_endpoints.router, prefix="/api/roles", tags=["Roles"])
app.include_router(ip_endpoints.router, prefix="/api/ip", tags=["IP"])
app.include_router(izin_endpoints.router, prefix="/api/izin", tags=["Izin"])
app.include_router(izin_rules_endpoints.router, prefix="/api/izin_rules", tags=["Izin_Rules"])
app.include_router(datatelat_router, prefix="/api/datatelat", tags=["datatelat"])
app.include_router(datajobdesk_router, prefix="/api/datajobdesk", tags=["DataJobdesk"])
app.include_router(datashift_router, prefix="/api/datashift", tags=["DataShift"])
app.include_router(listjob_router, prefix="/api/listjob", tags=["ListJob"])
app.include_router(datacuti_router, prefix="/api/datacuti", tags=["DataCuti"])
app.include_router(dataresign_endpoints.router, prefix="/api/dataresign", tags=["DataResign"])
app.include_router(whitelist_endpoints.router, prefix="/api/whitelist-ip", tags=["Whitelist IP"])
app.include_router(statuslive_endpoints.router, prefix="/api/status-live", tags=["Status Live"])

@app.get("/")
def read_root():
    return {"message": "Selamat datang di Admin Panel API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}