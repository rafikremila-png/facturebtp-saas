"""
Security utilities
Password hashing, JWT tokens, and authentication helpers
"""
import os
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_uuid() -> str:
    """Generate a unique UUID string"""
    return str(uuid.uuid4())

def generate_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)

def generate_short_token(length: int = 6) -> str:
    """Generate a short numeric token (for OTP)"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

# ============== JWT TOKENS ==============

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token (7 days)"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_client_access_token(client_id: str, quote_id: Optional[str] = None, invoice_id: Optional[str] = None) -> str:
    """Create a limited access token for client portal"""
    data = {
        "sub": client_id,
        "type": "client_access",
        "quote_id": quote_id,
        "invoice_id": invoice_id
    }
    expire = timedelta(hours=72)  # 3 days for client access
    return create_access_token(data, expire)

def create_signature_token(quote_id: str, client_email: str) -> str:
    """Create a token for quote signature"""
    data = {
        "quote_id": quote_id,
        "client_email": client_email,
        "type": "signature",
        "purpose": "quote_signature"
    }
    expire = timedelta(days=7)  # 7 days to sign
    return create_access_token(data, expire)

# ============== ROLE CONSTANTS ==============

ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_SUPER_ADMIN = "super_admin"

ALL_ROLES = [ROLE_USER, ROLE_ADMIN, ROLE_SUPER_ADMIN]

def is_admin(role: str) -> bool:
    """Check if role is admin or higher"""
    return role in [ROLE_ADMIN, ROLE_SUPER_ADMIN]

def is_super_admin(role: str) -> bool:
    """Check if role is super admin"""
    return role == ROLE_SUPER_ADMIN
