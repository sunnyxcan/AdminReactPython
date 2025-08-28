# backend/app/services/ip.py

from fastapi import APIRouter, Request
from app.utils.ip_utils import get_request_ip
from app.utils.device_utils import detect_device_info
from app.device.schemas import DeviceInfoResponse

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"],
)

@router.get("/get_my_ip")
def get_my_ip(request: Request):
    """Endpoint untuk mendapatkan IP publik pengguna."""
    ip = get_request_ip(request)
    return {"ip_address": ip}

@router.get("/get_device_info", response_model=DeviceInfoResponse)
def get_device_info(request: Request):
    """Endpoint untuk mendapatkan informasi perangkat, OS, dan browser pengguna."""
    user_agent = request.headers.get("User-Agent")
    device_info = detect_device_info(user_agent)
    return device_info