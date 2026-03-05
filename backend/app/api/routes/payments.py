"""
Stripe Payment Routes
Endpoints for invoice payments via Stripe Checkout
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import logging

from app.core.database import get_db
from app.services.stripe_payment_service import get_stripe_payment_service
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments (Stripe)"])


class PaymentRequest(BaseModel):
    invoice_id: str
    origin_url: str  # Frontend origin for redirect URLs


@router.post("/checkout")
async def create_checkout_session(
    request: PaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe Checkout session for invoice payment.
    
    The amount is determined server-side from the invoice - NOT from frontend.
    """
    service = get_stripe_payment_service(db)
    
    result = await service.create_invoice_checkout(
        invoice_id=request.invoice_id,
        user_id=current_user["id"],
        base_url=request.origin_url
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.get("/status/{session_id}")
async def get_payment_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check the status of a Stripe payment session.
    Poll this endpoint after redirect from Stripe.
    """
    service = get_stripe_payment_service(db)
    
    result = await service.check_payment_status(session_id)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhooks for payment updates.
    This endpoint is called by Stripe, not by the frontend.
    """
    try:
        payload = await request.body()
        
        if not stripe_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature"
            )
        
        service = get_stripe_payment_service(db)
        result = await service.handle_webhook(payload, stripe_signature)
        
        return {"status": "ok", **result}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============== PORTAL PAYMENT (No auth - via token) ==============

@router.post("/portal/checkout")
async def create_portal_checkout(
    invoice_id: str,
    token: str,
    origin_url: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Create Stripe checkout from client portal (no auth required).
    Uses portal token for authorization.
    """
    from app.services.client_portal_service import get_client_portal_service
    
    # Validate portal token
    portal_service = get_client_portal_service(db)
    client = await portal_service.validate_token(token)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Lien invalide ou expiré"
        )
    
    # Get invoice and verify it belongs to this client
    from sqlalchemy import select
    from app.models.models import Invoice
    
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice or invoice.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facture non trouvée"
        )
    
    # Create checkout
    service = get_stripe_payment_service(db)
    result = await service.create_invoice_checkout(
        invoice_id=invoice_id,
        user_id=invoice.user_id,  # Use invoice owner for the payment record
        base_url=origin_url
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result
