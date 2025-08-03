# backend/app/services/ip.py

from fastapi import APIRouter, Request
from app.utils.ip_utils import get_request_ip

router = APIRouter()

@router.get("/get_my_ip")
def get_my_ip(request: Request):
    """Endpoint untuk mendapatkan IP publik pengguna."""
    ip = get_request_ip(request)
    return {"ip_address": ip}