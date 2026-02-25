from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from io import BytesIO
import base64
import resend
import secrets
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import re

# Import new modular services
from app.services.email_service import get_email_service
from app.services.otp_service import get_otp_service
from app.services.rate_limit_service import get_rate_limiter, get_client_ip
from app.init import init_app_services, create_user_indexes

# ReportLab imports for PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ============== ENVIRONMENT VALIDATION ==============

JWT_SECRET = os.environ.get('JWT_SECRET')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

if not JWT_SECRET:
    if ENVIRONMENT == 'production':
        raise ValueError("JWT_SECRET must be set in production environment")
    else:
        JWT_SECRET = 'dev-secret-key-change-in-production'
        logging.warning("Using default JWT secret in development - DO NOT USE IN PRODUCTION")

MONGO_URL = os.environ.get('MONGO_URL')
if not MONGO_URL:
    raise ValueError("MONGO_URL must be set in environment")

DB_NAME = os.environ.get('DB_NAME', 'btp_invoice')

# ============== ADMIN CONFIGURATION ==============
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@btpfacture.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123!')
ADMIN_NAME = os.environ.get('ADMIN_NAME', 'Super Admin')

# Role constants
ROLE_SUPER_ADMIN = "super_admin"
ROLE_ADMIN = "admin"
ROLE_USER = "user"
VALID_ROLES = [ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER]

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

RESEND_CONFIGURED = False
if RESEND_API_KEY and not RESEND_API_KEY.startswith("re_123"):
    resend.api_key = RESEND_API_KEY
    RESEND_CONFIGURED = True
else:
    logging.warning("Resend API key not configured or using test key. Email sending disabled.")

FRONTEND_URL = os.environ.get("FRONTEND_URL")
if not FRONTEND_URL and RESEND_CONFIGURED:
    logging.warning("FRONTEND_URL not set. Email links may not work correctly.")

client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    maxPoolSize=10,
    minPoolSize=1
)
db = client[DB_NAME]

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
JWT_REFRESH_EXPIRATION_DAYS = 7

app = FastAPI(
    title="BTP Invoice API",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if ENVIRONMENT == 'production':
    allowed_hosts = os.environ.get('ALLOWED_HOSTS', '').split(',')
    if allowed_hosts and allowed_hosts[0]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# ============== LOGGING CONFIGURATION ==============

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        sensitive_patterns = ['password', 'token', 'authorization', 'key', 'secret']
        msg = record.getMessage()
        for pattern in sensitive_patterns:
            if pattern in msg.lower():
                words = msg.split()
                filtered_words = []
                for word in words:
                    if pattern in word.lower() and '=' in word:
                        parts = word.split('=')
                        if len(parts) == 2:
                            filtered_words.append(f"{parts[0]}=***FILTERED***")
                        else:
                            filtered_words.append(word)
                    else:
                        filtered_words.append(word)
                record.msg = ' '.join(filtered_words)
                break
        return True

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.addFilter(SensitiveDataFilter())

# ============== VALIDATION HELPERS ==============

def validate_uuid(uuid_str: str) -> bool:
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError, TypeError):
        return False

def sanitize_string(s: str, max_length: int = 500) -> str:
    if not s or not isinstance(s, str):
        return s
    cleaned = ''.join(char for char in s if ord(char) >= 32 or char in '\n\r\t')
    return cleaned[:max_length]

def validate_positive_float(value: float) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError("Value must be a number")
    if value < 0:
        raise ValueError("Value must be positive")
    if value > 1_000_000_000:
        raise ValueError("Value too large")
    return float(value)

def validate_percentage(value: float) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError("Value must be a number")
    if value < 0 or value > 100:
        raise ValueError("Percentage must be between 0 and 100")
    return float(value)

def generate_secure_id() -> str:
    return secrets.token_urlsafe(16)

def generate_share_token() -> str:
    return secrets.token_urlsafe(32)

