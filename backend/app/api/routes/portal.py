"""
Client Portal Routes
Public endpoints for clients to access their quotes and invoices via secure token
No authentication required - access via token in URL
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.core.database import get_db
from app.services.client_portal_service import get_client_portal_service
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portal", tags=["Client Portal"])


# ============== SCHEMAS ==============

class SignatureRequest(BaseModel):
    signer_name: str = Field(..., min_length=2, max_length=200)
    signer_email: str = Field(..., min_length=5)
    signer_title: Optional[str] = Field(None, max_length=100)
    signature_data: str = Field(..., description="Base64 encoded signature image or SVG")


# ============== PUBLIC ROUTES (No auth required) ==============

@router.get("/{token}")
async def get_portal_data(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all portal data for a client using their access token.
    This is a PUBLIC endpoint - no authentication required.
    
    Returns:
        - Client info
        - List of quotes (with signature status)
        - List of invoices (with payment status)
        - Pending signatures
        - Unpaid invoices
    """
    service = get_client_portal_service(db)
    data = await service.get_client_portal_data(token)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lien invalide ou expiré"
        )
    
    return data


@router.get("/{token}/quotes/{quote_id}")
async def get_quote_details(
    token: str,
    quote_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed quote information for viewing/signing.
    PUBLIC endpoint.
    """
    service = get_client_portal_service(db)
    quote = await service.get_quote_for_signature(token, quote_id)
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devis non trouvé ou accès non autorisé"
        )
    
    return quote


@router.post("/{token}/quotes/{quote_id}/sign")
async def sign_quote(
    token: str,
    quote_id: str,
    signature: SignatureRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign a quote electronically from the client portal.
    PUBLIC endpoint.
    
    The signature_data should be a base64 encoded image of the signature
    or an SVG path data.
    """
    service = get_client_portal_service(db)
    
    # Get client IP and user agent for audit
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    result = await service.sign_quote_from_portal(
        token=token,
        quote_id=quote_id,
        signer_name=signature.signer_name,
        signer_email=signature.signer_email,
        signer_title=signature.signer_title,
        signature_data=signature.signature_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devis non trouvé ou accès non autorisé"
        )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.get("/{token}/invoices/{invoice_id}")
async def get_invoice_details(
    token: str,
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed invoice information for viewing/payment.
    PUBLIC endpoint.
    """
    service = get_client_portal_service(db)
    invoice = await service.get_invoice_for_payment(token, invoice_id)
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facture non trouvée ou accès non autorisé"
        )
    
    return invoice


# ============== PROTECTED ROUTES (Auth required) ==============

@router.post("/generate-token/{client_id}")
async def generate_portal_token(
    client_id: str,
    validity_days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a portal access token for a client.
    Requires authentication.
    
    Args:
        client_id: The client's ID
        validity_days: How many days the token should be valid (1-30)
    
    Returns:
        The generated token and portal URL
    """
    service = get_client_portal_service(db)
    token = await service.generate_portal_token(
        client_id=client_id,
        user_id=current_user["id"],
        validity_days=validity_days
    )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )
    
    # Build portal URL
    # In production, this should use a configurable base URL
    portal_url = f"/portal/{token}"
    
    return {
        "token": token,
        "portal_url": portal_url,
        "validity_days": validity_days,
        "message": f"Lien de portail client valide {validity_days} jours"
    }
