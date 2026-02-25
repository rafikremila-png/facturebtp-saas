"""
Verification Models for BTP Facture
Pydantic models for OTP and email verification
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator


class EmailVerification(BaseModel):
    """
    Email verification document structure.
    Stored in MongoDB 'email_verifications' collection.
    """
    user_id: str
    email: EmailStr
    otp_hash: str  # bcrypt hashed OTP
    expires_at: datetime
    attempts: int = 0
    verified: bool = False
    resend_count: int = 0
    last_sent_at: datetime
    created_at: datetime
    verified_at: Optional[datetime] = None


class OTPRequest(BaseModel):
    """Request to generate OTP"""
    email: EmailStr
    
    
class OTPResendRequest(BaseModel):
    """Request to resend OTP"""
    email: EmailStr
    user_id: Optional[str] = None  # Can be provided if known


class OTPVerify(BaseModel):
    """Verify OTP code"""
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)
    
    @validator('otp_code')
    def validate_otp_format(cls, v):
        if not v.isdigit():
            raise ValueError('Le code OTP doit contenir uniquement des chiffres')
        return v


class PasswordResetRequest(BaseModel):
    """Request password reset with OTP"""
    user_id: str
    new_password: str
    otp_code: str = Field(..., min_length=6, max_length=6)
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        if not any(c.isupper() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not any(c.islower() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule')
        if not any(c.isdigit() for c in v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        return v


class OTPVerifyResponse(BaseModel):
    """Response after OTP verification"""
    success: bool
    message: str
    user_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class ResendOTPResponse(BaseModel):
    """Response after OTP resend"""
    success: bool
    message: str
    resend_count: int
    can_resend_after: int  # seconds until next resend allowed


class VerificationDBSchema:
    """
    Database schema reference for email_verifications collection.
    
    MongoDB Document Structure:
    {
        "user_id": str,
        "email": str,
        "otp_hash": str (bcrypt),
        "expires_at": datetime (TTL index),
        "attempts": int,
        "verified": bool,
        "resend_count": int,
        "last_sent_at": datetime,
        "created_at": datetime,
        "verified_at": datetime (optional)
    }
    
    Indexes:
    - TTL index on expires_at (auto-delete expired documents)
    - Compound index on (user_id, email) for lookups
    - Index on email for direct lookups
    """
    pass