def generate_otp() -> str:
    """Generate a 6-digit OTP code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

# ============== OTP TYPES ==============
OTP_TYPE_REGISTRATION = "registration"
OTP_TYPE_PASSWORD_RESET = "password_reset"
OTP_TYPE_DELETE_USER = "delete_user"
OTP_TYPE_PROMOTE_ADMIN = "promote_admin"
OTP_TYPE_IMPERSONATION = "impersonation"

OTP_EXPIRATION_MINUTES = {
    OTP_TYPE_REGISTRATION: 10,
    OTP_TYPE_PASSWORD_RESET: 5,
    OTP_TYPE_DELETE_USER: 5,
    OTP_TYPE_PROMOTE_ADMIN: 5,
    OTP_TYPE_IMPERSONATION: 5
}

# ============== MODELS COMPLETS ==============

class UserCreate(BaseModel):
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

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str = ROLE_USER
    phone: Optional[str] = None
    email_verified: bool = False

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
    email_verified: bool = False

class UserListResponse(BaseModel):
    """Response model for listing users (admin only)"""
    id: str
    email: str
    name: str
    role: str
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True
    email_verified: bool = False

class UserRoleUpdate(BaseModel):
    """Model for updating user role (admin only)"""
    role: str
    otp_code: str = Field(..., min_length=6, max_length=6)
    
    @validator('role')
    def validate_role(cls, v):
        if v not in VALID_ROLES:
            raise ValueError(f"Rôle invalide. Valeurs autorisées: {VALID_ROLES}")
        return v

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse

# ============== OTP MODELS ==============

class OTPRequest(BaseModel):
    """Request to generate OTP"""
    email: EmailStr
    otp_type: str
    target_user_id: Optional[str] = None  # For admin actions on other users
    
    @validator('otp_type')
    def validate_otp_type(cls, v):
        valid_types = [OTP_TYPE_REGISTRATION, OTP_TYPE_PASSWORD_RESET, 
                      OTP_TYPE_DELETE_USER, OTP_TYPE_PROMOTE_ADMIN, OTP_TYPE_IMPERSONATION]
        if v not in valid_types:
            raise ValueError(f"Type OTP invalide. Valeurs: {valid_types}")
        return v

class OTPVerify(BaseModel):
    """Verify OTP code"""
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)
    otp_type: str

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

class UserDeleteRequest(BaseModel):
    """Request to delete user with OTP"""
    otp_code: str = Field(..., min_length=6, max_length=6)

class ImpersonationRequest(BaseModel):
    """Request to impersonate a user"""
    target_user_id: str
    otp_code: str = Field(..., min_length=6, max_length=6)

# ============== WEBSITE REQUEST MODELS ==============

class WebsiteRequestCreate(BaseModel):
    """Request for website creation"""
    activity_type: str = Field(..., min_length=2, max_length=200)
    objective: str = Field(..., min_length=10, max_length=1000)
    budget: str = Field(..., max_length=100)
    timeline: str = Field(..., max_length=100)
    additional_notes: Optional[str] = Field(None, max_length=2000)
    
    @validator('activity_type', 'objective')
    def sanitize_text(cls, v):
        return sanitize_string(v, 1000)

class WebsiteRequestResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: str
    user_phone: str
    company_name: Optional[str]
    activity_type: str
    objective: str
    budget: str
    timeline: str
    additional_notes: Optional[str]
    status: str  # pending, contacted, in_progress, completed, cancelled
    created_at: str
    updated_at: Optional[str] = None

# ============== AUDIT LOG MODEL ==============

class AuditLogEntry(BaseModel):
    """Audit log for sensitive actions"""
    id: str
    action: str
    actor_id: str
    actor_email: str
    target_id: Optional[str] = None
    target_email: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: str

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(default="", max_length=500)
    phone: str = Field(default="", max_length=50)
    email: EmailStr = ""
    
    @validator('name')
    def sanitize_name(cls, v):
        return sanitize_string(v, 200)
    
    @validator('address')
    def sanitize_address(cls, v):
        return sanitize_string(v, 500)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^[0-9+\-\s()]{0,50}$', v):
            raise ValueError('Format de téléphone invalide')
        return v

class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    
    @validator('name')
    def sanitize_name(cls, v):
        if v is None:
            return v
        return sanitize_string(v, 200)
    
    @validator('address')
    def sanitize_address(cls, v):
        if v is None:
            return v
        return sanitize_string(v, 500)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        if v and not re.match(r'^[0-9+\-\s()]{0,50}$', v):
            raise ValueError('Format de téléphone invalide')
        return v

class ClientResponse(BaseModel):
    id: str
    name: str
    address: str
    phone: str
    email: str
    created_at: str

class LineItem(BaseModel):
    description: str = Field(..., max_length=500)
    quantity: float = Field(..., gt=0, le=1_000_000)
    unit_price: float = Field(..., ge=0, le=1_000_000)
    vat_rate: float = Field(20.0, ge=0, le=100)
    unit: str = Field(default="unité", max_length=50)
    
    @validator('description')
    def sanitize_description(cls, v):
        return sanitize_string(v, 500)
    
    @validator('quantity')
    def validate_quantity(cls, v):
        return validate_positive_float(v)
    
    @validator('unit_price')
    def validate_unit_price(cls, v):
        return validate_positive_float(v)
    
    @validator('vat_rate')
    def validate_vat_rate(cls, v):
        return validate_percentage(v)

class QuoteCreate(BaseModel):
    client_id: str
    validity_days: int = Field(30, ge=1, le=365)
    items: List[LineItem] = Field(..., max_items=100)
    notes: str = Field(default="", max_length=2000)
    
    @validator('client_id')
    def validate_client_id(cls, v):
        if not validate_uuid(v):
            raise ValueError('ID client invalide')
        return v
    
    @validator('notes')
    def sanitize_notes(cls, v):
        return sanitize_string(v, 2000)

class QuoteUpdate(BaseModel):
    client_id: Optional[str] = None
    validity_days: Optional[int] = Field(None, ge=1, le=365)
    items: Optional[List[LineItem]] = Field(None, max_items=100)
    notes: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(
        None,
        pattern="^(brouillon|envoye|accepte|refuse|facture)$"
    )

    @validator("client_id")
    def validate_client_id(cls, v):
        if v is None:
            return v
        if not validate_uuid(v):
            raise ValueError("ID client invalide")
        return v

    
    @validator('notes')
    def sanitize_notes(cls, v):
        if v is None:
            return v
        return sanitize_string(v, 2000)

class QuoteResponse(BaseModel):
    id: str
    quote_number: str
    client_id: str
    client_name: str
    issue_date: str
    validity_date: str
    items: List[dict]
    total_ht: float
    total_vat: float
    total_ttc: float
    status: str
    notes: str
    created_at: str
    share_token: Optional[str] = None

class InvoiceCreate(BaseModel):
    client_id: str
    quote_id: Optional[str] = None
    items: List[LineItem] = Field(..., max_items=100)
    notes: str = Field(default="", max_length=2000)
    payment_method: str = Field(
    "virement",
    pattern="^(virement|especes|cheque|carte)$"
)

    payment_delay_days: Optional[int] = Field(None, ge=0, le=365)
    
    @validator('client_id')
    def validate_client_id(cls, v):
        if not validate_uuid(v):
            raise ValueError('ID client invalide')
        return v
    
    @validator('quote_id')
    def validate_quote_id(cls, v):
        if v is None:
            return v
        if not validate_uuid(v):
            raise ValueError('ID devis invalide')
        return v
    
    @validator('notes')
    def sanitize_notes(cls, v):
        return sanitize_string(v, 2000)

class InvoiceUpdate(BaseModel):
    payment_status: Optional[str] = Field(
    None,
    pattern="^(impaye|partiel|paye)$"
)

    payment_method: str = Field(
    "virement",
    pattern="^(virement|especes|cheque|carte)$"
)

    paid_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=2000)
    
    @validator('paid_amount')
    def validate_paid_amount(cls, v):
        if v is None:
            return v
        return validate_positive_float(v)
    
    @validator('notes')
    def sanitize_notes(cls, v):
        if v is None:
            return v
        return sanitize_string(v, 2000)

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    client_id: str
    client_name: str
    quote_id: Optional[str]
    issue_date: str
    payment_due_date: str
    items: List[dict]
    total_ht: float
    total_vat: float
    total_ttc: float
    payment_status: str
    payment_method: str
    paid_amount: float
    notes: str
    created_at: str
    share_token: Optional[str] = None
    is_acompte: bool = False
    acompte_type: Optional[str] = None
    acompte_value: Optional[float] = None
    parent_quote_id: Optional[str] = None
    acompte_number: Optional[int] = None
    is_situation: bool = False
    situation_number: Optional[int] = None
    situation_percentage: Optional[float] = None
    previous_percentage: Optional[float] = None
    chantier_ref: Optional[str] = None
    has_retenue_garantie: bool = False
    retenue_garantie_rate: float = 0.0
    retenue_garantie_amount: float = 0.0
    retenue_garantie_release_date: Optional[str] = None
    retenue_garantie_released: bool = False
    net_a_payer: Optional[float] = None

class AcompteCreate(BaseModel):
    quote_id: str
    acompte_type: str = Field(
    ...,
    pattern="^(percentage|amount)$"
)

    value: float = Field(..., gt=0)
    notes: str = Field(default="", max_length=2000)
    payment_method: str = Field(
    "virement",
    pattern="^(virement|especes|cheque|carte)$"
)

    
    @validator('quote_id')
    def validate_quote_id(cls, v):
        if not validate_uuid(v):
            raise ValueError('ID devis invalide')
        return v
    
    @validator('value')
    def validate_value(cls, v, values):
        if 'acompte_type' in values:
            if values['acompte_type'] == 'percentage' and v > 100:
                raise ValueError('Le pourcentage ne peut pas dépasser 100%')
        return validate_positive_float(v)

class AcompteResponse(BaseModel):
    id: str
    invoice_number: str
    quote_id: str
    quote_number: str
    client_id: str
    client_name: str
    issue_date: str
    payment_due_date: str
    acompte_type: str
    acompte_value: float
    acompte_number: int
    total_ht: float
    total_vat: float
    total_ttc: float
    payment_status: str
    payment_method: str
    paid_amount: float
    notes: str
    created_at: str

class SituationLineItem(BaseModel):
    description: str = Field(..., max_length=500)
    quantity: float = Field(..., gt=0, le=1_000_000)
    unit_price: float = Field(..., ge=0, le=1_000_000)
    vat_rate: float = Field(20.0, ge=0, le=100)
    progress_percent: float = Field(..., ge=0, le=100)
    
    @validator('description')
    def sanitize_description(cls, v):
        return sanitize_string(v, 500)
    
    @validator('progress_percent')
    def validate_progress(cls, v):
        return validate_percentage(v)

class SituationCreate(BaseModel):
    quote_id: str
    situation_type: str = Field(
    ...,
    pattern="^(global|per_line)$"
)

    global_percentage: Optional[float] = Field(None, ge=0, le=100)
    line_items: Optional[List[SituationLineItem]] = Field(None, max_items=100)
    notes: str = Field(default="", max_length=2000)
    payment_method: str = Field("virement", pattern=
'^(virement|especes|cheque|carte)$')
    chantier_ref: str = Field(default="", max_length=200)
    
    @validator('quote_id')
    def validate_quote_id(cls, v):
        if not validate_uuid(v):
            raise ValueError('ID devis invalide')
        return v
    
    @validator('global_percentage')
    def validate_global_percentage(cls, v, values):
        if 'situation_type' in values and values['situation_type'] == 'global':
            if v is None:
                raise ValueError('Le pourcentage global est requis')
            return validate_percentage(v)
        return v
    
    @validator('line_items')
    def validate_line_items(cls, v, values):
        if 'situation_type' in values and values['situation_type'] == 'per_line':
            if not v:
                raise ValueError('Les lignes de situation sont requises')
        return v

class SituationResponse(BaseModel):
    id: str
    invoice_number: str
    quote_id: str
    quote_number: str
    client_id: str
    client_name: str
    issue_date: str
    payment_due_date: str
    situation_type: str
    situation_number: int
    current_percentage: float
    previous_percentage: float
    situation_percentage: float
    items: List[dict]
    total_ht: float
    total_vat: float
    total_ttc: float
    payment_status: str
    payment_method: str
    paid_amount: float
    notes: str
    chantier_ref: str
    created_at: str

class RetenueGarantieCreate(BaseModel):
    rate: float = Field(5.0, ge=0, le=5)
    warranty_months: int = Field(12, ge=1, le=60)
    
    @validator('rate')
    def validate_rate(cls, v):
        return validate_percentage(v)

class RetenueGarantieUpdate(BaseModel):
    rate: Optional[float] = Field(None, ge=0, le=5)
    release_date: Optional[str] = None
    
    @validator('rate')
    def validate_rate(cls, v):
        if v is None:
            return v
        return validate_percentage(v)

class RetenueGarantieSummary(BaseModel):
    total_retained: float
    total_released: float
    pending_release: float
    retentions: List[dict]

class CompanySettings(BaseModel):
    company_name: str = Field(default="", max_length=200)
    address: str = Field(default="", max_length=500)
    phone: str = Field(default="", max_length=50)
    email: EmailStr = ""
    siret: str = Field(default="", max_length=14)
    vat_number: str = Field(default="", max_length=20)
    default_vat_rates: List[float] = [20.0, 10.0, 5.5, 2.1]
    logo_base64: Optional[str] = None
    rcs_rm: str = Field(default="", max_length=50)
    code_ape: str = Field(default="", max_length=10)
    capital_social: str = Field(default="", max_length=50)
    iban: str = Field(default="", max_length=34)
    bic: str = Field(default="", max_length=11)
    is_auto_entrepreneur: bool = False
    auto_entrepreneur_mention: str = "TVA non applicable, art. 293B du CGI"
    default_payment_delay_days: int = Field(30, ge=0, le=365)
    late_payment_rate: float = Field(3.0, ge=0, le=100)
    default_retenue_garantie_enabled: bool = False
    default_retenue_garantie_rate: float = Field(5.0, ge=0, le=5)
    default_retenue_garantie_duration_months: int = Field(12, ge=1, le=60)
    website: Optional[str] = Field(default="", max_length=200)
    document_theme_color: str = Field(default="blue", max_length=20)
    
    @validator('siret')
    def validate_siret(cls, v):
        if v and not re.match(r'^\d{14}$', v):
            raise ValueError('SIRET doit contenir 14 chiffres')
        return v
    
    @validator('iban')
    def validate_iban(cls, v):
        if v and len(v) > 34:
            raise ValueError('IBAN trop long')
        return v
    
    @validator('bic')
    def validate_bic(cls, v):
        if v and not re.match(r'^[A-Z]{6}[A-Z0-9]{2,5}$', v):
            raise ValueError('Format BIC invalide')
        return v
    
    @validator('website')
    def validate_website(cls, v):
        if v and v.strip():
            # Simple URL validation
            url_pattern = r'^https?://[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+(/.*)?$'
            if not re.match(url_pattern, v):
                raise ValueError('Format URL invalide (ex: https://exemple.com)')
        return v or ""
    
    @validator('document_theme_color')
    def validate_theme_color(cls, v):
        valid_colors = ["blue", "light_blue", "green", "orange", "burgundy", "dark_grey"]
        if v not in valid_colors:
            raise ValueError(f"Couleur invalide. Valeurs autorisées: {valid_colors}")
        return v

class DashboardStats(BaseModel):
    total_turnover: float
    unpaid_invoices_count: int
    unpaid_invoices_amount: float
    pending_quotes_count: int
    total_clients: int
    total_quotes: int
    total_invoices: int

class KitItem(BaseModel):
    description: str = Field(..., max_length=500)
    unit: str = Field("unité", max_length=50)
    quantity: float = Field(1.0, gt=0, le=1_000_000)
    unit_price: float = Field(0.0, ge=0, le=1_000_000)
    vat_rate: float = Field(20.0, ge=0, le=100)
    
    @validator('description')
    def sanitize_description(cls, v):
        return sanitize_string(v, 500)

class KitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    items: List[KitItem] = Field(..., max_items=100)
    is_default: bool = False

class KitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    items: Optional[List[KitItem]] = Field(None, max_items=100)

class KitResponse(BaseModel):
    id: str
    name: str
    description: str
    items: List[dict]
    is_default: bool
    created_at: str

class PredefinedItemCreate(BaseModel):
    category: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    unit: str = Field("unité", max_length=50)
    default_price: float = Field(0.0, ge=0, le=1_000_000)
    default_vat_rate: float = Field(20.0, ge=0, le=100)

class PredefinedItemUpdate(BaseModel):
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    unit: Optional[str] = Field(None, max_length=50)
    default_price: Optional[float] = Field(None, ge=0, le=1_000_000)
    default_vat_rate: Optional[float] = Field(None, ge=0, le=100)

class PredefinedItemResponse(BaseModel):
    id: str
    category: str
    description: str
    unit: str
    default_price: float
    default_vat_rate: float

class CategoryResponse(BaseModel):
    name: str
    items: List[PredefinedItemResponse]

class SendDocumentEmailRequest(BaseModel):
    recipient_email: EmailStr
    recipient_name: str = Field(default="", max_length=200)
    custom_message: str = Field(default="", max_length=2000)
    
    @validator('custom_message')
    def sanitize_message(cls, v):
        return sanitize_string(v, 2000)

# ============== DEFAULT DATA (COMPLETE) ==============

DEFAULT_RENOVATION_KITS = [
    {
        "name": "Rénovation salle de bain",
        "description": "Kit complet pour la rénovation d'une salle de bain standard",
        "items": [
            {"description": "Démolition / Dépose sanitaires existants", "unit": "forfait", "quantity": 1, "unit_price": 450.0, "vat_rate": 20.0},
            {"description": "Plomberie - Alimentation et évacuation", "unit": "forfait", "quantity": 1, "unit_price": 850.0, "vat_rate": 20.0},
            {"description": "Carrelage sol", "unit": "m²", "quantity": 8, "unit_price": 55.0, "vat_rate": 20.0},
            {"description": "Carrelage mural / Faïence", "unit": "m²", "quantity": 15, "unit_price": 60.0, "vat_rate": 20.0},
            {"description": "Peinture plafond (2 couches)", "unit": "m²", "quantity": 8, "unit_price": 22.0, "vat_rate": 20.0},
            {"description": "Installation sanitaires (WC, lavabo, douche)", "unit": "forfait", "quantity": 1, "unit_price": 650.0, "vat_rate": 20.0},
        ]
    },
    {
        "name": "Installation cuisine",
        "description": "Kit pour l'installation complète d'une cuisine équipée",
        "items": [
            {"description": "Dépose ancienne cuisine", "unit": "forfait", "quantity": 1, "unit_price": 350.0, "vat_rate": 20.0},
            {"description": "Installation meubles de cuisine", "unit": "ml", "quantity": 5, "unit_price": 180.0, "vat_rate": 20.0},
            {"description": "Installation électroménager", "unit": "unité", "quantity": 4, "unit_price": 85.0, "vat_rate": 20.0},
            {"description": "Plomberie - Évier et lave-vaisselle", "unit": "forfait", "quantity": 1, "unit_price": 380.0, "vat_rate": 20.0},
            {"description": "Électricité - Prises et raccordements", "unit": "forfait", "quantity": 1, "unit_price": 450.0, "vat_rate": 20.0},
            {"description": "Crédence et finitions", "unit": "ml", "quantity": 3, "unit_price": 120.0, "vat_rate": 20.0},
        ]
    },
    {
        "name": "Rénovation électrique complète",
        "description": "Mise aux normes et rénovation complète de l'installation électrique",
        "items": [
            {"description": "Tableau électrique avec disjoncteurs", "unit": "unité", "quantity": 1, "unit_price": 950.0, "vat_rate": 20.0},
            {"description": "Tirage de câbles", "unit": "ml", "quantity": 80, "unit_price": 12.0, "vat_rate": 20.0},
            {"description": "Pose prises électriques", "unit": "unité", "quantity": 15, "unit_price": 65.0, "vat_rate": 20.0},
            {"description": "Pose interrupteurs", "unit": "unité", "quantity": 8, "unit_price": 55.0, "vat_rate": 20.0},
            {"description": "Mise en conformité NF C 15-100", "unit": "forfait", "quantity": 1, "unit_price": 350.0, "vat_rate": 20.0},
        ]
    }
]

DEFAULT_BTP_CATEGORIES = {
    "Maçonnerie": [
        {"description": "Démolition cloison légère", "unit": "m²", "default_price": 25.0, "default_vat_rate": 10.0},
        {"description": "Démolition cloison en briques/parpaings", "unit": "m²", "default_price": 45.0, "default_vat_rate": 10.0},
        {"description": "Démolition mur porteur (avec étaiement)", "unit": "forfait", "default_price": 1500.0, "default_vat_rate": 10.0},
        {"description": "Création ouverture dans mur porteur", "unit": "forfait", "default_price": 2200.0, "default_vat_rate": 10.0},
        {"description": "Création ouverture dans cloison", "unit": "unité", "default_price": 350.0, "default_vat_rate": 10.0},
        {"description": "Dépose de carrelage existant", "unit": "m²", "default_price": 18.0, "default_vat_rate": 10.0},
        {"description": "Évacuation gravats", "unit": "m³", "default_price": 85.0, "default_vat_rate": 10.0},
        {"description": "Montage mur en parpaings (20cm)", "unit": "m²", "default_price": 85.0, "default_vat_rate": 10.0},
        {"description": "Montage mur en parpaings (15cm)", "unit": "m²", "default_price": 75.0, "default_vat_rate": 10.0},
        {"description": "Montage mur en briques", "unit": "m²", "default_price": 95.0, "default_vat_rate": 10.0},
        {"description": "Montage cloison en carreaux de plâtre", "unit": "m²", "default_price": 55.0, "default_vat_rate": 10.0},
        {"description": "Coffrage béton", "unit": "m²", "default_price": 45.0, "default_vat_rate": 10.0},
        {"description": "Coulage dalle béton armé (10cm)", "unit": "m²", "default_price": 75.0, "default_vat_rate": 10.0},
        {"description": "Coulage dalle béton armé (15cm)", "unit": "m²", "default_price": 95.0, "default_vat_rate": 10.0},
        {"description": "Chape traditionnelle (5cm)", "unit": "m²", "default_price": 35.0, "default_vat_rate": 10.0},
        {"description": "Chape liquide autonivelante", "unit": "m²", "default_price": 28.0, "default_vat_rate": 10.0},
        {"description": "Ragréage sol (P3)", "unit": "m²", "default_price": 22.0, "default_vat_rate": 10.0},
        {"description": "Enduit intérieur plâtre", "unit": "m²", "default_price": 28.0, "default_vat_rate": 10.0},
        {"description": "Enduit intérieur ciment", "unit": "m²", "default_price": 25.0, "default_vat_rate": 10.0},
        {"description": "Enduit extérieur monocouche", "unit": "m²", "default_price": 45.0, "default_vat_rate": 10.0},
        {"description": "Ravalement façade complet", "unit": "m²", "default_price": 65.0, "default_vat_rate": 10.0},
        {"description": "Réparation fissures façade", "unit": "ml", "default_price": 35.0, "default_vat_rate": 10.0},
        {"description": "Pose appui de fenêtre béton", "unit": "ml", "default_price": 55.0, "default_vat_rate": 10.0},
        {"description": "Pose seuil de porte", "unit": "unité", "default_price": 120.0, "default_vat_rate": 10.0},
    ],
    "Carrelage": [
        {"description": "Dépose carrelage existant", "unit": "m²", "default_price": 18.0, "default_vat_rate": 10.0},
        {"description": "Dépose faïence murale", "unit": "m²", "default_price": 15.0, "default_vat_rate": 10.0},
        {"description": "Ragréage sol avant carrelage", "unit": "m²", "default_price": 22.0, "default_vat_rate": 10.0},
        {"description": "Primaire d'accrochage", "unit": "m²", "default_price": 6.0, "default_vat_rate": 10.0},
        {"description": "Étanchéité SPEC sous carrelage", "unit": "m²", "default_price": 25.0, "default_vat_rate": 10.0},
        {"description": "Pose carrelage sol (petit format <30x30)", "unit": "m²", "default_price": 42.0, "default_vat_rate": 10.0},
        {"description": "Pose carrelage sol (format standard 30x30 à 60x60)", "unit": "m²", "default_price": 48.0, "default_vat_rate": 10.0},
        {"description": "Pose carrelage sol (grand format >60x60)", "unit": "m²", "default_price": 58.0, "default_vat_rate": 10.0},
        {"description": "Pose carrelage imitation parquet", "unit": "m²", "default_price": 55.0, "default_vat_rate": 10.0},
        {"description": "Pose mosaïque sol", "unit": "m²", "default_price": 75.0, "default_vat_rate": 10.0},
        {"description": "Pose faïence murale (format standard)", "unit": "m²", "default_price": 52.0, "default_vat_rate": 10.0},
        {"description": "Pose faïence murale métro", "unit": "m²", "default_price": 58.0, "default_vat_rate": 10.0},
        {"description": "Pose mosaïque murale", "unit": "m²", "default_price": 78.0, "default_vat_rate": 10.0},
        {"description": "Pose crédence cuisine", "unit": "ml", "default_price": 85.0, "default_vat_rate": 10.0},
        {"description": "Joints carrelage (pose comprise)", "unit": "m²", "default_price": 12.0, "default_vat_rate": 10.0},
        {"description": "Joints époxy (pièces humides)", "unit": "m²", "default_price": 18.0, "default_vat_rate": 10.0},
        {"description": "Pose plinthes carrelées", "unit": "ml", "default_price": 15.0, "default_vat_rate": 10.0},
        {"description": "Barre de seuil", "unit": "unité", "default_price": 25.0, "default_vat_rate": 10.0},
        {"description": "Nez de marche carrelé", "unit": "ml", "default_price": 45.0, "default_vat_rate": 10.0},
    ],
    "Plâtrerie / Isolation": [
        {"description": "Cloison placo BA13 simple (72mm)", "unit": "m²", "default_price": 38.0, "default_vat_rate": 10.0},
        {"description": "Cloison placo BA13 double (98mm)", "unit": "m²", "default_price": 52.0, "default_vat_rate": 10.0},
        {"description": "Cloison placo hydrofuge (pièces humides)", "unit": "m²", "default_price": 48.0, "default_vat_rate": 10.0},
        {"description": "Cloison placo phonique", "unit": "m²", "default_price": 55.0, "default_vat_rate": 10.0},
        {"description": "Cloison placo coupe-feu", "unit": "m²", "default_price": 62.0, "default_vat_rate": 10.0},
        {"description": "Faux plafond placo BA13", "unit": "m²", "default_price": 45.0, "default_vat_rate": 10.0},
        {"description": "Faux plafond placo suspendu", "unit": "m²", "default_price": 55.0, "default_vat_rate": 10.0},
        {"description": "Faux plafond dalles 60x60", "unit": "m²", "default_price": 42.0, "default_vat_rate": 10.0},
        {"description": "Faux plafond acoustique", "unit": "m²", "default_price": 65.0, "default_vat_rate": 10.0},
        {"description": "Création coffrage technique", "unit": "ml", "default_price": 55.0, "default_vat_rate": 10.0},
        {"description": "Doublage murs placo + isolant (10+40)", "unit": "m²", "default_price": 42.0, "default_vat_rate": 10.0},
        {"description": "Doublage murs placo + isolant (10+80)", "unit": "m²", "default_price": 52.0, "default_vat_rate": 10.0},
        {"description": "Doublage murs placo + isolant (13+100)", "unit": "m²", "default_price": 58.0, "default_vat_rate": 10.0},
        {"description": "Isolation laine de verre (100mm)", "unit": "m²", "default_price": 18.0, "default_vat_rate": 5.5},
        {"description": "Isolation laine de verre (200mm)", "unit": "m²", "default_price": 28.0, "default_vat_rate": 5.5},
        {"description": "Isolation laine de roche (100mm)", "unit": "m²", "default_price": 22.0, "default_vat_rate": 5.5},
        {"description": "Isolation laine de roche (200mm)", "unit": "m²", "default_price": 35.0, "default_vat_rate": 5.5},
        {"description": "Isolation polystyrène expansé (80mm)", "unit": "m²", "default_price": 25.0, "default_vat_rate": 5.5},
        {"description": "Isolation combles perdus soufflée", "unit": "m²", "default_price": 22.0, "default_vat_rate": 5.5},
        {"description": "Isolation rampants sous toiture", "unit": "m²", "default_price": 45.0, "default_vat_rate": 5.5},
        {"description": "Bandes et joints placo", "unit": "m²", "default_price": 12.0, "default_vat_rate": 10.0},
        {"description": "Enduit de lissage placo", "unit": "m²", "default_price": 8.0, "default_vat_rate": 10.0},
        {"description": "Pose corniche décorative", "unit": "ml", "default_price": 25.0, "default_vat_rate": 10.0},
        {"description": "Trappe de visite plafond", "unit": "unité", "default_price": 85.0, "default_vat_rate": 10.0},
    ]
}

# ============== SECURITY HELPERS ==============

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# ============== OTP FUNCTIONS ==============

async def generate_and_store_otp(email: str, otp_type: str, target_user_id: str = None) -> str:
    """Generate OTP, store in database, and return the code"""
    otp_code = generate_otp()
    expiration_minutes = OTP_EXPIRATION_MINUTES.get(otp_type, 5)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
    
    # Delete any existing OTP for this email/type
    await db.otp_codes.delete_many({"email": email, "otp_type": otp_type})
    
    otp_doc = {
        "id": str(uuid.uuid4()),
        "email": email,
        "otp_code": otp_code,
        "otp_type": otp_type,
        "target_user_id": target_user_id,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "used": False
    }
    
    await db.otp_codes.insert_one(otp_doc)
    
    # Log OTP for development (will be replaced by email in production)
    logger.info(f"[OTP] Code: {otp_code} | Email: {email} | Type: {otp_type} | Expires in {expiration_minutes} minutes")
    
    # Send email if Resend is configured
    if RESEND_CONFIGURED:
        try:
            await send_otp_email(email, otp_code, otp_type, expiration_minutes)
        except Exception as e:
            logger.error(f"Failed to send OTP email: {str(e)}")
    
    return otp_code

async def verify_otp(email: str, otp_code: str, otp_type: str) -> dict:
    """Verify OTP code and return the OTP document if valid"""
    otp_doc = await db.otp_codes.find_one({
        "email": email,
        "otp_code": otp_code,
        "otp_type": otp_type,
        "used": False
    })
    
    if not otp_doc:
        return None
    
    expires_at = datetime.fromisoformat(otp_doc["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        await db.otp_codes.delete_one({"id": otp_doc["id"]})
        return None
    
    # Mark as used
    await db.otp_codes.update_one(
        {"id": otp_doc["id"]},
        {"$set": {"used": True}}
    )
    
    return otp_doc

async def send_otp_email(email: str, otp_code: str, otp_type: str, expiration_minutes: int):
    """Send OTP via email using Resend"""
    type_labels = {
        OTP_TYPE_REGISTRATION: "Vérification de votre compte",
        OTP_TYPE_PASSWORD_RESET: "Réinitialisation du mot de passe",
        OTP_TYPE_DELETE_USER: "Suppression de compte",
        OTP_TYPE_PROMOTE_ADMIN: "Modification de rôle",
        OTP_TYPE_IMPERSONATION: "Accès support"
    }
    
    subject = f"BTP Facture - {type_labels.get(otp_type, 'Code de vérification')}"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #ea580c;">BTP Facture</h2>
        <p>Votre code de vérification est :</p>
        <div style="background: #f1f5f9; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1e293b;">{otp_code}</span>
        </div>
        <p style="color: #64748b;">Ce code expire dans {expiration_minutes} minutes.</p>
        <p style="color: #64748b; font-size: 12px;">Si vous n'avez pas demandé ce code, ignorez cet email.</p>
    </div>
    """
    
    resend.emails.send({
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": subject,
        "html": html_content
    })

