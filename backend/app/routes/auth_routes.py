"""
Authentication Routes for BTP Facture
Clean, secure auth endpoints with OTP verification and rate limiting
"""

import logging
from datetime import datetime, timezone
from typing import Optional
import uuid
import bcrypt

from fastapi import APIRouter, HTTPException, Depends, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.user_model import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserDetailResponse,
    create_user_document,
    activate_user_trial,
    ROLE_USER,
)
from ..models.verification_model import (
    OTPVerify,
    OTPResendRequest,
    OTPVerifyResponse,
    ResendOTPResponse,
)
from ..services.email_service import get_email_service, EmailService
from ..services.otp_service import get_otp_service, OTPService
from ..services.rate_limit_service import (
    rate_limit_dependency,
    get_rate_limiter,
    get_client_ip,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Database dependency (will be set by main app)
_db: Optional[AsyncIOMotorDatabase] = None


def set_database(db: AsyncIOMotorDatabase):
    """Set database instance for routes"""
    global _db
    _db = db


def get_db() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if _db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )
    return _db


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# ============== REGISTRATION ==============

class RegistrationResponse:
    """Response model for registration"""
    def __init__(self, message: str, user_id: str, email: str, requires_verification: bool = True):
        self.message = message
        self.user_id = user_id
        self.email = email
        self.requires_verification = requires_verification


@router.post("/register")
async def register(
    request: Request,
    user_data: UserCreate,
    _: None = Depends(rate_limit_dependency("/api/auth/register"))
):
    """
    Register a new user.
    
    Flow:
    1. Validate user data
    2. Check email uniqueness
    3. Create user with is_verified=False, trial_start=None, plan="trial_pending"
    4. Generate and send OTP via email
    5. User must verify OTP to activate trial
    
    Rate limited: 5 requests per minute per IP
    """
    db = get_db()
    email_service = get_email_service()
    otp_service = get_otp_service(db)
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cet email"
        )
    
    # Create user document
    user_id = str(uuid.uuid4())
    password_hash = hash_password(user_data.password)
    
    user_doc = create_user_document(
        user_id=user_id,
        email=user_data.email,
        password_hash=password_hash,
        name=user_data.name,
        phone=user_data.phone,
        company_name=user_data.company_name,
        address=user_data.address,
        role=ROLE_USER,
    )
    
    # Insert user
    await db.users.insert_one(user_doc)
    
    # Generate and send OTP
    try:
        otp_code = await otp_service.create_otp(user_id, user_data.email)
        email_service.send_otp_email(user_data.email, otp_code)
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        # Don't fail registration if email fails, user can resend
    
    logger.info(f"User registered: {user_data.email} (pending verification)")
    
    return {
        "message": "Inscription réussie. Vérifiez votre email pour activer votre compte.",
        "user_id": user_id,
        "email": user_data.email,
        "requires_verification": True
    }


# ============== EMAIL VERIFICATION ==============

@router.post("/verify-otp", response_model=OTPVerifyResponse)
async def verify_otp(
    request: Request,
    data: OTPVerify,
    _: None = Depends(rate_limit_dependency("/api/auth/verify-otp"))
):
    """
    Verify OTP code and activate user account.
    
    On success:
    - Sets is_verified=True, email_verified=True
    - Sets trial_start=now, trial_end=now+14days
    - Sets plan="trial_active"
    - Returns JWT tokens
    
    Rate limited: 10 requests per minute per IP
    """
    db = get_db()
    otp_service = get_otp_service(db)
    email_service = get_email_service()
    
    # Find user by email
    user = await db.users.find_one({"email": data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Check if already verified
    if user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compte déjà vérifié"
        )
    
    # Verify OTP
    result = await otp_service.verify_otp(user["id"], data.email, data.otp_code)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    # Activate trial
    trial_updates = activate_user_trial(user)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": trial_updates}
    )
    
    # Clean up OTP document
    await otp_service.delete_otp(user["id"], data.email)
    
    # Generate JWT tokens
    from ..services.jwt_service import create_access_token, create_refresh_token
    
    access_token = create_access_token(user["id"], user.get("role", ROLE_USER))
    refresh_token = create_refresh_token(user["id"])
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Send welcome email
    try:
        email_service.send_welcome_email(data.email, user["name"])
    except Exception as e:
        logger.warning(f"Failed to send welcome email: {e}")
    
    logger.info(f"User verified and trial activated: {data.email}")
    
    return OTPVerifyResponse(
        success=True,
        message="Compte vérifié avec succès. Votre essai de 14 jours commence maintenant !",
        user_id=user["id"],
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ============== RESEND OTP ==============

@router.post("/resend-otp", response_model=ResendOTPResponse)
async def resend_otp(
    request: Request,
    data: OTPResendRequest,
    _: None = Depends(rate_limit_dependency("/api/auth/resend-otp"))
):
    """
    Resend OTP code with rate limiting.
    
    Rules:
    - Minimum 60 seconds between resends
    - Maximum 5 resends per hour
    - Deletes previous OTP before generating new one
    
    Rate limited: 3 requests per minute per IP
    """
    db = get_db()
    otp_service = get_otp_service(db)
    email_service = get_email_service()
    
    # Find user by email
    user = await db.users.find_one({"email": data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Check if already verified
    if user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compte déjà vérifié"
        )
    
    # Check resend eligibility (will raise 429 if not allowed)
    otp_code = await otp_service.resend_otp(user["id"], data.email)
    
    # Send OTP email
    try:
        email_service.send_otp_email(data.email, otp_code)
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Erreur d'envoi email. Réessayez plus tard."
        )
    
    # Get current resend status
    can_resend = await otp_service.can_resend_otp(user["id"], data.email)
    
    logger.info(f"OTP resent to: {data.email}")
    
    return ResendOTPResponse(
        success=True,
        message="Code de vérification renvoyé",
        resend_count=5 - can_resend.get("wait_seconds", 0) // 60,  # Approximation
        can_resend_after=60  # 60 seconds cooldown
    )


# ============== LOGIN ==============

@router.post("/login")
async def login(
    request: Request,
    user_data: UserLogin,
    _: None = Depends(rate_limit_dependency("/api/auth/login"))
):
    """
    Login user and return JWT tokens.
    
    Checks:
    - Email exists
    - Password correct
    - Account verified (is_verified=True)
    - Account active (is_active=True)
    
    Rate limited: 10 requests per minute per IP
    """
    db = get_db()
    
    # Find user
    user = await db.users.find_one({"email": user_data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Check if verified
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Veuillez vérifier votre email avant de vous connecter"
        )
    
    # Check if active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé. Contactez l'administrateur."
        )
    
    # Generate tokens
    from ..services.jwt_service import create_access_token, create_refresh_token
    
    access_token = create_access_token(user["id"], user.get("role", ROLE_USER))
    refresh_token = create_refresh_token(user["id"])
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    logger.info(f"User logged in: {user_data.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user.get("role", ROLE_USER),
            "phone": user.get("phone"),
            "email_verified": user.get("email_verified", False),
            "is_verified": user.get("is_verified", False),
            "plan": user.get("plan"),
        }
    }
