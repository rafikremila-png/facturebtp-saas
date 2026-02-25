"""
User Models for BTP Facture
Pydantic models for user data validation and serialization
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator

# Role constants
ROLE_SUPER_ADMIN = "super_admin"
ROLE_ADMIN = "admin"
ROLE_USER = "user"
VALID_ROLES = [ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER]


def sanitize_string(s: str, max_length: int = 500) -> str:
    """Remove non-printable characters and limit length"""
    if not s or not isinstance(s, str):
        return s
    cleaned = ''.join(char for char in s if ord(char) >= 32 or char in '\n\r\t')
    return cleaned[:max_length]


class UserCreate(BaseModel):
    """User registration model with validation"""
    email: EmailStr
    password: str
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    company_name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    
    @validator('password')
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
    
    @validator('name')
    def sanitize_name(cls, v):
        return sanitize_string(v, 100)
    
    @validator('phone')
    def validate_phone(cls, v):
        cleaned = re.sub(r'[\s\-\.]', '', v)
        if not re.match(r'^(\+33|0)[1-9][0-9]{8}$', cleaned):
            raise ValueError('Format de téléphone invalide (ex: 0612345678 ou +33612345678)')
        return v


class UserLogin(BaseModel):
    """User login credentials"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Basic user response model"""
    id: str
    email: str
    name: str
    role: str = ROLE_USER
    phone: Optional[str] = None
    email_verified: bool = False
    is_verified: bool = False
    plan: Optional[str] = None


class UserDetailResponse(BaseModel):
    """Detailed user info for admin view"""
    id: str
    email: str
    name: str
    phone: str
    company_name: Optional[str] = None
    address: Optional[str] = None
    role: str
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    email_verified: bool = False
    plan: Optional[str] = None
    trial_start: Optional[str] = None
    trial_end: Optional[str] = None
    invoice_limit: int = 9
    # Stripe fields (prepared but not integrated)
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_status: Optional[str] = None  # active | canceled | past_due
    current_period_end: Optional[str] = None


class UserListResponse(BaseModel):
    """Response model for listing users (admin only)"""
    id: str
    email: str
    name: str
    role: str
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    email_verified: bool = False
    plan: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """Model for user profile self-update"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    company_name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        cleaned = re.sub(r'[\s\-\.]', '', v)
        if not re.match(r'^(\+33|0)[1-9][0-9]{8}$', cleaned):
            raise ValueError('Format de téléphone invalide')
        return v


class UserRoleUpdate(BaseModel):
    """Model for updating user role (admin only)"""
    role: str
    otp_code: str = Field(..., min_length=6, max_length=6)
    
    @validator('role')
    def validate_role(cls, v):
        if v not in VALID_ROLES:
            raise ValueError(f"Rôle invalide. Valeurs autorisées: {VALID_ROLES}")
        return v


class UserDBSchema:
    """
    Database schema for users collection.
    This is not a Pydantic model but a reference for the MongoDB document structure.
    
    Fields:
    - id: str (UUID)
    - email: str (unique)
    - password_hash: str (bcrypt)
    - name: str
    - phone: str
    - company_name: Optional[str]
    - address: Optional[str]
    - role: str (super_admin, admin, user)
    - created_at: datetime
    - last_login: Optional[datetime]
    - is_active: bool (default True)
    
    # Email verification
    - is_verified: bool (default False)
    - email_verified: bool (default False)
    
    # Trial management
    - trial_start: Optional[datetime] (None until email verified)
    - trial_end: Optional[datetime] (None until email verified)
    - plan: str (trial_pending, trial_active, trial_expired, paid)
    - invoice_limit: int (default 9)
    
    # Stripe (prepared, not integrated)
    - stripe_customer_id: Optional[str]
    - stripe_subscription_id: Optional[str]
    - subscription_status: Optional[str] (active, canceled, past_due)
    - current_period_end: Optional[datetime]
    """
    pass


def create_user_document(
    user_id: str,
    email: str,
    password_hash: str,
    name: str,
    phone: str,
    company_name: Optional[str] = None,
    address: Optional[str] = None,
    role: str = ROLE_USER,
    created_at: str = None
) -> dict:
    """
    Create a new user document for MongoDB insertion.
    Trial starts only after email verification.
    """
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc).isoformat()
    
    return {
        "id": user_id,
        "email": email,
        "password_hash": password_hash,
        "name": name,
        "phone": phone,
        "company_name": company_name,
        "address": address,
        "role": role,
        "created_at": created_at or now,
        "last_login": None,
        "is_active": True,
        
        # Email verification
        "is_verified": False,
        "email_verified": False,
        
        # Trial management (starts after verification)
        "trial_start": None,
        "trial_end": None,
        "plan": "trial_pending",
        "invoice_limit": 9,
        
        # Stripe preparation (not integrated yet)
        "stripe_customer_id": None,
        "stripe_subscription_id": None,
        "subscription_status": None,
        "current_period_end": None,
    }


def activate_user_trial(user_doc: dict) -> dict:
    """
    Activate trial period for a user after email verification.
    Called after successful OTP verification.
    
    Returns updated fields dict for MongoDB update.
    """
    from datetime import datetime, timezone, timedelta
    
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=14)
    
    return {
        "is_verified": True,
        "email_verified": True,
        "trial_start": now.isoformat(),
        "trial_end": trial_end.isoformat(),
        "plan": "trial_active",
    }
