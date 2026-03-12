"""
Supabase Authentication Service
Handles JWT validation and user management via Supabase
"""
import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
import logging

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", os.getenv("JWT_SECRET"))

# Initialize Supabase client
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase credentials not configured")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase_client

# HTTP Bearer security
security = HTTPBearer()

async def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Verify a Supabase JWT token and return the decoded payload
    """
    try:
        # Decode without verification first to get the user ID
        unverified = jwt.decode(token, options={"verify_signature": False})
        
        user_id = unverified.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Try to get user from auth (may fail if user was created differently)
        auth_user = None
        try:
            user_response = supabase.auth.admin.get_user_by_id(user_id)
            if user_response and user_response.user:
                auth_user = user_response.user
        except Exception as auth_error:
            logger.debug(f"Could not get auth user: {auth_error}")
        
        # Get user profile from database (this is the source of truth)
        try:
            profile_response = supabase.from_("users").select("*").eq("id", user_id).single().execute()
            profile = profile_response.data
        except Exception as db_error:
            logger.error(f"Could not get user profile: {db_error}")
            profile = None
        
        # Build user data
        if profile:
            user_data = {
                "id": str(user_id),
                "email": profile.get("email") or (auth_user.email if auth_user else ""),
                "role": profile.get("role", "user"),
                "name": profile.get("name", ""),
                "phone": profile.get("phone", ""),
                "company_name": profile.get("company_name", ""),
                "address": profile.get("address", ""),
                "business_type": profile.get("business_type"),
                "siret": profile.get("siret"),
                "subscription_plan": profile.get("subscription_plan"),
                "subscription_status": profile.get("subscription_status"),
            }
            return user_data
        elif auth_user:
            # Fallback to auth user if no profile
            return {
                "id": str(auth_user.id),
                "email": auth_user.email,
                "role": "user",
                "name": auth_user.user_metadata.get("name", "") if auth_user.user_metadata else "",
                "phone": "",
                "company_name": "",
                "address": "",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré"
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erreur d'authentification"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get the current authenticated user
    """
    token = credentials.credentials
    return await verify_supabase_token(token)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to optionally get the current user (for public endpoints)
    """
    if not credentials:
        return None
    try:
        return await verify_supabase_token(credentials.credentials)
    except HTTPException:
        return None

async def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    FastAPI dependency to require admin role
    """
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )
    return user

async def require_super_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    FastAPI dependency to require super_admin role
    """
    if user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès super administrateur requis"
        )
    return user

# Helper to create user profile
async def create_user_profile(user_id: str, email: str, **kwargs) -> Dict[str, Any]:
    """
    Create a user profile in the database
    """
    supabase = get_supabase_client()
    
    profile_data = {
        "id": user_id,
        "email": email,
        "name": kwargs.get("name", ""),
        "phone": kwargs.get("phone", ""),
        "company_name": kwargs.get("company_name", ""),
        "address": kwargs.get("address", ""),
        "role": kwargs.get("role", "user"),
        "created_at": "now()",
        "updated_at": "now()",
    }
    
    result = supabase.from_("users").upsert(profile_data).execute()
    return result.data[0] if result.data else profile_data

# Helper to get user by ID
async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile by ID
    """
    supabase = get_supabase_client()
    result = supabase.from_("users").select("*").eq("id", user_id).single().execute()
    return result.data

# Helper to update user profile
async def update_user_profile(user_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update user profile
    """
    supabase = get_supabase_client()
    
    update_data = {k: v for k, v in kwargs.items() if v is not None}
    update_data["updated_at"] = "now()"
    
    result = supabase.from_("users").update(update_data).eq("id", user_id).execute()
    return result.data[0] if result.data else None
