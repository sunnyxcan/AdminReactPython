# backend/app/dependencies.py

from .database import get_db
from .auth import get_current_user_from_firebase, get_current_admin_user