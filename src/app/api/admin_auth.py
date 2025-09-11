from __future__ import annotations
from fastapi import Header, HTTPException, Depends
from src.app.core.config import settings

ADMIN_HEADER = "X-Admin-Key"


def require_admin(x_admin_key: str = Header("") ):
    if not settings.admin_api_key:
        # Admin key not configured -> deny by default
        raise HTTPException(status_code=403, detail="Admin API disabled")
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return True