# ============== AUDIT LOG FUNCTIONS ==============

async def create_audit_log(action: str, actor_id: str, actor_email: str, 
                          target_id: str = None, target_email: str = None,
                          details: str = None, ip_address: str = None):
    """Create an audit log entry for sensitive actions"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "action": action,
        "actor_id": actor_id,
        "actor_email": actor_email,
        "target_id": target_id,
        "target_email": target_email,
        "details": details,
        "ip_address": ip_address,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.audit_logs.insert_one(log_entry)
    logger.info(f"[AUDIT] {action} | Actor: {actor_email} | Target: {target_email or 'N/A'} | Details: {details or 'N/A'}")

def create_token(user_id: str, token_type: str = "access") -> str:
    if token_type == "access":
        expires = timedelta(hours=JWT_EXPIRATION_HOURS)
    else:
        expires = timedelta(days=JWT_REFRESH_EXPIRATION_DAYS)
    
    payload = {
        "sub": user_id,
        "type": token_type,
        "exp": int((datetime.now(timezone.utc) + expires).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "jti": secrets.token_urlsafe(16)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_impersonation_token(admin_id: str, target_user_id: str) -> str:
    """Create a special token for impersonation sessions"""
    expires = timedelta(hours=2)  # Shorter expiration for impersonation
    
    payload = {
        "sub": target_user_id,
        "type": "impersonation",
        "admin_id": admin_id,
        "exp": int((datetime.now(timezone.utc) + expires).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "jti": secrets.token_urlsafe(16)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True}
        )
        
        user_id = payload.get("sub")
        token_type = payload.get("type", "access")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        # Accept both access and impersonation tokens
        if token_type not in ["access", "impersonation"]:
            raise HTTPException(status_code=401, detail="Type de token invalide")
        
        if not validate_uuid(user_id):
            raise HTTPException(status_code=401, detail="ID utilisateur invalide")
        
        user = await db.users.find_one(
            {"id": user_id},
            {"_id": 0, "password": 0}
        )
        
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        # Add impersonation flag to user if applicable
        if token_type == "impersonation":
            user["is_impersonated"] = True
            user["impersonated_by"] = payload.get("admin_id")
        else:
            user["is_impersonated"] = False
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

# ============== ROLE-BASED ACCESS CONTROL (RBAC) ==============

def check_user_role(user: dict, required_roles: List[str]) -> bool:
    """Check if user has one of the required roles"""
    user_role = user.get("role", ROLE_USER)
    return user_role in required_roles

async def require_admin(user: dict = Depends(get_current_user)):
    """Dependency that requires admin or super_admin role"""
    user_role = user.get("role", ROLE_USER)
    if user_role not in [ROLE_ADMIN, ROLE_SUPER_ADMIN]:
        logger.warning(f"Access denied: user {user.get('id')} with role {user_role} attempted admin action")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Droits administrateur requis."
        )
    return user

async def require_super_admin(user: dict = Depends(get_current_user)):
    """Dependency that requires super_admin role only"""
    user_role = user.get("role", ROLE_USER)
    if user_role != ROLE_SUPER_ADMIN:
        logger.warning(f"Access denied: user {user.get('id')} with role {user_role} attempted super_admin action")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Droits super-administrateur requis."
        )
    return user

def is_admin(user: dict) -> bool:
    """Helper function to check if user is admin or super_admin"""
    return user.get("role", ROLE_USER) in [ROLE_ADMIN, ROLE_SUPER_ADMIN]

def is_super_admin(user: dict) -> bool:
    """Helper function to check if user is super_admin"""
    return user.get("role", ROLE_USER) == ROLE_SUPER_ADMIN

# ============== ADMIN ACCOUNT INITIALIZATION ==============

async def init_super_admin():
    """Create super admin account on startup if it doesn't exist"""
    try:
        existing_admin = await db.users.find_one({"email": ADMIN_EMAIL})
        
        if not existing_admin:
            admin_id = str(uuid.uuid4())
            admin_doc = {
                "id": admin_id,
                "email": ADMIN_EMAIL,
                "password": hash_password(ADMIN_PASSWORD),
                "name": ADMIN_NAME,
                "role": ROLE_SUPER_ADMIN,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": None,
                "login_attempts": 0,
                "locked_until": None
            }
            await db.users.insert_one(admin_doc)
            logger.info(f"Super admin account created: {ADMIN_EMAIL}")
        else:
            # Ensure existing admin has super_admin role
            if existing_admin.get("role") != ROLE_SUPER_ADMIN:
                await db.users.update_one(
                    {"email": ADMIN_EMAIL},
                    {"$set": {"role": ROLE_SUPER_ADMIN, "is_active": True}}
                )
                logger.info(f"Super admin role restored for: {ADMIN_EMAIL}")
    except Exception as e:
        logger.error(f"Error initializing super admin: {str(e)}")

# ============== AUTH ROUTES ==============

class RegistrationResponse(BaseModel):
    """Response after initial registration"""
    message: str
    email: str
    requires_verification: bool = True

@api_router.post("/auth/register", response_model=RegistrationResponse)
@limiter.limit("5/hour")
async def register(request: Request, user_data: UserCreate):
    """Register a new user - requires email verification via OTP"""
    try:
        existing = await db.users.find_one({"email": user_data.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(user_data.password)
        
        user_doc = {
            "id": user_id,
            "email": user_data.email,
            "password": hashed_password,
            "name": user_data.name,
            "phone": user_data.phone,
            "company_name": user_data.company_name or "",
            "address": user_data.address or "",
            "role": ROLE_USER,
            "is_active": False,  # Inactive until email verified
            "email_verified": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": None,
            "login_attempts": 0,
            "locked_until": None
        }
        
        await db.users.insert_one(user_doc)
        
        # Generate and send OTP for email verification
        await generate_and_store_otp(user_data.email, OTP_TYPE_REGISTRATION)
        
        logger.info(f"User registered (pending verification): {user_id}")
        
        return RegistrationResponse(
            message="Compte créé. Vérifiez votre email pour le code de validation.",
            email=user_data.email,
            requires_verification=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'inscription")

@api_router.post("/auth/verify-email", response_model=TokenResponse)
@limiter.limit("10/hour")
async def verify_email(request: Request, data: OTPVerify):
    """Verify email with OTP and activate account"""
    try:
        if data.otp_type != OTP_TYPE_REGISTRATION:
            raise HTTPException(status_code=400, detail="Type OTP invalide")
        
        otp_doc = await verify_otp(data.email, data.otp_code, OTP_TYPE_REGISTRATION)
        
        if not otp_doc:
            raise HTTPException(status_code=400, detail="Code OTP invalide ou expiré")
        
        # Activate user account
        user = await db.users.find_one({"email": data.email})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        await db.users.update_one(
            {"email": data.email},
            {"$set": {
                "is_active": True,
                "email_verified": True,
                "last_login": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        access_token = create_token(user["id"], "access")
        refresh_token = create_token(user["id"], "refresh")
        
        logger.info(f"Email verified and account activated: {user['id']}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(
                id=user["id"], 
                email=user["email"], 
                name=user["name"], 
                role=user.get("role", ROLE_USER),
                phone=user.get("phone"),
                email_verified=True
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la vérification")

@api_router.post("/auth/resend-otp")
@limiter.limit("3/hour")
async def resend_otp(request: Request, data: OTPRequest):
    """Resend OTP code"""
    try:
        user = await db.users.find_one({"email": data.email})
        if not user:
            # Don't reveal if email exists
            return {"message": "Si cet email existe, un code a été envoyé"}
        
        # For registration OTP, only send if not verified
        if data.otp_type == OTP_TYPE_REGISTRATION and user.get("email_verified"):
            raise HTTPException(status_code=400, detail="Email déjà vérifié")
        
        await generate_and_store_otp(data.email, data.otp_type, data.target_user_id)
        
        return {"message": "Code envoyé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend OTP error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi")

@api_router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, user_data: UserLogin):
    try:
        user = await db.users.find_one({"email": user_data.email})
        
        if user and user.get("locked_until"):
            if datetime.fromisoformat(user["locked_until"]) > datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=429,
                    detail="Compte bloqué. Réessayez plus tard."
                )
        
        if not user or not verify_password(user_data.password, user["password"]):
            if user:
                attempts = user.get("login_attempts", 0) + 1
                update_data = {"login_attempts": attempts}
                
                if attempts >= 5:
                    lock_time = datetime.now(timezone.utc) + timedelta(minutes=30)
                    update_data["locked_until"] = lock_time.isoformat()
                
                await db.users.update_one(
                    {"id": user["id"]},
                    {"$set": update_data}
                )
            
            logger.warning(f"Failed login attempt for email: {user_data.email}")
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        
        # Check if email is verified (except for super admin)
        if not user.get("email_verified", False) and user.get("role") != ROLE_SUPER_ADMIN:
            # Generate new OTP for verification
            await generate_and_store_otp(user_data.email, OTP_TYPE_REGISTRATION)
            raise HTTPException(
                status_code=403, 
                detail="Email non vérifié. Un nouveau code a été envoyé."
            )
        
        # Check if user account is active
        if not user.get("is_active", True):
            logger.warning(f"Login attempt on disabled account: {user_data.email}")
            raise HTTPException(status_code=403, detail="Compte désactivé. Contactez l'administrateur.")
        
        await db.users.update_one(
            {"id": user["id"]},
            {
                "$set": {
                    "last_login": datetime.now(timezone.utc).isoformat(),
                    "login_attempts": 0,
                    "locked_until": None
                }
            }
        )
        
        access_token = create_token(user["id"], "access")
        refresh_token = create_token(user["id"], "refresh")
        
        user_role = user.get("role", ROLE_USER)
        logger.info(f"User logged in: {user['id']} with role: {user_role}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(
                id=user["id"], 
                email=user["email"], 
                name=user["name"], 
                role=user_role,
                phone=user.get("phone"),
                email_verified=user.get("email_verified", False)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la connexion")

class RefreshRequest(BaseModel):
    refresh_token: str

@api_router.post("/auth/refresh")
async def refresh_token(data: RefreshRequest):
    try:
        payload = jwt.decode(
            data.refresh_token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Type de token invalide")
        
        user_id = payload.get("sub")
        if not user_id or not validate_uuid(user_id):
            raise HTTPException(status_code=401, detail="Token invalide")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        access_token = create_token(user_id, "access")
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token de rafraîchissement expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token de rafraîchissement invalide")

@api_router.post("/auth/logout")
async def logout(user: dict = Depends(get_current_user)):
    logger.info(f"User logged out: {user['id']}")
    return {"message": "Déconnexion réussie"}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"], 
        email=user["email"], 
        name=user["name"],
        role=user.get("role", ROLE_USER),
        phone=user.get("phone"),
        email_verified=user.get("email_verified", False)
    )

@api_router.get("/auth/profile", response_model=UserDetailResponse)
async def get_profile(user: dict = Depends(get_current_user)):
    """Get current user's full profile"""
    return UserDetailResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        phone=user.get("phone", ""),
        company_name=user.get("company_name"),
        address=user.get("address"),
        role=user.get("role", ROLE_USER),
        created_at=user["created_at"],
        last_login=user.get("last_login"),
        is_active=user.get("is_active", True),
        email_verified=user.get("email_verified", False)
    )

@api_router.put("/auth/profile")
async def update_profile(profile_data: UserProfileUpdate, user: dict = Depends(get_current_user)):
    """Update current user's profile"""
    update_fields = {}
    
    if profile_data.name is not None:
        update_fields["name"] = profile_data.name
    if profile_data.phone is not None:
        update_fields["phone"] = profile_data.phone
    if profile_data.company_name is not None:
        update_fields["company_name"] = profile_data.company_name
    if profile_data.address is not None:
        update_fields["address"] = profile_data.address
    
    if update_fields:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": update_fields}
        )
        logger.info(f"Profile updated for user {user['id']}")
    
    # Return updated user
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password": 0})
    return UserDetailResponse(
        id=updated_user["id"],
        email=updated_user["email"],
        name=updated_user["name"],
        phone=updated_user.get("phone", ""),
        company_name=updated_user.get("company_name"),
        address=updated_user.get("address"),
        role=updated_user.get("role", ROLE_USER),
        created_at=updated_user["created_at"],
        last_login=updated_user.get("last_login"),
        is_active=updated_user.get("is_active", True),
        email_verified=updated_user.get("email_verified", False)
    )

@api_router.get("/auth/impersonation-status")
async def get_impersonation_status(user: dict = Depends(get_current_user)):
    """Check if current session is an impersonation session"""
    is_impersonated = user.get("is_impersonated", False)
    
    if is_impersonated:
        admin_id = user.get("impersonated_by")
        admin_user = await db.users.find_one({"id": admin_id}, {"_id": 0, "password": 0})
        return {
            "is_impersonated": True,
            "admin_name": admin_user["name"] if admin_user else "Admin",
            "admin_email": admin_user["email"] if admin_user else "",
            "user_name": user["name"],
            "user_email": user["email"]
        }
    
    return {"is_impersonated": False}

# ============== USER MANAGEMENT ROUTES (ADMIN ONLY) ==============

@api_router.get("/users", response_model=List[UserListResponse])
async def list_users(admin: dict = Depends(require_admin)):
    """List all users - Admin only"""
    try:
        users_cursor = db.users.find(
            {},
            {"_id": 0, "password": 0, "login_attempts": 0, "locked_until": 0}
        ).sort("created_at", -1)
        
        users = await users_cursor.to_list(length=100)
        
        return [
            UserListResponse(
                id=u["id"],
                email=u["email"],
                name=u["name"],
                role=u.get("role", ROLE_USER),
                created_at=u["created_at"],
                last_login=u.get("last_login"),
                is_active=u.get("is_active", True),
                email_verified=u.get("email_verified", False)
            )
            for u in users
        ]
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des utilisateurs")

@api_router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: str, admin: dict = Depends(require_admin)):
    """Get a specific user with full details - Admin only"""
    if not validate_uuid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    
    user = await db.users.find_one(
        {"id": user_id},
        {"_id": 0, "password": 0, "login_attempts": 0, "locked_until": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return UserDetailResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        phone=user.get("phone", ""),
        company_name=user.get("company_name"),
        address=user.get("address"),
        role=user.get("role", ROLE_USER),
        created_at=user["created_at"],
        last_login=user.get("last_login"),
        is_active=user.get("is_active", True),
        email_verified=user.get("email_verified", False)
    )

@api_router.post("/users/{user_id}/request-otp")
async def request_admin_otp(user_id: str, otp_type: str, admin: dict = Depends(require_admin)):
    """Request OTP for admin action on a user"""
    if otp_type not in [OTP_TYPE_DELETE_USER, OTP_TYPE_PROMOTE_ADMIN, OTP_TYPE_PASSWORD_RESET, OTP_TYPE_IMPERSONATION]:
        raise HTTPException(status_code=400, detail="Type OTP invalide pour cette action")
    
    if not validate_uuid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Generate OTP for admin's email
    await generate_and_store_otp(admin["email"], otp_type, user_id)
    
    return {"message": "Code OTP envoyé à votre adresse email"}

@api_router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, role_data: UserRoleUpdate, request: Request, admin: dict = Depends(require_admin)):
    """Update user role - Admin only. Requires OTP verification."""
    if not validate_uuid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Verify OTP
    otp_doc = await verify_otp(admin["email"], role_data.otp_code, OTP_TYPE_PROMOTE_ADMIN)
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Code OTP invalide ou expiré")
    
    # Verify target user matches OTP
    if otp_doc.get("target_user_id") != user_id:
        raise HTTPException(status_code=400, detail="OTP non valide pour cet utilisateur")
    
    # Prevent modifying super admin unless you are super admin
    if target_user.get("role") == ROLE_SUPER_ADMIN and not is_super_admin(admin):
        raise HTTPException(status_code=403, detail="Impossible de modifier un super administrateur")
    
    # Only super admin can assign super_admin role
    if role_data.role == ROLE_SUPER_ADMIN and not is_super_admin(admin):
        raise HTTPException(status_code=403, detail="Seul un super administrateur peut attribuer ce rôle")
    
    # Prevent removing your own admin role
    if admin["id"] == user_id and role_data.role == ROLE_USER:
        raise HTTPException(status_code=400, detail="Impossible de retirer vos propres droits administrateur")
    
    old_role = target_user.get("role", ROLE_USER)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": role_data.role}}
    )
    
    # Create audit log
    client_ip = request.client.host if request.client else None
    await create_audit_log(
        action="ROLE_CHANGE",
        actor_id=admin["id"],
        actor_email=admin["email"],
        target_id=user_id,
        target_email=target_user["email"],
        details=f"Role changed from {old_role} to {role_data.role}",
        ip_address=client_ip
    )
    
    logger.info(f"User {admin['id']} changed role of user {user_id} to {role_data.role}")
    
    return {"message": f"Rôle modifié en '{role_data.role}'", "user_id": user_id, "new_role": role_data.role}

@api_router.patch("/users/{user_id}/activate")
async def activate_user(user_id: str, admin: dict = Depends(require_admin)):
    """Activate a user account - Admin only"""
    if not validate_uuid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": True}}
    )
    
    logger.info(f"User {admin['id']} activated user {user_id}")
    return {"message": "Compte activé", "user_id": user_id}

@api_router.patch("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, admin: dict = Depends(require_admin)):
    """Deactivate a user account - Admin only. Cannot deactivate super admin."""
    if not validate_uuid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Prevent deactivating super admin
    if target_user.get("role") == ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Impossible de désactiver le compte super administrateur")
    
    # Prevent self-deactivation
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Impossible de désactiver votre propre compte")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": False}}
    )
    
    logger.info(f"User {admin['id']} deactivated user {user_id}")
    return {"message": "Compte désactivé", "user_id": user_id}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, data: UserDeleteRequest, request: Request, admin: dict = Depends(require_super_admin)):
    """Delete a user - Super Admin only. Requires OTP verification."""
    if not validate_uuid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Verify OTP
    otp_doc = await verify_otp(admin["email"], data.otp_code, OTP_TYPE_DELETE_USER)
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Code OTP invalide ou expiré")
    
    # Verify target user matches OTP
    if otp_doc.get("target_user_id") != user_id:
        raise HTTPException(status_code=400, detail="OTP non valide pour cet utilisateur")
    
    # Prevent deleting super admin
    if target_user.get("role") == ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Impossible de supprimer le compte super administrateur")
    
    # Prevent self-deletion
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Impossible de supprimer votre propre compte")
    
    await db.users.delete_one({"id": user_id})
    
    # Create audit log
    client_ip = request.client.host if request.client else None
    await create_audit_log(
        action="USER_DELETED",
        actor_id=admin["id"],
        actor_email=admin["email"],
        target_id=user_id,
        target_email=target_user["email"],
        details="User account permanently deleted",
        ip_address=client_ip
    )
    
    logger.info(f"Super admin {admin['id']} deleted user {user_id}")
    return {"message": "Utilisateur supprimé", "user_id": user_id}

