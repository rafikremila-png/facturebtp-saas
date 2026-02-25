"""
JWT Service for BTP Facture
Token generation and validation
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
JWT_REFRESH_EXPIRATION_DAYS = 7

# Validate secret in production
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
if not JWT_SECRET:
    if ENVIRONMENT == 'production':
        raise ValueError("JWT_SECRET must be set in production environment")
    else:
        JWT_SECRET = 'dev-secret-key-change-in-production'
        logger.warning("Using default JWT secret in development - DO NOT USE IN PRODUCTION")


def create_access_token(user_id: str, role: str) -> str:
    """
    Create JWT access token.
    
    Args:
        user_id: User's unique identifier
        role: User's role (super_admin, admin, user)
        
    Returns:
        str: JWT access token
    """
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": expiration,
        "iat": datetime.now(timezone.utc),
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create JWT refresh token (longer lived).
    
    Args:
        user_id: User's unique identifier
        
    Returns:
        str: JWT refresh token
    """
    expiration = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRATION_DAYS)
    
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expiration,
        "iat": datetime.now(timezone.utc),
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Token payload
        
    Raises:
        HTTPException: On invalid or expired token
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )


def validate_access_token(token: str) -> Dict[str, Any]:
    """
    Validate access token specifically.
    
    Args:
        token: JWT access token
        
    Returns:
        dict: Token payload with user_id and role
        
    Raises:
        HTTPException: On invalid token or wrong type
    """
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Type de token invalide"
        )
    
    return {
        "user_id": payload["sub"],
        "role": payload.get("role", "user"),
    }


def validate_refresh_token(token: str) -> str:
    """
    Validate refresh token and return user_id.
    
    Args:
        token: JWT refresh token
        
    Returns:
        str: User ID
        
    Raises:
        HTTPException: On invalid token or wrong type
    """
    payload = decode_token(token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Type de token invalide"
        )
    
    return payload["sub"]


def refresh_access_token(refresh_token: str, user_role: str) -> str:
    """
    Generate new access token from refresh token.
    
    Args:
        refresh_token: Valid refresh token
        user_role: User's current role
        
    Returns:
        str: New access token
    """
    user_id = validate_refresh_token(refresh_token)
    return create_access_token(user_id, user_role)
