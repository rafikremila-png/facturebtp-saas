"""
Shared Dependencies
Authentication and authorization dependencies for API routes
Uses Supabase Auth for JWT validation
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.services.supabase_auth_service import verify_supabase_token, get_supabase_client

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await verify_supabase_token(credentials.credentials)
    except Exception:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user, raises 401 if not authenticated"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié"
        )
    
    try:
        user_data = await verify_supabase_token(credentials.credentials)
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )

async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require admin or super_admin role"""
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    return user

async def require_super_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require super_admin role"""
    if user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès super administrateur requis"
        )
    return user