@api_router.post("/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, data: PasswordResetRequest, request: Request, admin: dict = Depends(require_admin)):
    """Reset a user's password - Admin only. Requires OTP verification."""
    if not validate_uuid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    
    if data.user_id != user_id:
        raise HTTPException(status_code=400, detail="ID utilisateur ne correspond pas")
    
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Verify OTP
    otp_doc = await verify_otp(admin["email"], data.otp_code, OTP_TYPE_PASSWORD_RESET)
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Code OTP invalide ou expiré")
    
    if otp_doc.get("target_user_id") != user_id:
        raise HTTPException(status_code=400, detail="OTP non valide pour cet utilisateur")
    
    # Cannot reset super admin password unless you are super admin
    if target_user.get("role") == ROLE_SUPER_ADMIN and not is_super_admin(admin):
        raise HTTPException(status_code=403, detail="Impossible de modifier le mot de passe d'un super administrateur")
    
    # Hash and update password
    hashed_password = hash_password(data.new_password)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password": hashed_password}}
    )
    
    # Create audit log
    client_ip = request.client.host if request.client else None
    await create_audit_log(
        action="PASSWORD_RESET",
        actor_id=admin["id"],
        actor_email=admin["email"],
        target_id=user_id,
        target_email=target_user["email"],
        details="Password reset by admin",
        ip_address=client_ip
    )
    
    logger.info(f"Admin {admin['id']} reset password for user {user_id}")
    return {"message": "Mot de passe réinitialisé avec succès"}

# ============== IMPERSONATION (SUPER ADMIN ONLY) ==============

