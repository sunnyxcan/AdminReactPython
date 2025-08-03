# backend/app/utils/ip_utils.py

import requests
import os

def get_public_ip():
    """Mengambil alamat IP publik dari API eksternal."""
    try:
        response = requests.get('https://api.ipify.org')
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        pass
    return None

def get_request_ip(request):
    """Mendapatkan alamat IP dari request."""
    # Prioritaskan header 'X-Forwarded-For' jika ada (lingkungan produksi)
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(',')[0].strip()

    # Untuk lingkungan lokal, coba ambil IP publik secara langsung
    ip_address = get_public_ip()
    if ip_address:
        return ip_address

    # Jika gagal, kembalikan IP client dari request
    return request.client.host