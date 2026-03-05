"""
Authentication Routes
Registration, login, email verification, password reset
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
import logging

from app.core.database import get_db
from app.core.security import (
    create_access_token, create_refresh_token, decode_token,
    generate_uuid, generate_short_token, ROLE_USER
)
from app.services.user_service import get_user_service
from app.schemas.schemas import (
    LoginRequest, RegisterRequest, TokenResponse, UserResponse,
    PasswordResetRequest, PasswordResetConfirm
)
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    Creates account with email_verified=False and trial_pending status.
    """
    user_service = get_user_service(db)
    
    # Check if email exists
    existing = await user_service.get_user_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé"
        )
    
    # Create user
    user = await user_service.create_user(request)
    
    # TODO: Generate and send OTP for email verification
    otp_code = generate_short_token(6)
    logger.info(f"[OTP] Registration code for {request.email}: {otp_code}")
    
    # Store OTP (would normally go to OTP table)
    # For now, log it for testing
    
    return {
        "message": "Compte créé. Vérifiez votre email pour le code de validation.",
        "email": request.email,
        "user_id": user.id,
        "requires_verification": True
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    Returns JWT tokens on success.
    """
    user_service = get_user_service(db)
    
    # Get user
    user = await user_service.get_user_by_email(request.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Check if account is locked
    if await user_service.is_account_locked(user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Compte temporairement bloqué. Réessayez plus tard."
        )
    
    # Authenticate
    authenticated_user = await user_service.authenticate_user(request.email, request.password)
    
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Check if email is verified (except for super admin)
    if not authenticated_user.email_verified and authenticated_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email non vérifié. Veuillez vérifier votre boîte mail."
        )
    
    # Check if account is active
    if not authenticated_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )
    
    # Update last login
    await user_service.update_last_login(authenticated_user.id)
    
    # Generate tokens
    token_data = {"sub": authenticated_user.id, "role": authenticated_user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=authenticated_user.id,
            email=authenticated_user.email,
            name=authenticated_user.name,
            phone=authenticated_user.phone,
            role=authenticated_user.role,
            is_active=authenticated_user.is_active,
            email_verified=authenticated_user.email_verified,
            subscription_plan=authenticated_user.subscription_plan,
            created_at=authenticated_user.created_at,
            last_login=authenticated_user.last_login
        )
    )


@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(
    email: str,
    otp_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email with OTP code.
    Activates account and starts trial period.
    """
    user_service = get_user_service(db)
    
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # TODO: Verify OTP from database
    # For now, accept any 6-digit code in development
    
    # Verify email and activate trial
    await user_service.verify_user_email(user.id)
    
    # Generate tokens
    token_data = {"sub": user.id, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            phone=user.phone,
            role=user.role,
            is_active=True,
            email_verified=True,
            subscription_plan="trial_active",
            created_at=user.created_at,
            last_login=datetime.now(timezone.utc)
        )
    )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    payload = decode_token(refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de rafraîchissement invalide"
        )
    
    user_service = get_user_service(db)
    user = await user_service.get_user_by_id(payload.get("sub"))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé ou désactivé"
        )
    
    token_data = {"sub": user.id, "role": user.role}
    new_access_token = create_access_token(token_data)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset.
    Sends reset code to email.
    """
    user_service = get_user_service(db)
    user = await user_service.get_user_by_email(request.email)
    
    # Don't reveal if user exists
    if user:
        reset_code = generate_short_token(6)
        logger.info(f"[OTP] Password reset code for {request.email}: {reset_code}")
        # TODO: Store OTP and send email
    
    return {
        "message": "Si cet email existe, un code de réinitialisation a été envoyé."
    }


@router.post("/reset-password")
async def reset_password(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password with token.
    """
    # TODO: Verify reset token from database
    
    # For now, decode token to get user ID
    payload = decode_token(request.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalide ou expiré"
        )
    
    user_service = get_user_service(db)
    user_id = payload.get("sub")
    
    success = await user_service.update_password(user_id, request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Échec de la réinitialisation"
        )
    
    return {"message": "Mot de passe réinitialisé avec succès"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user information.
    """
    user_service = get_user_service(db)
    user = await user_service.get_user_by_id(current_user["id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        email_verified=user.email_verified,
        subscription_plan=user.subscription_plan,
        created_at=user.created_at,
        last_login=user.last_login
    )