@api_router.post("/admin/impersonate", response_model=TokenResponse)
async def impersonate_user(data: ImpersonationRequest, request: Request, admin: dict = Depends(require_super_admin)):
    """Impersonate a user - Super Admin only. Requires OTP verification."""
    if not validate_uuid(data.target_user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    
    target_user = await db.users.find_one({"id": data.target_user_id}, {"_id": 0, "password": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Verify OTP
    otp_doc = await verify_otp(admin["email"], data.otp_code, OTP_TYPE_IMPERSONATION)
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Code OTP invalide ou expiré")
    
    if otp_doc.get("target_user_id") != data.target_user_id:
        raise HTTPException(status_code=400, detail="OTP non valide pour cet utilisateur")
    
    # Cannot impersonate another super admin
    if target_user.get("role") == ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Impossible d'usurper un autre super administrateur")
    
    # Create impersonation token with special flag
    impersonation_token = create_impersonation_token(admin["id"], target_user["id"])
    
    # Create audit log
    client_ip = request.client.host if request.client else None
    await create_audit_log(
        action="IMPERSONATION_START",
        actor_id=admin["id"],
        actor_email=admin["email"],
        target_id=target_user["id"],
        target_email=target_user["email"],
        details="Super admin started impersonation session",
        ip_address=client_ip
    )
    
    # Store impersonation session
    session_id = str(uuid.uuid4())
    await db.impersonation_sessions.insert_one({
        "id": session_id,
        "admin_id": admin["id"],
        "target_user_id": target_user["id"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "active": True
    })
    
    logger.info(f"Super admin {admin['id']} started impersonating user {target_user['id']}")
    
    return TokenResponse(
        access_token=impersonation_token,
        refresh_token=None,  # No refresh token for impersonation
        user=UserResponse(
            id=target_user["id"],
            email=target_user["email"],
            name=target_user["name"],
            role=target_user.get("role", ROLE_USER),
            phone=target_user.get("phone"),
            email_verified=target_user.get("email_verified", False)
        )
    )

@api_router.post("/admin/stop-impersonation")
async def stop_impersonation(request: Request, user: dict = Depends(get_current_user)):
    """Stop impersonation session and return to admin"""
    # Check if this is an impersonation session
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "impersonation":
            raise HTTPException(status_code=400, detail="Pas de session d'usurpation active")
        
        admin_id = payload.get("admin_id")
        target_id = payload.get("sub")
        
        # End impersonation session
        await db.impersonation_sessions.update_one(
            {"admin_id": admin_id, "target_user_id": target_id, "active": True},
            {"$set": {"active": False, "ended_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Get admin user
        admin_user = await db.users.find_one({"id": admin_id}, {"_id": 0, "password": 0})
        if not admin_user:
            raise HTTPException(status_code=404, detail="Admin non trouvé")
        
        # Create audit log
        client_ip = request.client.host if request.client else None
        await create_audit_log(
            action="IMPERSONATION_END",
            actor_id=admin_id,
            actor_email=admin_user["email"],
            target_id=target_id,
            target_email=user["email"],
            details="Super admin ended impersonation session",
            ip_address=client_ip
        )
        
        # Generate new admin token
        access_token = create_token(admin_id, "access")
        refresh_token = create_token(admin_id, "refresh")
        
        logger.info(f"Super admin {admin_id} stopped impersonating user {target_id}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(
                id=admin_user["id"],
                email=admin_user["email"],
                name=admin_user["name"],
                role=admin_user.get("role", ROLE_USER),
                phone=admin_user.get("phone"),
                email_verified=admin_user.get("email_verified", False)
            )
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Token invalide")

# ============== WEBSITE REQUEST ROUTES ==============

ADMIN_NOTIFICATION_EMAIL = os.environ.get("ADMIN_NOTIFICATION_EMAIL", "admin@btpfacture.com")

@api_router.post("/website-requests", response_model=WebsiteRequestResponse)
async def create_website_request(data: WebsiteRequestCreate, user: dict = Depends(get_current_user)):
    """Create a website creation request"""
    request_id = str(uuid.uuid4())
    
    request_doc = {
        "id": request_id,
        "user_id": user["id"],
        "user_name": user["name"],
        "user_email": user["email"],
        "user_phone": user.get("phone", ""),
        "company_name": user.get("company_name"),
        "activity_type": data.activity_type,
        "objective": data.objective,
        "budget": data.budget,
        "timeline": data.timeline,
        "additional_notes": data.additional_notes,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    
    await db.website_requests.insert_one(request_doc)
    
    # Log the request (email notification in production)
    logger.info(f"[WEBSITE REQUEST] New request from {user['email']}: {data.activity_type}")
    
    # Send email notification if configured
    if RESEND_CONFIGURED:
        try:
            resend.emails.send({
                "from": SENDER_EMAIL,
                "to": [ADMIN_NOTIFICATION_EMAIL],
                "subject": f"Nouvelle demande de site web - {user['name']}",
                "html": f"""
                <h2>Nouvelle demande de création de site web</h2>
                <p><strong>Client:</strong> {user['name']} ({user['email']})</p>
                <p><strong>Téléphone:</strong> {user.get('phone', 'Non renseigné')}</p>
                <p><strong>Entreprise:</strong> {user.get('company_name', 'Non renseigné')}</p>
                <hr>
                <p><strong>Type d'activité:</strong> {data.activity_type}</p>
                <p><strong>Objectif:</strong> {data.objective}</p>
                <p><strong>Budget:</strong> {data.budget}</p>
                <p><strong>Délai souhaité:</strong> {data.timeline}</p>
                <p><strong>Notes:</strong> {data.additional_notes or 'Aucune'}</p>
                """
            })
        except Exception as e:
            logger.error(f"Failed to send website request notification: {str(e)}")
    
    return WebsiteRequestResponse(**{k: v for k, v in request_doc.items() if k != "_id"})

@api_router.get("/website-requests", response_model=List[WebsiteRequestResponse])
async def list_website_requests(admin: dict = Depends(require_admin)):
    """List all website requests - Admin only"""
    requests_cursor = db.website_requests.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1)
    
    requests = await requests_cursor.to_list(length=100)
    return [WebsiteRequestResponse(**r) for r in requests]

@api_router.patch("/website-requests/{request_id}/status")
async def update_website_request_status(request_id: str, status: str, admin: dict = Depends(require_admin)):
    """Update website request status - Admin only"""
    valid_statuses = ["pending", "contacted", "in_progress", "completed", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Valeurs: {valid_statuses}")
    
    result = await db.website_requests.update_one(
        {"id": request_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    return {"message": "Statut mis à jour", "status": status}

# ============== CLIENT ROUTES ==============

@api_router.post("/clients", response_model=ClientResponse)
async def create_client(client_data: ClientCreate, user: dict = Depends(get_current_user)):
    try:
        client_id = str(uuid.uuid4())
        client_doc = {
            "id": client_id,
            "owner_id": user["id"],
            "name": client_data.name,
            "address": client_data.address,
            "phone": client_data.phone,
            "email": client_data.email,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.clients.insert_one(client_doc)
        
        logger.info(f"Client created: {client_id}")
        
        return ClientResponse(**client_doc)
        
    except Exception as e:
        logger.error(f"Client creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création du client")

@api_router.get("/clients", response_model=List[ClientResponse])
async def list_clients(user: dict = Depends(get_current_user)):
    try:
        clients = await db.clients.find(
            {"owner_id": user["id"]},
            {"_id": 0}
        ).to_list(1000)
        
        return [ClientResponse(**c) for c in clients]
        
    except Exception as e:
        logger.error(f"List clients error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des clients")

@api_router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(client_id):
        raise HTTPException(status_code=400, detail="ID client invalide")
    
    client = await db.clients.find_one(
        {"id": client_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    return ClientResponse(**client)

@api_router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, client_data: ClientUpdate, user: dict = Depends(get_current_user)):
    if not validate_uuid(client_id):
        raise HTTPException(status_code=400, detail="ID client invalide")
    
    update_data = {k: v for k, v in client_data.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
    
    result = await db.clients.update_one(
        {"id": client_id, "owner_id": user["id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    client = await db.clients.find_one(
        {"id": client_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    return ClientResponse(**client)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(client_id):
        raise HTTPException(status_code=400, detail="ID client invalide")
    
    result = await db.clients.delete_one(
        {"id": client_id, "owner_id": user["id"]}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    logger.info(f"Client deleted: {client_id}")
    
    return {"message": "Client supprimé"}

# ============== QUOTE HELPERS ==============

async def get_next_quote_number():
    year = datetime.now().year
    counter = await db.counters.find_one_and_update(
        {"_id": f"quote_{year}"},
        {"$inc": {"sequence": 1}},
        upsert=True,
        return_document=True
    )
    sequence = counter.get("sequence", 1)
    return f"DEV-{year}-{str(sequence).zfill(4)}"

async def get_next_invoice_number():
    year = datetime.now().year
    counter = await db.counters.find_one_and_update(
        {"_id": f"invoice_{year}"},
        {"$inc": {"sequence": 1}},
        upsert=True,
        return_document=True
    )
    sequence = counter.get("sequence", 1)
    return f"FAC-{year}-{str(sequence).zfill(4)}"

def calculate_totals(items: List[dict], is_auto_entrepreneur: bool = False) -> tuple:
    total_ht = sum(item["quantity"] * item["unit_price"] for item in items)
    
    if is_auto_entrepreneur:
        total_vat = 0.0
    else:
        total_vat = sum(item["quantity"] * item["unit_price"] * item["vat_rate"] / 100 for item in items)
    
    total_ttc = total_ht + total_vat
    
    return round(total_ht, 2), round(total_vat, 2), round(total_ttc, 2)

async def get_company_settings():
    settings = await db.settings.find_one(
        {"type": "company"},
        {"_id": 0}
    )
    return settings or {}

# ============== QUOTE ROUTES ==============

@api_router.post("/quotes", response_model=QuoteResponse)
async def create_quote(quote_data: QuoteCreate, user: dict = Depends(get_current_user)):
    try:
        if not validate_uuid(quote_data.client_id):
            raise HTTPException(status_code=400, detail="ID client invalide")
        
        client = await db.clients.find_one(
            {"id": quote_data.client_id, "owner_id": user["id"]},
            {"_id": 0}
        )
        
        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        
        settings = await get_company_settings()
        
        quote_id = str(uuid.uuid4())
        quote_number = await get_next_quote_number()
        
        items = [item.dict() for item in quote_data.items]
        
        if settings.get("is_auto_entrepreneur"):
            for item in items:
                item["vat_rate"] = 0.0
        
        total_ht, total_vat, total_ttc = calculate_totals(items, settings.get("is_auto_entrepreneur", False))
        
        issue_date = datetime.now(timezone.utc)
        validity_date = issue_date + timedelta(days=quote_data.validity_days)
        
        quote_doc = {
            "id": quote_id,
            "owner_id": user["id"],
            "quote_number": quote_number,
            "client_id": quote_data.client_id,
            "client_name": client["name"],
            "issue_date": issue_date.isoformat(),
            "validity_date": validity_date.isoformat(),
            "items": items,
            "total_ht": total_ht,
            "total_vat": total_vat,
            "total_ttc": total_ttc,
            "status": "brouillon",
            "notes": quote_data.notes,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.quotes.insert_one(quote_doc)
        
        logger.info(f"Quote created: {quote_number}")
        
        return QuoteResponse(**quote_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quote creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création du devis")

@api_router.get("/quotes", response_model=List[QuoteResponse])
async def list_quotes(
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    try:
        query = {"owner_id": user["id"]}
        
        if status and status in ["brouillon", "envoye", "accepte", "refuse", "facture"]:
            query["status"] = status
        
        if client_id and validate_uuid(client_id):
            query["client_id"] = client_id
        
        quotes = await db.quotes.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
        
        return [QuoteResponse(**q) for q in quotes]
        
    except Exception as e:
        logger.error(f"List quotes error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des devis")

@api_router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    return QuoteResponse(**quote)

@api_router.put("/quotes/{quote_id}", response_model=QuoteResponse)
async def update_quote(quote_id: str, quote_data: QuoteUpdate, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    update_data = {}
    
    if quote_data.client_id:
        if not validate_uuid(quote_data.client_id):
            raise HTTPException(status_code=400, detail="ID client invalide")
        
        client = await db.clients.find_one(
            {"id": quote_data.client_id, "owner_id": user["id"]},
            {"_id": 0}
        )
        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        update_data["client_id"] = quote_data.client_id
        update_data["client_name"] = client["name"]
    
    if quote_data.validity_days:
        issue_date = datetime.fromisoformat(quote["issue_date"].replace('Z', '+00:00'))
        validity_date = issue_date + timedelta(days=quote_data.validity_days)
        update_data["validity_date"] = validity_date.isoformat()
    
    if quote_data.items:
        settings = await get_company_settings()
        items = [item.dict() for item in quote_data.items]
        if settings.get("is_auto_entrepreneur"):
            items = [{**item, "vat_rate": 0.0} for item in items]
        total_ht, total_vat, total_ttc = calculate_totals(items, settings.get("is_auto_entrepreneur", False))
        update_data["items"] = items
        update_data["total_ht"] = total_ht
        update_data["total_vat"] = total_vat
        update_data["total_ttc"] = total_ttc
    
    if quote_data.notes is not None:
        update_data["notes"] = quote_data.notes
    
    if quote_data.status:
        update_data["status"] = quote_data.status
    
    if update_data:
        await db.quotes.update_one(
            {"id": quote_id, "owner_id": user["id"]},
            {"$set": update_data}
        )
    
    updated_quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    return QuoteResponse(**updated_quote)

@api_router.delete("/quotes/{quote_id}")
async def delete_quote(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    result = await db.quotes.delete_one(
        {"id": quote_id, "owner_id": user["id"]}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    logger.info(f"Quote deleted: {quote_id}")
    
    return {"message": "Devis supprimé"}

@api_router.post("/quotes/{quote_id}/convert", response_model=InvoiceResponse)
async def convert_quote_to_invoice(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote["status"] != "accepte":
        raise HTTPException(status_code=400, detail="Seuls les devis acceptés peuvent être convertis en facture")
    
    settings = await get_company_settings()
    
    invoice_id = str(uuid.uuid4())
    invoice_number = await get_next_invoice_number()
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=settings.get("default_payment_delay_days", 30))
    
    items = quote["items"]
    if settings.get("is_auto_entrepreneur"):
        items = [{**item, "vat_rate": 0.0} for item in items]
        total_ht, total_vat, total_ttc = calculate_totals(items, True)
    else:
        total_ht, total_vat, total_ttc = quote["total_ht"], quote["total_vat"], quote["total_ttc"]
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "owner_id": user["id"],
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": items,
        "total_ht": total_ht,
        "total_vat": total_vat,
        "total_ttc": total_ttc,
        "payment_status": "impaye",
        "payment_method": "virement",
        "paid_amount": 0,
        "notes": quote.get("notes", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.invoices.insert_one(invoice_doc)
    
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"status": "facture"}}
    )
    
    logger.info(f"Quote converted to invoice: {quote['quote_number']} -> {invoice_number}")
    
    return InvoiceResponse(**invoice_doc)
	
	# ============== INVOICE ROUTES ==============

@api_router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(invoice_data: InvoiceCreate, user: dict = Depends(get_current_user)):
    try:
        if not validate_uuid(invoice_data.client_id):
            raise HTTPException(status_code=400, detail="ID client invalide")
        
        client = await db.clients.find_one(
            {"id": invoice_data.client_id, "owner_id": user["id"]},
            {"_id": 0}
        )
        
        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        
        if invoice_data.quote_id and not validate_uuid(invoice_data.quote_id):
            raise HTTPException(status_code=400, detail="ID devis invalide")
        
        settings = await get_company_settings()
        payment_delay = invoice_data.payment_delay_days or settings.get("default_payment_delay_days", 30)
        
        invoice_id = str(uuid.uuid4())
        invoice_number = await get_next_invoice_number()
        
        items = [item.dict() for item in invoice_data.items]
        
        if settings.get("is_auto_entrepreneur"):
            for item in items:
                item["vat_rate"] = 0.0
        
        total_ht, total_vat, total_ttc = calculate_totals(items, settings.get("is_auto_entrepreneur", False))
        
        issue_date = datetime.now(timezone.utc)
        payment_due_date = issue_date + timedelta(days=payment_delay)
        
        invoice_doc = {
            "id": invoice_id,
            "invoice_number": invoice_number,
            "owner_id": user["id"],
            "client_id": invoice_data.client_id,
            "client_name": client["name"],
            "quote_id": invoice_data.quote_id,
            "issue_date": issue_date.isoformat(),
            "payment_due_date": payment_due_date.isoformat(),
            "items": items,
            "total_ht": total_ht,
            "total_vat": total_vat,
            "total_ttc": total_ttc,
            "payment_status": "impaye",
            "payment_method": invoice_data.payment_method,
            "paid_amount": 0,
            "notes": invoice_data.notes,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.invoices.insert_one(invoice_doc)
        
        logger.info(f"Invoice created: {invoice_number}")
        
        return InvoiceResponse(**invoice_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invoice creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création de la facture")

@api_router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    payment_status: Optional[str] = None,
    client_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    try:
        query = {"owner_id": user["id"]}
        
        if payment_status and payment_status in ["impaye", "partiel", "paye"]:
            query["payment_status"] = payment_status
        
        if client_id and validate_uuid(client_id):
            query["client_id"] = client_id
        
        invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
        
        for inv in invoices:
            inv.setdefault("is_acompte", False)
            inv.setdefault("acompte_type", None)
            inv.setdefault("acompte_value", None)
            inv.setdefault("parent_quote_id", None)
            inv.setdefault("acompte_number", None)
            inv.setdefault("is_situation", False)
            inv.setdefault("situation_number", None)
            inv.setdefault("situation_percentage", None)
            inv.setdefault("previous_percentage", None)
            inv.setdefault("chantier_ref", None)
            inv.setdefault("has_retenue_garantie", False)
            inv.setdefault("retenue_garantie_rate", 0)
            inv.setdefault("retenue_garantie_amount", 0)
            inv.setdefault("retenue_garantie_release_date", None)
            inv.setdefault("retenue_garantie_released", False)
            inv.setdefault("net_a_payer", inv["total_ttc"])
        
        return [InvoiceResponse(**i) for i in invoices]
        
    except Exception as e:
        logger.error(f"List invoices error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des factures")

@api_router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="ID facture invalide")
    
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    invoice.setdefault("is_acompte", False)
    invoice.setdefault("acompte_type", None)
    invoice.setdefault("acompte_value", None)
    invoice.setdefault("parent_quote_id", None)
    invoice.setdefault("acompte_number", None)
    invoice.setdefault("is_situation", False)
    invoice.setdefault("situation_number", None)
    invoice.setdefault("situation_percentage", None)
    invoice.setdefault("previous_percentage", None)
    invoice.setdefault("chantier_ref", None)
    invoice.setdefault("has_retenue_garantie", False)
    invoice.setdefault("retenue_garantie_rate", 0)
    invoice.setdefault("retenue_garantie_amount", 0)
    invoice.setdefault("retenue_garantie_release_date", None)
    invoice.setdefault("retenue_garantie_released", False)
    invoice.setdefault("net_a_payer", invoice["total_ttc"])
    
    return InvoiceResponse(**invoice)

@api_router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: str, invoice_data: InvoiceUpdate, user: dict = Depends(get_current_user)):
    if not validate_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="ID facture invalide")
    
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    update_data = {}
    
    if invoice_data.payment_status:
        update_data["payment_status"] = invoice_data.payment_status
    
    if invoice_data.payment_method:
        update_data["payment_method"] = invoice_data.payment_method
    
    if invoice_data.paid_amount is not None:
        update_data["paid_amount"] = invoice_data.paid_amount
        if invoice_data.paid_amount >= invoice["total_ttc"]:
            update_data["payment_status"] = "paye"
        elif invoice_data.paid_amount > 0:
            update_data["payment_status"] = "partiel"
    
    if invoice_data.notes is not None:
        update_data["notes"] = invoice_data.notes
    
    if update_data:
        await db.invoices.update_one(
            {"id": invoice_id, "owner_id": user["id"]},
            {"$set": update_data}
        )
    
    updated_invoice = await db.invoices.find_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    return InvoiceResponse(**updated_invoice)

@api_router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="ID facture invalide")
    
    result = await db.invoices.delete_one(
        {"id": invoice_id, "owner_id": user["id"]}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    logger.info(f"Invoice deleted: {invoice_id}")
    
    return {"message": "Facture supprimée"}

@api_router.post("/invoices/bulk-delete")
async def bulk_delete_invoices(invoice_ids: List[str], user: dict = Depends(get_current_user)):
    valid_ids = [id for id in invoice_ids if validate_uuid(id)]
    
    if not valid_ids:
        raise HTTPException(status_code=400, detail="Aucun ID valide fourni")
    
    result = await db.invoices.delete_many({
        "id": {"$in": valid_ids},
        "owner_id": user["id"]
    })
    
    logger.info(f"Bulk deleted {result.deleted_count} invoices")
    
    return {"message": f"{result.deleted_count} factures supprimées"}

# ============== ACOMPTES ROUTES ==============

@api_router.post("/quotes/{quote_id}/acompte", response_model=AcompteResponse)
async def create_acompte(quote_id: str, acompte_data: AcompteCreate, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote["status"] not in ["accepte", "envoye"]:
        raise HTTPException(status_code=400, detail="Le devis doit être accepté ou envoyé pour créer un acompte")
    
    settings = await get_company_settings()
    
    if acompte_data.acompte_type == "percentage":
        acompte_ht = quote["total_ht"] * (acompte_data.value / 100)
        acompte_vat = quote["total_vat"] * (acompte_data.value / 100) if not settings.get("is_auto_entrepreneur") else 0
    else:
        proportion = acompte_data.value / quote["total_ttc"] if quote["total_ttc"] > 0 else 0
        acompte_ht = quote["total_ht"] * proportion
        acompte_vat = quote["total_vat"] * proportion if not settings.get("is_auto_entrepreneur") else 0
    
    acompte_ttc = acompte_ht + acompte_vat
    
    existing_acomptes = await db.invoices.count_documents({"parent_quote_id": quote_id, "is_acompte": True})
    acompte_number = existing_acomptes + 1
    
    invoice_number = await get_next_invoice_number()
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=settings.get("default_payment_delay_days", 30))
    
    item_vat_rate = 0.0 if settings.get("is_auto_entrepreneur") else ((acompte_vat / acompte_ht * 100) if acompte_ht > 0 else 0)
    
    acompte_items = [{
        "description": f"Acompte n°{acompte_number} - {acompte_data.value}{'%' if acompte_data.acompte_type == 'percentage' else '€'} sur devis {quote['quote_number']}",
        "quantity": 1,
        "unit_price": round(acompte_ht, 2),
        "vat_rate": item_vat_rate,
        "unit": "forfait"
    }]
    
    acompte_doc = {
        "id": str(uuid.uuid4()),
        "invoice_number": invoice_number,
        "owner_id": user["id"],
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "parent_quote_id": quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": acompte_items,
        "total_ht": round(acompte_ht, 2),
        "total_vat": round(acompte_vat, 2),
        "total_ttc": round(acompte_ttc, 2),
        "payment_status": "impaye",
        "payment_method": acompte_data.payment_method,
        "paid_amount": 0,
        "notes": acompte_data.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_acompte": True,
        "acompte_type": acompte_data.acompte_type,
        "acompte_value": acompte_data.value,
        "acompte_number": acompte_number
    }
    
    await db.invoices.insert_one(acompte_doc)
    
    logger.info(f"Acompte created: {invoice_number} for quote {quote_id}")
    
    return AcompteResponse(
        id=acompte_doc["id"],
        invoice_number=invoice_number,
        quote_id=quote_id,
        quote_number=quote["quote_number"],
        client_id=acompte_doc["client_id"],
        client_name=acompte_doc["client_name"],
        issue_date=acompte_doc["issue_date"],
        payment_due_date=acompte_doc["payment_due_date"],
        acompte_type=acompte_doc["acompte_type"],
        acompte_value=acompte_doc["acompte_value"],
        acompte_number=acompte_doc["acompte_number"],
        total_ht=acompte_doc["total_ht"],
        total_vat=acompte_doc["total_vat"],
        total_ttc=acompte_doc["total_ttc"],
        payment_status=acompte_doc["payment_status"],
        payment_method=acompte_doc["payment_method"],
        paid_amount=acompte_doc["paid_amount"],
        notes=acompte_doc["notes"],
        created_at=acompte_doc["created_at"]
    )

@api_router.get("/quotes/{quote_id}/acomptes", response_model=List[AcompteResponse])
async def list_quote_acomptes(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    acomptes = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_acompte": True, "owner_id": user["id"]},
        {"_id": 0}
    ).sort("acompte_number", 1).to_list(100)
    
    return [
        AcompteResponse(
            id=a["id"],
            invoice_number=a["invoice_number"],
            quote_id=quote_id,
            quote_number=quote["quote_number"],
            client_id=a["client_id"],
            client_name=a["client_name"],
            issue_date=a["issue_date"],
            payment_due_date=a.get("payment_due_date", a["issue_date"]),
            acompte_type=a["acompte_type"],
            acompte_value=a["acompte_value"],
            acompte_number=a["acompte_number"],
            total_ht=a["total_ht"],
            total_vat=a["total_vat"],
            total_ttc=a["total_ttc"],
            payment_status=a["payment_status"],
            payment_method=a["payment_method"],
            paid_amount=a.get("paid_amount", 0),
            notes=a.get("notes", ""),
            created_at=a["created_at"]
        )
        for a in acomptes
    ]

@api_router.get("/quotes/{quote_id}/acomptes/summary")
async def get_acomptes_summary(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    acomptes = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_acompte": True, "owner_id": user["id"]},
        {"_id": 0}
    ).to_list(100)
    
    total_acomptes_ht = sum(a["total_ht"] for a in acomptes)
    total_acomptes_vat = sum(a["total_vat"] for a in acomptes)
    total_acomptes_ttc = sum(a["total_ttc"] for a in acomptes)
    total_paid = sum(a.get("paid_amount", 0) for a in acomptes if a["payment_status"] == "paye")
    
    remaining_ht = quote["total_ht"] - total_acomptes_ht
    remaining_vat = quote["total_vat"] - total_acomptes_vat
    remaining_ttc = quote["total_ttc"] - total_acomptes_ttc
    
    return {
        "quote_total_ht": quote["total_ht"],
        "quote_total_vat": quote["total_vat"],
        "quote_total_ttc": quote["total_ttc"],
        "acomptes_count": len(acomptes),
        "total_acomptes_ht": round(total_acomptes_ht, 2),
        "total_acomptes_vat": round(total_acomptes_vat, 2),
        "total_acomptes_ttc": round(total_acomptes_ttc, 2),
        "total_paid": round(total_paid, 2),
        "remaining_ht": round(max(0, remaining_ht), 2),
        "remaining_vat": round(max(0, remaining_vat), 2),
        "remaining_ttc": round(max(0, remaining_ttc), 2),
        "percentage_invoiced": round((total_acomptes_ttc / quote["total_ttc"] * 100) if quote["total_ttc"] > 0 else 0, 1),
        "percentage_paid": round((total_paid / quote["total_ttc"] * 100) if quote["total_ttc"] > 0 else 0, 1),
        "acomptes": [
            {
                "id": a["id"],
                "invoice_number": a["invoice_number"],
                "acompte_number": a["acompte_number"],
                "acompte_type": a["acompte_type"],
                "acompte_value": a["acompte_value"],
                "total_ttc": a["total_ttc"],
                "payment_status": a["payment_status"],
                "paid_amount": a.get("paid_amount", 0)
            }
            for a in acomptes
        ]
    }

@api_router.post("/quotes/{quote_id}/final-invoice", response_model=InvoiceResponse)
async def create_final_invoice(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote["status"] != "accepte":
        raise HTTPException(status_code=400, detail="Le devis doit être accepté pour créer la facture finale")
    
    settings = await get_company_settings()
    
    acomptes = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_acompte": True, "owner_id": user["id"]},
        {"_id": 0}
    ).to_list(100)
    
    total_acomptes_ttc = sum(a["total_ttc"] for a in acomptes if a["payment_status"] == "paye")
    
    invoice_id = str(uuid.uuid4())
    invoice_number = await get_next_invoice_number()
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=settings.get("default_payment_delay_days", 30))
    
    items = quote["items"]
    if settings.get("is_auto_entrepreneur"):
        items = [{**item, "vat_rate": 0.0} for item in items]
        total_ht = sum(item["quantity"] * item["unit_price"] for item in items)
        total_vat = 0.0
        total_ttc = total_ht
    else:
        total_ht = quote["total_ht"]
        total_vat = quote["total_vat"]
        total_ttc = quote["total_ttc"]
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "owner_id": user["id"],
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "parent_quote_id": quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": items,
        "total_ht": total_ht,
        "total_vat": total_vat,
        "total_ttc": total_ttc,
        "payment_status": "impaye",
        "payment_method": "virement",
        "paid_amount": 0,
        "notes": quote.get("notes", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_acompte": False,
        "is_final_invoice": True,
        "acomptes_deducted": total_acomptes_ttc,
        "net_to_pay": round(total_ttc - total_acomptes_ttc, 2)
    }
    
    await db.invoices.insert_one(invoice_doc)
    
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"status": "facture"}}
    )
    
    invoice_doc["acompte_type"] = None
    invoice_doc["acompte_value"] = None
    invoice_doc["acompte_number"] = None
    
    logger.info(f"Final invoice created: {invoice_number}")
    
    return InvoiceResponse(**invoice_doc)

# ============== SITUATIONS ROUTES ==============

@api_router.post("/quotes/{quote_id}/situation", response_model=SituationResponse)
async def create_situation(quote_id: str, situation_data: SituationCreate, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote["status"] not in ["accepte", "envoye"]:
        raise HTTPException(status_code=400, detail="Le devis doit être accepté ou envoyé pour créer une situation")
    
    settings = await get_company_settings()
    
    existing_situations = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_situation": True, "owner_id": user["id"]},
        {"_id": 0}
    ).sort("situation_number", -1).to_list(100)
    
    situation_number = len(existing_situations) + 1
    
    if existing_situations:
        previous_percentage = existing_situations[0].get("situation_percentage", 0) or 0
    else:
        previous_percentage = 0
    
    if situation_data.situation_type == "global":
        if situation_data.global_percentage is None or situation_data.global_percentage <= 0:
            raise HTTPException(status_code=400, detail="Le pourcentage global doit être supérieur à 0")
        
        if situation_data.global_percentage > 100:
            raise HTTPException(status_code=400, detail="Le pourcentage ne peut pas dépasser 100%")
        
        if situation_data.global_percentage <= previous_percentage:
            raise HTTPException(
                status_code=400,
                detail=f"Le pourcentage ({situation_data.global_percentage}%) doit être supérieur au cumul précédent ({previous_percentage}%)"
            )
        
        current_percentage = situation_data.global_percentage
        situation_percentage = current_percentage - previous_percentage
        
        situation_ht = quote["total_ht"] * (situation_percentage / 100)
        situation_vat = quote["total_vat"] * (situation_percentage / 100) if not settings.get("is_auto_entrepreneur") else 0
        situation_ttc = situation_ht + situation_vat
        
        situation_items = []
        for item in quote["items"]:
            item_ht = item["quantity"] * item["unit_price"] * (situation_percentage / 100)
            situation_items.append({
                "description": item["description"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "vat_rate": 0.0 if settings.get("is_auto_entrepreneur") else item["vat_rate"],
                "situation_percent": situation_percentage,
                "original_total_ht": item["quantity"] * item["unit_price"],
                "situation_amount_ht": round(item_ht, 2)
            })
    
    else:
        if not situation_data.line_items or len(situation_data.line_items) == 0:
            raise HTTPException(status_code=400, detail="Les lignes de situation sont requises")
        
        if len(situation_data.line_items) != len(quote["items"]):
            raise HTTPException(status_code=400, detail="Le nombre de lignes doit correspondre au devis")
        
        previous_line_progress = {}
        if existing_situations:
            last_situation = existing_situations[0]
            last_type = last_situation.get("situation_type", "global")
            
            if last_type == "global":
                global_cumul = last_situation.get("situation_percentage", 0)
                for quote_item in quote["items"]:
                    previous_line_progress[quote_item["description"]] = global_cumul
            else:
                for item in last_situation.get("items", []):
                    previous_line_progress[item.get("description", "")] = item.get("cumulative_percent", 0)
        
        situation_items = []
        total_situation_ht = 0
        total_situation_vat = 0
        
        for i, (quote_item, sit_item) in enumerate(zip(quote["items"], situation_data.line_items)):
            prev_progress = previous_line_progress.get(quote_item["description"], 0)
            
            if sit_item.progress_percent < prev_progress:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ligne {i+1}: le % ({sit_item.progress_percent}%) ne peut pas être inférieur au cumul précédent ({prev_progress}%)"
                )
            
            if sit_item.progress_percent > 100:
                raise HTTPException(status_code=400, detail=f"Ligne {i+1}: le pourcentage ne peut pas dépasser 100%")
            
            line_situation_percent = sit_item.progress_percent - prev_progress
            item_base_ht = quote_item["quantity"] * quote_item["unit_price"]
            item_situation_ht = item_base_ht * (line_situation_percent / 100)
            item_situation_vat = item_situation_ht * (quote_item["vat_rate"] / 100) if not settings.get("is_auto_entrepreneur") else 0
            
            total_situation_ht += item_situation_ht
            total_situation_vat += item_situation_vat
            
            situation_items.append({
                "description": quote_item["description"],
                "quantity": quote_item["quantity"],
                "unit_price": quote_item["unit_price"],
                "vat_rate": 0.0 if settings.get("is_auto_entrepreneur") else quote_item["vat_rate"],
                "situation_percent": line_situation_percent,
                "cumulative_percent": sit_item.progress_percent,
                "original_total_ht": item_base_ht,
                "situation_amount_ht": round(item_situation_ht, 2)
            })
        
        situation_ht = total_situation_ht
        situation_vat = total_situation_vat
        situation_ttc = situation_ht + situation_vat
        
        total_weight = sum(item["original_total_ht"] for item in situation_items)
        if total_weight > 0:
            current_percentage = sum(
                item["cumulative_percent"] * item["original_total_ht"] / total_weight
                for item in situation_items
            )
        else:
            current_percentage = 0
        
        situation_percentage = current_percentage - previous_percentage
    
    invoice_number = await get_next_invoice_number()
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=settings.get("default_payment_delay_days", 30))
    
    situation_doc = {
        "id": str(uuid.uuid4()),
        "invoice_number": invoice_number,
        "owner_id": user["id"],
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "parent_quote_id": quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": situation_items,
        "total_ht": round(situation_ht, 2),
        "total_vat": round(situation_vat, 2),
        "total_ttc": round(situation_ttc, 2),
        "payment_status": "impaye",
        "payment_method": situation_data.payment_method,
        "paid_amount": 0,
        "notes": situation_data.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_situation": True,
        "situation_type": situation_data.situation_type,
        "situation_number": situation_number,
        "situation_percentage": round(current_percentage, 2),
        "previous_percentage": round(previous_percentage, 2),
        "chantier_ref": situation_data.chantier_ref or f"Chantier {quote['quote_number']}"
    }
    
    await db.invoices.insert_one(situation_doc)
    
    logger.info(f"Situation created: {invoice_number} for quote {quote_id}")
    
    return SituationResponse(
        id=situation_doc["id"],
        invoice_number=invoice_number,
        quote_id=quote_id,
        quote_number=quote["quote_number"],
        client_id=situation_doc["client_id"],
        client_name=situation_doc["client_name"],
        issue_date=situation_doc["issue_date"],
        payment_due_date=situation_doc["payment_due_date"],
        situation_type=situation_doc["situation_type"],
        situation_number=situation_doc["situation_number"],
        current_percentage=situation_doc["situation_percentage"],
        previous_percentage=situation_doc["previous_percentage"],
        situation_percentage=round(situation_percentage, 2),
        items=situation_doc["items"],
        total_ht=situation_doc["total_ht"],
        total_vat=situation_doc["total_vat"],
        total_ttc=situation_doc["total_ttc"],
        payment_status=situation_doc["payment_status"],
        payment_method=situation_doc["payment_method"],
        paid_amount=situation_doc["paid_amount"],
        notes=situation_doc["notes"],
        chantier_ref=situation_doc["chantier_ref"],
        created_at=situation_doc["created_at"]
    )

@api_router.get("/quotes/{quote_id}/situations", response_model=List[SituationResponse])
async def list_quote_situations(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    situations = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_situation": True, "owner_id": user["id"]},
        {"_id": 0}
    ).sort("situation_number", 1).to_list(100)
    
    result = []
    for i, s in enumerate(situations):
        prev_pct = situations[i-1].get("situation_percentage", 0) if i > 0 else 0
        current_pct = s.get("situation_percentage", 0)
        sit_pct = current_pct - prev_pct
        
        result.append(SituationResponse(
            id=s["id"],
            invoice_number=s["invoice_number"],
            quote_id=quote_id,
            quote_number=quote["quote_number"],
            client_id=s["client_id"],
            client_name=s["client_name"],
            issue_date=s["issue_date"],
            payment_due_date=s.get("payment_due_date", s["issue_date"]),
            situation_type=s.get("situation_type", "global"),
            situation_number=s["situation_number"],
            current_percentage=current_pct,
            previous_percentage=s.get("previous_percentage", prev_pct),
            situation_percentage=round(sit_pct, 2),
            items=s.get("items", []),
            total_ht=s["total_ht"],
            total_vat=s["total_vat"],
            total_ttc=s["total_ttc"],
            payment_status=s["payment_status"],
            payment_method=s["payment_method"],
            paid_amount=s.get("paid_amount", 0),
            notes=s.get("notes", ""),
            chantier_ref=s.get("chantier_ref", ""),
            created_at=s["created_at"]
        ))
    
    return result

@api_router.get("/quotes/{quote_id}/situations/summary")
async def get_situations_summary(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    situations = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_situation": True, "owner_id": user["id"]},
        {"_id": 0}
    ).sort("situation_number", 1).to_list(100)
    
    total_situations_ht = sum(s["total_ht"] for s in situations)
    total_situations_vat = sum(s["total_vat"] for s in situations)
    total_situations_ttc = sum(s["total_ttc"] for s in situations)
    total_paid = sum(s.get("paid_amount", 0) for s in situations if s["payment_status"] == "paye")
    
    remaining_ht = quote["total_ht"] - total_situations_ht
    remaining_vat = quote["total_vat"] - total_situations_vat
    remaining_ttc = quote["total_ttc"] - total_situations_ttc
    
    current_progress = situations[-1].get("situation_percentage", 0) if situations else 0
    
    line_progress = []
    if situations:
        last_situation = situations[-1]
        for item in last_situation.get("items", []):
            line_progress.append({
                "description": item.get("description", ""),
                "cumulative_percent": item.get("cumulative_percent", item.get("situation_percent", 0))
            })
    
    return {
        "quote_total_ht": quote["total_ht"],
        "quote_total_vat": quote["total_vat"],
        "quote_total_ttc": quote["total_ttc"],
        "situations_count": len(situations),
        "current_progress_percentage": round(current_progress, 2),
        "total_situations_ht": round(total_situations_ht, 2),
        "total_situations_vat": round(total_situations_vat, 2),
        "total_situations_ttc": round(total_situations_ttc, 2),
        "total_paid": round(total_paid, 2),
        "remaining_ht": round(max(0, remaining_ht), 2),
        "remaining_vat": round(max(0, remaining_vat), 2),
        "remaining_ttc": round(max(0, remaining_ttc), 2),
        "percentage_invoiced": round(current_progress, 2),
        "percentage_paid": round((total_paid / quote["total_ttc"] * 100) if quote["total_ttc"] > 0 else 0, 1),
        "line_progress": line_progress,
        "situations": [
            {
                "id": s["id"],
                "invoice_number": s["invoice_number"],
                "situation_number": s["situation_number"],
                "situation_type": s.get("situation_type", "global"),
                "cumulative_percentage": s.get("situation_percentage", 0),
                "total_ttc": s["total_ttc"],
                "payment_status": s["payment_status"],
                "paid_amount": s.get("paid_amount", 0)
            }
            for s in situations
        ]
    }

@api_router.post("/quotes/{quote_id}/situation/final-invoice", response_model=InvoiceResponse)
async def create_situation_final_invoice(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote["status"] != "accepte":
        raise HTTPException(status_code=400, detail="Le devis doit être accepté pour créer la facture finale")
    
    settings = await get_company_settings()
    
    situations = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_situation": True, "owner_id": user["id"]},
        {"_id": 0}
    ).sort("situation_number", 1).to_list(100)
    
    if not situations:
        raise HTTPException(status_code=400, detail="Aucune situation trouvée. Créez d'abord des situations.")
    
    total_situations_ttc = sum(s["total_ttc"] for s in situations)
    total_paid_situations = sum(s.get("paid_amount", 0) for s in situations if s["payment_status"] == "paye")
    
    invoice_id = str(uuid.uuid4())
    invoice_number = await get_next_invoice_number()
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=settings.get("default_payment_delay_days", 30))
    
    items = quote["items"]
    if settings.get("is_auto_entrepreneur"):
        items = [{**item, "vat_rate": 0.0} for item in items]
        total_ht = sum(item["quantity"] * item["unit_price"] for item in items)
        total_vat = 0.0
        total_ttc = total_ht
    else:
        total_ht = quote["total_ht"]
        total_vat = quote["total_vat"]
        total_ttc = quote["total_ttc"]
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "owner_id": user["id"],
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "parent_quote_id": quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": items,
        "total_ht": total_ht,
        "total_vat": total_vat,
        "total_ttc": total_ttc,
        "payment_status": "impaye",
        "payment_method": "virement",
        "paid_amount": 0,
        "notes": quote.get("notes", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_acompte": False,
        "is_final_invoice": True,
        "is_situation_final": True,
        "situations_deducted": total_situations_ttc,
        "situations_recap": [
            {
                "invoice_number": s["invoice_number"],
                "situation_number": s["situation_number"],
                "percentage": s.get("situation_percentage", 0),
                "total_ttc": s["total_ttc"],
                "payment_status": s["payment_status"]
            }
            for s in situations
        ],
        "net_to_pay": round(total_ttc - total_situations_ttc, 2)
    }
    
    await db.invoices.insert_one(invoice_doc)
    
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"status": "facture"}}
    )
    
    invoice_doc["acompte_type"] = None
    invoice_doc["acompte_value"] = None
    invoice_doc["acompte_number"] = None
    
    logger.info(f"Situation final invoice created: {invoice_number}")
    
    return InvoiceResponse(**invoice_doc)

# ============== RETENUE DE GARANTIE ROUTES ==============

@api_router.post("/invoices/{invoice_id}/retenue-garantie")
async def apply_retenue_garantie(invoice_id: str, retenue_data: RetenueGarantieCreate, user: dict = Depends(get_current_user)):
    if not validate_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="ID facture invalide")
    
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if retenue_data.rate > 5.0:
        raise HTTPException(status_code=400, detail="La retenue de garantie ne peut pas dépasser 5%")
    if retenue_data.rate <= 0:
        raise HTTPException(status_code=400, detail="Le taux doit être supérieur à 0")
    
    total_ttc = invoice["total_ttc"]
    retenue_amount = round(total_ttc * (retenue_data.rate / 100), 2)
    net_a_payer = round(total_ttc - retenue_amount, 2)
    
    issue_date = datetime.fromisoformat(invoice["issue_date"].replace("Z", "+00:00"))
    release_date = issue_date + timedelta(days=retenue_data.warranty_months * 30)
    
    update_data = {
        "has_retenue_garantie": True,
        "retenue_garantie_rate": retenue_data.rate,
        "retenue_garantie_amount": retenue_amount,
        "retenue_garantie_release_date": release_date.isoformat(),
        "retenue_garantie_released": False,
        "net_a_payer": net_a_payer
    }
    
    await db.invoices.update_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"$set": update_data}
    )
    
    logger.info(f"Retenue garantie applied to invoice {invoice_id}")
    
    return {
        "message": "Retenue de garantie appliquée",
        "invoice_id": invoice_id,
        "total_ttc": total_ttc,
        "retenue_rate": retenue_data.rate,
        "retenue_amount": retenue_amount,
        "net_a_payer": net_a_payer,
        "release_date": release_date.isoformat()
    }

@api_router.delete("/invoices/{invoice_id}/retenue-garantie")
async def remove_retenue_garantie(invoice_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="ID facture invalide")
    
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if invoice.get("retenue_garantie_released"):
        raise HTTPException(status_code=400, detail="La retenue a déjà été libérée")
    
    update_data = {
        "has_retenue_garantie": False,
        "retenue_garantie_rate": 0,
        "retenue_garantie_amount": 0,
        "retenue_garantie_release_date": None,
        "retenue_garantie_released": False,
        "net_a_payer": invoice["total_ttc"]
    }
    
    await db.invoices.update_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"$set": update_data}
    )
    
    logger.info(f"Retenue garantie removed from invoice {invoice_id}")
    
    return {"message": "Retenue de garantie supprimée", "invoice_id": invoice_id}

@api_router.post("/invoices/{invoice_id}/retenue-garantie/release")
async def release_retenue_garantie(invoice_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="ID facture invalide")
    
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if not invoice.get("has_retenue_garantie"):
        raise HTTPException(status_code=400, detail="Cette facture n'a pas de retenue de garantie")
    
    if invoice.get("retenue_garantie_released"):
        raise HTTPException(status_code=400, detail="La retenue a déjà été libérée")
    
    await db.invoices.update_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {
            "$set": {
                "retenue_garantie_released": True,
                "retenue_garantie_released_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    logger.info(f"Retenue garantie released for invoice {invoice_id}")
    
    return {
        "message": "Retenue de garantie libérée",
        "invoice_id": invoice_id,
        "released_amount": invoice.get("retenue_garantie_amount", 0),
        "released_at": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/quotes/{quote_id}/retenues-garantie/summary")
async def get_quote_retenues_summary(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    invoices = await db.invoices.find(
        {"parent_quote_id": quote_id, "has_retenue_garantie": True, "owner_id": user["id"]},
        {"_id": 0}
    ).to_list(100)
    
    total_retained = sum(inv.get("retenue_garantie_amount", 0) for inv in invoices)
    total_released = sum(
        inv.get("retenue_garantie_amount", 0)
        for inv in invoices
        if inv.get("retenue_garantie_released")
    )
    pending_release = total_retained - total_released
    
    retentions = [
        {
            "invoice_id": inv["id"],
            "invoice_number": inv["invoice_number"],
            "amount": inv.get("retenue_garantie_amount", 0),
            "rate": inv.get("retenue_garantie_rate", 5),
            "release_date": inv.get("retenue_garantie_release_date"),
            "released": inv.get("retenue_garantie_released", False),
            "released_at": inv.get("retenue_garantie_released_at")
        }
        for inv in invoices
    ]
    
    return {
        "quote_id": quote_id,
        "quote_number": quote["quote_number"],
        "total_retained": round(total_retained, 2),
        "total_released": round(total_released, 2),
        "pending_release": round(pending_release, 2),
        "retentions": retentions
    }
	
	# ============== PROJECT FINANCIAL SUMMARY ==============

async def calculate_project_financial_summary(quote_id: str, user_id: str):
    quote = await db.quotes.find_one({"id": quote_id, "owner_id": user_id}, {"_id": 0})
    if not quote:
        return None
    
    all_invoices = await db.invoices.find(
        {"parent_quote_id": quote_id, "owner_id": user_id},
        {"_id": 0}
    ).to_list(100)
    
    acomptes = [inv for inv in all_invoices if inv.get("is_acompte")]
    situations = [inv for inv in all_invoices if inv.get("is_situation")]
    final_invoices = [inv for inv in all_invoices if inv.get("is_final_invoice") or inv.get("is_situation_final")]
    
    acomptes_total = sum(a.get("total_ttc", 0) for a in acomptes)
    acomptes_paid = sum(a.get("paid_amount", 0) for a in acomptes if a.get("payment_status") == "paye")
    
    situations_total = sum(s.get("total_ttc", 0) for s in situations)
    situations_paid = sum(s.get("paid_amount", 0) for s in situations if s.get("payment_status") == "paye")
    current_progress = situations[-1].get("situation_percentage", 0) if situations else 0
    
    retenue_invoices = [inv for inv in all_invoices if inv.get("has_retenue_garantie")]
    total_retenue = sum(inv.get("retenue_garantie_amount", 0) for inv in retenue_invoices)
    retenue_released = sum(
        inv.get("retenue_garantie_amount", 0)
        for inv in retenue_invoices
        if inv.get("retenue_garantie_released")
    )
    
    final_total = sum(f.get("total_ttc", 0) for f in final_invoices)
    final_paid = sum(f.get("paid_amount", 0) for f in final_invoices if f.get("payment_status") == "paye")
    
    total_invoiced = acomptes_total + situations_total
    total_paid = acomptes_paid + situations_paid + final_paid
    
    remaining_to_invoice = max(0, quote["total_ttc"] - total_invoiced)
    remaining_to_pay = total_invoiced - total_paid + (total_retenue - retenue_released)
    
    invoices_list = []
    for inv in sorted(all_invoices, key=lambda x: x.get("created_at", "")):
        inv_type = "Facture"
        if inv.get("is_acompte"):
            inv_type = f"Acompte n°{inv.get('acompte_number', '?')}"
        elif inv.get("is_situation"):
            inv_type = f"Situation n°{inv.get('situation_number', '?')}"
        elif inv.get("is_situation_final"):
            inv_type = "Décompte final"
        elif inv.get("is_final_invoice"):
            inv_type = "Facture de solde"
        
        invoices_list.append({
            "id": inv["id"],
            "invoice_number": inv["invoice_number"],
            "type": inv_type,
            "date": inv.get("issue_date", "")[:10],
            "total_ttc": inv.get("total_ttc", 0),
            "paid_amount": inv.get("paid_amount", 0),
            "payment_status": inv.get("payment_status", "impaye"),
            "has_retenue": inv.get("has_retenue_garantie", False),
            "retenue_amount": inv.get("retenue_garantie_amount", 0) if inv.get("has_retenue_garantie") else 0,
            "retenue_released": inv.get("retenue_garantie_released", False)
        })
    
    return {
        "quote_id": quote_id,
        "quote_number": quote["quote_number"],
        "client_name": quote["client_name"],
        "status": quote["status"],
        "project_total_ht": quote["total_ht"],
        "project_total_vat": quote["total_vat"],
        "project_total_ttc": quote["total_ttc"],
        "progress_percentage": round(current_progress, 1),
        "acomptes": {
            "count": len(acomptes),
            "total_invoiced": round(acomptes_total, 2),
            "total_paid": round(acomptes_paid, 2),
            "pending": round(acomptes_total - acomptes_paid, 2)
        },
        "situations": {
            "count": len(situations),
            "total_invoiced": round(situations_total, 2),
            "total_paid": round(situations_paid, 2),
            "pending": round(situations_total - situations_paid, 2),
            "progress_percentage": round(current_progress, 1)
        },
        "retenue_garantie": {
            "total_retained": round(total_retenue, 2),
            "total_released": round(retenue_released, 2),
            "pending_release": round(total_retenue - retenue_released, 2),
            "next_release_date": min(
                (inv.get("retenue_garantie_release_date") for inv in retenue_invoices
                 if not inv.get("retenue_garantie_released") and inv.get("retenue_garantie_release_date")),
                default=None
            )
        },
        "totals": {
            "total_invoiced": round(total_invoiced, 2),
            "total_paid": round(total_paid, 2),
            "remaining_to_invoice": round(remaining_to_invoice, 2),
            "remaining_to_pay": round(remaining_to_pay, 2),
            "percentage_paid": round((total_paid / quote["total_ttc"] * 100) if quote["total_ttc"] > 0 else 0, 1)
        },
        "invoices": invoices_list
    }

@api_router.get("/quotes/{quote_id}/financial-summary")
async def get_project_financial_summary(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    summary = await calculate_project_financial_summary(quote_id, user["id"])
    if not summary:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    return summary

@api_router.get("/public/quote/{share_token}/financial-summary")
async def get_public_project_financial_summary(share_token: str):
    if not share_token:
        raise HTTPException(status_code=400, detail="Token invalide")
    
    share_link = await db.share_links.find_one({"token": share_token})
    if not share_link:
        raise HTTPException(status_code=404, detail="Lien non trouvé")
    
    if share_link.get("expires_at"):
        if datetime.fromisoformat(share_link["expires_at"]) < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Lien expiré")
    
    summary = await calculate_project_financial_summary(share_link["document_id"], share_link["created_by"])
    if not summary:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    return summary

# ============== DASHBOARD ROUTES ==============

@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(user: dict = Depends(get_current_user)):
    try:
        paid_invoices = await db.invoices.find(
            {"payment_status": "paye", "owner_id": user["id"]},
            {"_id": 0}
        ).to_list(10000)
        total_turnover = sum(inv["total_ttc"] for inv in paid_invoices)
        
        unpaid_invoices = await db.invoices.find(
            {"payment_status": {"$in": ["impaye", "partiel"]}, "owner_id": user["id"]},
            {"_id": 0}
        ).to_list(10000)
        unpaid_count = len(unpaid_invoices)
        unpaid_amount = sum(inv["total_ttc"] - inv.get("paid_amount", 0) for inv in unpaid_invoices)
        
        pending_quotes = await db.quotes.count_documents({"status": "envoye", "owner_id": user["id"]})
        
        total_clients = await db.clients.count_documents({"owner_id": user["id"]})
        total_quotes = await db.quotes.count_documents({"owner_id": user["id"]})
        total_invoices = await db.invoices.count_documents({"owner_id": user["id"]})
        
        return DashboardStats(
            total_turnover=round(total_turnover, 2),
            unpaid_invoices_count=unpaid_count,
            unpaid_invoices_amount=round(unpaid_amount, 2),
            pending_quotes_count=pending_quotes,
            total_clients=total_clients,
            total_quotes=total_quotes,
            total_invoices=total_invoices
        )
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des statistiques")

# ============== PREDEFINED ITEMS ROUTES ==============

async def initialize_default_items():
    count = await db.predefined_items.count_documents({})
    if count == 0:
        for category, items in DEFAULT_BTP_CATEGORIES.items():
            for item in items:
                item_doc = {
                    "id": str(uuid.uuid4()),
                    "category": category,
                    "description": item["description"],
                    "unit": item["unit"],
                    "default_price": item["default_price"],
                    "default_vat_rate": item.get("default_vat_rate", 20.0)
                }
                await db.predefined_items.insert_one(item_doc)

@api_router.get("/predefined-items/categories")
async def get_categories(user: dict = Depends(get_current_user)):
    await initialize_default_items()
    items = await db.predefined_items.find({}, {"_id": 0}).to_list(1000)
    
    categories = {}
    for item in items:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(PredefinedItemResponse(**item))
    
    result = [{"name": name, "items": items} for name, items in sorted(categories.items())]
    return result

@api_router.get("/predefined-items", response_model=List[PredefinedItemResponse])
async def list_predefined_items(category: Optional[str] = None, user: dict = Depends(get_current_user)):
    await initialize_default_items()
    query = {}
    if category:
        query["category"] = category
    items = await db.predefined_items.find(query, {"_id": 0}).to_list(1000)
    return [PredefinedItemResponse(**item) for item in items]

@api_router.post("/predefined-items", response_model=PredefinedItemResponse)
async def create_predefined_item(item_data: PredefinedItemCreate, user: dict = Depends(get_current_user)):
    item_id = str(uuid.uuid4())
    item_doc = {
        "id": item_id,
        "category": item_data.category,
        "description": item_data.description,
        "unit": item_data.unit,
        "default_price": item_data.default_price,
        "default_vat_rate": item_data.default_vat_rate
    }
    await db.predefined_items.insert_one(item_doc)
    return PredefinedItemResponse(**item_doc)

@api_router.put("/predefined-items/{item_id}", response_model=PredefinedItemResponse)
async def update_predefined_item(item_id: str, item_data: PredefinedItemUpdate, user: dict = Depends(get_current_user)):
    if not validate_uuid(item_id):
        raise HTTPException(status_code=400, detail="ID article invalide")
    
    item = await db.predefined_items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    update_data = {k: v for k, v in item_data.dict().items() if v is not None}
    if update_data:
        await db.predefined_items.update_one({"id": item_id}, {"$set": update_data})
    
    updated_item = await db.predefined_items.find_one({"id": item_id}, {"_id": 0})
    return PredefinedItemResponse(**updated_item)

@api_router.delete("/predefined-items/{item_id}")
async def delete_predefined_item(item_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(item_id):
        raise HTTPException(status_code=400, detail="ID article invalide")
    
    result = await db.predefined_items.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    return {"message": "Article supprimé"}

@api_router.post("/predefined-items/reset")
async def reset_predefined_items(user: dict = Depends(get_current_user)):
    await db.predefined_items.delete_many({})
    await initialize_default_items()
    return {"message": "Articles réinitialisés"}

# ============== RENOVATION KITS ROUTES ==============

async def initialize_default_kits():
    count = await db.renovation_kits.count_documents({"is_default": True})
    if count == 0:
        for kit in DEFAULT_RENOVATION_KITS:
            kit_doc = {
                "id": str(uuid.uuid4()),
                "name": kit["name"],
                "description": kit["description"],
                "items": kit["items"],
                "is_default": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.renovation_kits.insert_one(kit_doc)

@api_router.get("/kits", response_model=List[KitResponse])
async def list_kits(user: dict = Depends(get_current_user)):
    await initialize_default_kits()
    kits = await db.renovation_kits.find({}, {"_id": 0}).sort("name", 1).to_list(1000)
    return [KitResponse(**kit) for kit in kits]

@api_router.get("/kits/{kit_id}", response_model=KitResponse)
async def get_kit(kit_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(kit_id):
        raise HTTPException(status_code=400, detail="ID kit invalide")
    
    kit = await db.renovation_kits.find_one({"id": kit_id}, {"_id": 0})
    if not kit:
        raise HTTPException(status_code=404, detail="Kit non trouvé")
    return KitResponse(**kit)

@api_router.post("/kits", response_model=KitResponse)
async def create_kit(kit_data: KitCreate, user: dict = Depends(get_current_user)):
    kit_id = str(uuid.uuid4())
    kit_doc = {
        "id": kit_id,
        "name": kit_data.name,
        "description": kit_data.description,
        "items": [item.dict() for item in kit_data.items],
        "is_default": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.renovation_kits.insert_one(kit_doc)
    return KitResponse(**kit_doc)

@api_router.put("/kits/{kit_id}", response_model=KitResponse)
async def update_kit(kit_id: str, kit_data: KitUpdate, user: dict = Depends(get_current_user)):
    if not validate_uuid(kit_id):
        raise HTTPException(status_code=400, detail="ID kit invalide")
    
    kit = await db.renovation_kits.find_one({"id": kit_id}, {"_id": 0})
    if not kit:
        raise HTTPException(status_code=404, detail="Kit non trouvé")
    
    update_data = {}
    if kit_data.name is not None:
        update_data["name"] = kit_data.name
    if kit_data.description is not None:
        update_data["description"] = kit_data.description
    if kit_data.items is not None:
        update_data["items"] = [item.dict() for item in kit_data.items]
    
    if update_data:
        await db.renovation_kits.update_one({"id": kit_id}, {"$set": update_data})
    
    updated_kit = await db.renovation_kits.find_one({"id": kit_id}, {"_id": 0})
    return KitResponse(**updated_kit)

@api_router.delete("/kits/{kit_id}")
async def delete_kit(kit_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(kit_id):
        raise HTTPException(status_code=400, detail="ID kit invalide")
    
    result = await db.renovation_kits.delete_one({"id": kit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kit non trouvé")
    return {"message": "Kit supprimé"}

@api_router.post("/kits/from-quote/{quote_id}")
async def create_kit_from_quote(quote_id: str, kit_name: str, kit_description: str = "", user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    kit_items = []
    for item in quote["items"]:
        kit_items.append({
            "description": item["description"],
            "unit": item.get("unit", "unité"),
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "vat_rate": item["vat_rate"]
        })
    
    kit_id = str(uuid.uuid4())
    kit_doc = {
        "id": kit_id,
        "name": kit_name,
        "description": kit_description,
        "items": kit_items,
        "is_default": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.renovation_kits.insert_one(kit_doc)
    return KitResponse(**kit_doc)

@api_router.post("/kits/reset")
async def reset_kits(user: dict = Depends(get_current_user)):
    await db.renovation_kits.delete_many({})
    await initialize_default_kits()
    return {"message": "Kits réinitialisés"}

# ============== COMPANY SETTINGS (ADMIN ONLY) ==============

@api_router.get("/settings", response_model=CompanySettings)
async def get_settings(user: dict = Depends(get_current_user)):
    """Get company settings - All authenticated users can view"""
    settings = await db.settings.find_one({"type": "company"}, {"_id": 0})
    if not settings:
        return CompanySettings()
    return CompanySettings(**{k: v for k, v in settings.items() if k != "type"})

@api_router.put("/settings", response_model=CompanySettings)
async def update_settings(settings_data: CompanySettings, admin: dict = Depends(require_admin)):
    """Update company settings - Admin only"""
    settings_doc = settings_data.dict()
    settings_doc["type"] = "company"
    
    await db.settings.update_one(
        {"type": "company"},
        {"$set": settings_doc},
        upsert=True
    )
    
    logger.info(f"Settings updated by admin {admin['id']}")
    
    return settings_data

@api_router.post("/settings/logo")
async def upload_logo(file: UploadFile = File(...), admin: dict = Depends(require_admin)):
    """Upload company logo - Admin only"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image")
    
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="L'image ne doit pas dépasser 5MB")
    
    logo_base64 = base64.b64encode(contents).decode('utf-8')
    logo_data = f"data:{file.content_type};base64,{logo_base64}"
    
    await db.settings.update_one(
        {"type": "company"},
        {"$set": {"logo_base64": logo_data}},
        upsert=True
    )
    
    logger.info(f"Logo updated by admin {admin['id']}")
    
    return {"message": "Logo téléchargé avec succès", "logo": logo_data}

# ============== PDF GENERATION ==============

# Document Theme Colors Mapping
DOCUMENT_THEME_COLORS = {
    "blue": {
        "primary": "#2563EB",      # Blue-600
        "primary_dark": "#1D4ED8", # Blue-700
        "header_bg": "#2563EB",
        "accent": "#3B82F6",       # Blue-500
        "text_dark": "#0F172A"
    },
    "light_blue": {
        "primary": "#0EA5E9",      # Sky-500
        "primary_dark": "#0284C7", # Sky-600
        "header_bg": "#0EA5E9",
        "accent": "#38BDF8",       # Sky-400
        "text_dark": "#0F172A"
    },
    "green": {
        "primary": "#16A34A",      # Green-600
        "primary_dark": "#15803D", # Green-700
        "header_bg": "#16A34A",
        "accent": "#22C55E",       # Green-500
        "text_dark": "#0F172A"
    },
    "orange": {
        "primary": "#EA580C",      # Orange-600
        "primary_dark": "#C2410C", # Orange-700
        "header_bg": "#EA580C",
        "accent": "#F97316",       # Orange-500
        "text_dark": "#0F172A"
    },
    "burgundy": {
        "primary": "#9F1239",      # Rose-800
        "primary_dark": "#881337", # Rose-900
        "header_bg": "#9F1239",
        "accent": "#BE123C",       # Rose-700
        "text_dark": "#0F172A"
    },
    "dark_grey": {
        "primary": "#475569",      # Slate-600
        "primary_dark": "#334155", # Slate-700
        "header_bg": "#475569",
        "accent": "#64748B",       # Slate-500
        "text_dark": "#0F172A"
    }
}

def get_theme_colors(theme_color: str) -> dict:
    """Get theme color palette, defaults to blue if invalid"""
    return DOCUMENT_THEME_COLORS.get(theme_color, DOCUMENT_THEME_COLORS["blue"])

def create_pdf(doc_type: str, doc_data: dict, company: dict, client: dict):
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15*mm,
        bottomMargin=25*mm,
        leftMargin=15*mm,
        rightMargin=15*mm
    )
    
    styles = getSampleStyleSheet()
    company_name = company.get("company_name", "Votre Entreprise BTP")
    
    # Get theme colors
    theme_color = company.get("document_theme_color", "blue")
    theme = get_theme_colors(theme_color)
    
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
        canvas.setLineWidth(0.5)
        canvas.line(15*mm, 18*mm, A4[0] - 15*mm, 18*mm)
        
        footer_parts = [company_name]
        if company.get("siret"):
            footer_parts.append(f"SIRET: {company['siret']}")
        
        footer_text = " | ".join(footer_parts)
        
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#64748B'))
        
        text_width = canvas.stringWidth(footer_text, 'Helvetica', 7)
        x_position = (A4[0] - text_width) / 2
        canvas.drawString(x_position, 12*mm, footer_text)
        
        canvas.restoreState()
    
    company_name_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Heading1'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(theme['text_dark']),
        alignment=TA_CENTER,
        spaceAfter=2
    )
    company_info_style = ParagraphStyle(
        'CompanyInfo',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#475569'),
        alignment=TA_CENTER,
        leading=11
    )
    
    elements = []
    
    if company.get("logo_base64"):
        try:
            logo_data = company["logo_base64"]
            if ',' in logo_data:
                logo_data = logo_data.split(',')[1]
            logo_bytes = base64.b64decode(logo_data)
            logo_buffer = BytesIO(logo_bytes)
            logo_image = Image(logo_buffer)
            logo_image.drawWidth = 40 * mm
            logo_image.drawHeight = 20 * mm
            logo_table = Table([[logo_image]], colWidths=[180*mm])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(logo_table)
            elements.append(Spacer(1, 5*mm))
        except Exception as e:
            logger.warning(f"Failed to load logo: {str(e)}")
    
    elements.append(Paragraph(company_name, company_name_style))
    if company.get("address"):
        elements.append(Paragraph(company["address"], company_info_style))
    
    elements.append(Spacer(1, 6*mm))
    
    if doc_type == "quote":
        title = f"DEVIS N° {doc_data['quote_number']}"
    else:
        if doc_data.get('is_situation'):
            title = f"SITUATION N° {doc_data['situation_number']}"
        elif doc_data.get('is_acompte'):
            title = f"ACOMPTE N° {doc_data['acompte_number']}"
        else:
            title = f"FACTURE N° {doc_data['invoice_number']}"
    
    elements.append(Paragraph(title, ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#0F172A'),
        alignment=TA_CENTER
    )))
    
    elements.append(Spacer(1, 6*mm))
    
    info_data = [
        ["Date:", doc_data['issue_date'][:10]],
        ["Client:", client.get('name', '')]
    ]
    
    if doc_type == "quote":
        info_data.insert(1, ["Valable jusqu'au:", doc_data['validity_date'][:10]])
    else:
        info_data.insert(1, ["Échéance:", doc_data.get('payment_due_date', '')[:10]])
    
    info_table = Table(info_data, colWidths=[40*mm, 130*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))
    
    table_data = [[
        Paragraph("<b>Description</b>", styles['Normal']),
        Paragraph("<b>Qté</b>", styles['Normal']),
        Paragraph("<b>Prix unit.</b>", styles['Normal']),
        Paragraph("<b>Total</b>", styles['Normal'])
    ]]
    
    for item in doc_data['items']:
        line_total = item['quantity'] * item['unit_price']
        table_data.append([
            Paragraph(item['description'], styles['Normal']),
            str(item['quantity']),
            f"{item['unit_price']:.2f} €",
            f"{line_total:.2f} €"
        ])
    
    items_table = Table(table_data, colWidths=[80*mm, 20*mm, 35*mm, 35*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(theme['header_bg'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 6*mm))
    
    totals_data = [
        ["Total HT:", f"{doc_data['total_ht']:.2f} €"],
    ]
    
    if not company.get("is_auto_entrepreneur"):
        totals_data.append(["Total TVA:", f"{doc_data['total_vat']:.2f} €"])
    
    totals_data.append(["Total TTC:", f"{doc_data['total_ttc']:.2f} €"])
    
    totals_table = Table(totals_data, colWidths=[120*mm, 50*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor(theme['header_bg'])),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
    ]))
    elements.append(totals_table)
    
    if doc_data.get('notes'):
        elements.append(Spacer(1, 6*mm))
        elements.append(Paragraph("<b>Notes:</b>", styles['Normal']))
        elements.append(Paragraph(doc_data['notes'], styles['Normal']))
    
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer

def generate_financial_summary_pdf(summary: dict, company: dict):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0F172A'), alignment=TA_CENTER, spaceAfter=10)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#0F172A'), spaceBefore=15, spaceAfter=8)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#334155'))
    
    elements.append(Paragraph("RÉCAPITULATIF FINANCIER", title_style))
    elements.append(Paragraph(f"Projet {summary['quote_number']}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    if company.get("company_name"):
        elements.append(Paragraph(f"<b>{company['company_name']}</b>", normal_style))
    
    elements.append(Spacer(1, 8*mm))
    
    info_data = [
        ["Client:", summary['client_name']],
        ["Référence devis:", summary['quote_number']],
        ["Date:", datetime.now().strftime("%d/%m/%Y")],
    ]
    
    info_table = Table(info_data, colWidths=[50*mm, 120*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10*mm))
    
    elements.append(Paragraph("MONTANT TOTAL DU PROJET", section_style))
    
    total_data = [
        ["Total HT:", f"{summary['project_total_ht']:,.2f} €".replace(",", " ")],
        ["Total TVA:", f"{summary['project_total_vat']:,.2f} €".replace(",", " ")],
        ["TOTAL TTC:", f"{summary['project_total_ttc']:,.2f} €".replace(",", " ")],
    ]
    
    total_table = Table(total_data, colWidths=[50*mm, 50*mm])
    total_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('TEXTCOLOR', (1, -1), (1, -1), colors.HexColor('#059669')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 8*mm))
    
    elements.append(Paragraph("SYNTHÈSE DES PAIEMENTS", section_style))
    
    totals = summary['totals']
    synth_data = [
        ["Montant facturé:", f"{totals['total_invoiced']:,.2f} €".replace(",", " ")],
        ["Montant encaissé:", f"{totals['total_paid']:,.2f} €".replace(",", " ")],
        ["Reste à facturer:", f"{totals['remaining_to_invoice']:,.2f} €".replace(",", " ")],
        ["RESTE À PAYER:", f"{totals['remaining_to_pay']:,.2f} €".replace(",", " ")],
    ]
    
    synth_table = Table(synth_data, colWidths=[60*mm, 50*mm])
    synth_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    elements.append(synth_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

@api_router.get("/quotes/{quote_id}/pdf")
async def generate_quote_pdf(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    client = await db.clients.find_one(
        {"id": quote["client_id"]},
        {"_id": 0}
    ) or {"name": quote["client_name"]}
    
    company = await get_company_settings()
    
    pdf_buffer = create_pdf("quote", quote, company, client)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=devis_{quote['quote_number']}.pdf"}
    )

@api_router.get("/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="ID facture invalide")
    
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    client = await db.clients.find_one(
        {"id": invoice["client_id"]},
        {"_id": 0}
    ) or {"name": invoice["client_name"]}
    
    company = await get_company_settings()
    
    pdf_buffer = create_pdf("invoice", invoice, company, client)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=facture_{invoice['invoice_number']}.pdf"}
    )

@api_router.get("/quotes/{quote_id}/financial-summary/pdf")
async def download_financial_summary_pdf(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    summary = await calculate_project_financial_summary(quote_id, user["id"])
    if not summary:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    company = await get_company_settings()
    pdf_buffer = generate_financial_summary_pdf(summary, company)
    
    filename = f"Recapitulatif_financier_{summary['quote_number']}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ============== SHARE LINKS ==============

@api_router.post("/quotes/{quote_id}/share")
async def create_quote_share_link(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    share_token = generate_share_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"share_token": share_token, "share_expires_at": expires_at}}
    )
    
    await db.share_links.insert_one({
        "token": share_token,
        "document_type": "quote",
        "document_id": quote_id,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "access_count": 0,
        "last_accessed": None
    })
    
    share_url = f"{FRONTEND_URL or ''}/client/devis/{share_token}"
    
    return {
        "share_token": share_token,
        "expires_at": expires_at,
        "share_url": share_url
    }

@api_router.post("/invoices/{invoice_id}/share")
async def create_invoice_share_link(invoice_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="ID facture invalide")
    
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    share_token = generate_share_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"share_token": share_token, "share_expires_at": expires_at}}
    )
    
    await db.share_links.insert_one({
        "token": share_token,
        "document_type": "invoice",
        "document_id": invoice_id,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "access_count": 0,
        "last_accessed": None
    })
    
    share_url = f"{FRONTEND_URL or ''}/client/facture/{share_token}"
    
    return {
        "share_token": share_token,
        "expires_at": expires_at,
        "share_url": share_url
    }

@api_router.delete("/quotes/{quote_id}/share")
async def revoke_quote_share_link(quote_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    result = await db.quotes.update_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"$unset": {"share_token": "", "share_expires_at": ""}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    await db.share_links.delete_many({
        "document_id": quote_id,
        "document_type": "quote"
    })
    
    return {"message": "Lien de partage révoqué"}

@api_router.delete("/invoices/{invoice_id}/share")
async def revoke_invoice_share_link(invoice_id: str, user: dict = Depends(get_current_user)):
    if not validate_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="ID facture invalide")
    
    result = await db.invoices.update_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"$unset": {"share_token": "", "share_expires_at": ""}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    await db.share_links.delete_many({
        "document_id": invoice_id,
        "document_type": "invoice"
    })
    
    return {"message": "Lien de partage révoqué"}

@api_router.get("/public/quote/{share_token}")
async def get_public_quote(share_token: str):
    if not share_token or len(share_token) != 43:
        raise HTTPException(status_code=400, detail="Token invalide")
    
    share_link = await db.share_links.find_one({
        "token": share_token,
        "document_type": "quote"
    })
    
    if not share_link:
        raise HTTPException(status_code=404, detail="Lien non trouvé")
    
    if share_link.get("expires_at"):
        if datetime.fromisoformat(share_link["expires_at"]) < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Lien expiré")
    
    quote = await db.quotes.find_one(
        {"id": share_link["document_id"]},
        {"_id": 0, "owner_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    await db.share_links.update_one(
        {"token": share_token},
        {
            "$inc": {"access_count": 1},
            "$set": {"last_accessed": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    company = await get_company_settings()
    
    return {
        **quote,
        "company": {
            "name": company.get("company_name"),
            "address": company.get("address"),
            "siret": company.get("siret")
        }
    }

@api_router.get("/public/invoice/{share_token}")
async def get_public_invoice(share_token: str):
    if not share_token or len(share_token) != 43:
        raise HTTPException(status_code=400, detail="Token invalide")
    
    share_link = await db.share_links.find_one({
        "token": share_token,
        "document_type": "invoice"
    })
    
    if not share_link:
        raise HTTPException(status_code=404, detail="Lien non trouvé")
    
    if share_link.get("expires_at"):
        if datetime.fromisoformat(share_link["expires_at"]) < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Lien expiré")
    
    invoice = await db.invoices.find_one(
        {"id": share_link["document_id"]},
        {"_id": 0, "owner_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    await db.share_links.update_one(
        {"token": share_token},
        {
            "$inc": {"access_count": 1},
            "$set": {"last_accessed": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    company = await get_company_settings()
    
    return {
        **invoice,
        "company": {
            "name": company.get("company_name"),
            "address": company.get("address"),
            "siret": company.get("siret")
        }
    }

@api_router.get("/public/quote/{share_token}/pdf")
async def get_public_quote_pdf(share_token: str):
    if not share_token or len(share_token) != 43:
        raise HTTPException(status_code=400, detail="Token invalide")
    
    share_link = await db.share_links.find_one({
        "token": share_token,
        "document_type": "quote"
    })
    
    if not share_link:
        raise HTTPException(status_code=404, detail="Lien non trouvé")
    
    if share_link.get("expires_at"):
        if datetime.fromisoformat(share_link["expires_at"]) < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Lien expiré")
    
    quote = await db.quotes.find_one(
        {"id": share_link["document_id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    client = await db.clients.find_one(
        {"id": quote["client_id"]},
        {"_id": 0}
    ) or {"name": quote["client_name"]}
    
    company = await get_company_settings()
    pdf_buffer = create_pdf("quote", quote, company, client)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=devis_{quote['quote_number']}.pdf"}
    )

@api_router.get("/public/invoice/{share_token}/pdf")
async def get_public_invoice_pdf(share_token: str):
    if not share_token or len(share_token) != 43:
        raise HTTPException(status_code=400, detail="Token invalide")
    
    share_link = await db.share_links.find_one({
        "token": share_token,
        "document_type": "invoice"
    })
    
    if not share_link:
        raise HTTPException(status_code=404, detail="Lien non trouvé")
    
    if share_link.get("expires_at"):
        if datetime.fromisoformat(share_link["expires_at"]) < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Lien expiré")
    
    invoice = await db.invoices.find_one(
        {"id": share_link["document_id"]},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    client = await db.clients.find_one(
        {"id": invoice["client_id"]},
        {"_id": 0}
    ) or {"name": invoice["client_name"]}
    
    company = await get_company_settings()
    pdf_buffer = create_pdf("invoice", invoice, company, client)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=facture_{invoice['invoice_number']}.pdf"}
    )

# ============== EMAIL SENDING ==============

def generate_email_html(doc_type: str, doc_data: dict, company: dict, client: dict, share_url: str, custom_message: str = ""):
    doc_label = "Devis" if doc_type == "quote" else "Facture"
    doc_number = doc_data.get("quote_number") if doc_type == "quote" else doc_data.get("invoice_number")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f97316; padding: 20px; text-align: center;">
            <h1 style="color: white;">{company.get('company_name', '')}</h1>
        </div>
        <div style="padding: 30px;">
            <p>Bonjour {client.get('name', '')},</p>
            <p>Veuillez trouver ci-joint votre {doc_label.lower()} n° {doc_number}.</p>
            {f'<p>{custom_message}</p>' if custom_message else ''}
            <div style="text-align: center; margin: 30px 0;">
                <a href="{share_url}" style="background-color: #f97316; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">
                    Consulter le {doc_label.lower()}
                </a>
            </div>
            <p>Cordialement,<br><strong>{company.get('company_name', '')}</strong></p>
        </div>
    </body>
    </html>
    """

@api_router.post("/quotes/{quote_id}/send-email")
async def send_quote_email(quote_id: str, request: SendDocumentEmailRequest, user: dict = Depends(get_current_user)):
    if not RESEND_CONFIGURED:
        raise HTTPException(status_code=503, detail="Service email non configuré")
    
    if not FRONTEND_URL:
        raise HTTPException(status_code=500, detail="FRONTEND_URL non configuré")
    
    if not validate_uuid(quote_id):
        raise HTTPException(status_code=400, detail="ID devis invalide")
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    client = await db.clients.find_one(
        {"id": quote["client_id"]},
        {"_id": 0}
    ) or {"name": quote["client_name"]}
    
    company = await get_company_settings()
    
    share_token = quote.get("share_token")
    if not share_token:
        share_token = generate_share_token()
        await db.quotes.update_one(
            {"id": quote_id},
            {"$set": {"share_token": share_token}}
        )
    
    share_url = f"{FRONTEND_URL}/client/devis/{share_token}"
    
    email_html = generate_email_html("quote", quote, company, client, share_url, request.custom_message)
    
    pdf_buffer = create_pdf("quote", quote, company, client)
    pdf_data = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [request.recipient_email],
            "subject": f"Devis n° {quote['quote_number']} - {company.get('company_name', '')}",
            "html": email_html,
            "attachments": [
                {
                    "filename": f"devis_{quote['quote_number']}.pdf",
                    "content": pdf_data,
                }
            ]
        }
        
        email_result = await asyncio.to_thread(resend.Emails.send, params)
        
        await db.quotes.update_one(
            {"id": quote_id},
            {"$set": {"status": "envoye"}}
        )
        
        logger.info(f"Quote email sent: {quote['quote_number']} to {request.recipient_email}")
        
        return {
            "status": "success",
            "message": f"Devis envoyé à {request.recipient_email}",
            "email_id": email_result.get("id")
        }
        
    except Exception as e:
        logger.error(f"Email send error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi: {str(e)}")

@api_router.post("/invoices/{invoice_id}/send-email")
async def send_invoice_email(invoice_id: str, request: SendDocumentEmailRequest, user: dict = Depends(get_current_user)):
    if not RESEND_CONFIGURED:
        raise HTTPException(status_code=503, detail="Service email non configuré")
    
    if not FRONTEND_URL:
        raise HTTPException(status_code=500, detail="FRONTEND_URL non configuré")
    
    if not validate_uuid(invoice_id):
        raise HTTPException(status_code=400, detail="ID facture invalide")
    
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "owner_id": user["id"]},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    client = await db.clients.find_one(
        {"id": invoice["client_id"]},
        {"_id": 0}
    ) or {"name": invoice["client_name"]}
    
    company = await get_company_settings()
    
    share_token = invoice.get("share_token")
    if not share_token:
        share_token = generate_share_token()
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"share_token": share_token}}
        )
    
    share_url = f"{FRONTEND_URL}/client/facture/{share_token}"
    
    email_html = generate_email_html("invoice", invoice, company, client, share_url, request.custom_message)
    
    pdf_buffer = create_pdf("invoice", invoice, company, client)
    pdf_data = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [request.recipient_email],
            "subject": f"Facture n° {invoice['invoice_number']} - {company.get('company_name', '')}",
            "html": email_html,
            "attachments": [
                {
                    "filename": f"facture_{invoice['invoice_number']}.pdf",
                    "content": pdf_data,
                }
            ]
        }
        
        email_result = await asyncio.to_thread(resend.Emails.send, params)
        
        logger.info(f"Invoice email sent: {invoice['invoice_number']} to {request.recipient_email}")
        
        return {
            "status": "success",
            "message": f"Facture envoyée à {request.recipient_email}",
            "email_id": email_result.get("id")
        }
        
    except Exception as e:
        logger.error(f"Email send error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi: {str(e)}")

@api_router.get("/email/status")
async def get_email_status(user: dict = Depends(get_current_user)):
    return {
        "configured": RESEND_CONFIGURED,
        "sender": SENDER_EMAIL if RESEND_CONFIGURED else None,
        "frontend_url": FRONTEND_URL
    }

# ============== HEALTH CHECK ==============

@api_router.get("/health")
async def health_check():
    try:
        await client.admin.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "environment": ENVIRONMENT
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# ============== MAIN APP SETUP ==============

app.include_router(api_router)

cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    max_age=3600,
)

@app.on_event("startup")
async def startup_db_client():
    try:
        await client.admin.command('ping')
        logger.info("Connected to MongoDB")
        
        # Create indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        await db.users.create_index("role")  # Index for role-based queries
        await db.users.create_index("is_verified")  # Index for verification status
        await db.users.create_index("is_active")  # Index for active users
        await db.users.create_index([("plan", 1), ("trial_end", 1)])  # Index for trial management
        await db.clients.create_index([("owner_id", 1), ("id", 1)], unique=True)
        await db.quotes.create_index([("owner_id", 1), ("id", 1)], unique=True)
        await db.invoices.create_index([("owner_id", 1), ("id", 1)], unique=True)
        await db.share_links.create_index("token", unique=True)
        await db.share_links.create_index("expires_at", expireAfterSeconds=0)
        
        # Initialize new modular services (OTP indexes, email verification TTL)
        await init_app_services(db)
        
        logger.info("Database indexes created")
        
        # Initialize super admin account
        await init_super_admin()
        
        # Initialize default data
        await initialize_default_items()
        await initialize_default_kits()
        
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Database connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)