"""
Quote Routes (Devis)
CRUD operations for quotes with electronic signature support
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.database import get_db
from app.services.quote_service import get_quote_service
from app.schemas.schemas import (
    QuoteCreate, QuoteUpdate, QuoteResponse,
    QuoteSignatureCreate, QuoteSignatureResponse
)
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quotes", tags=["Quotes (Devis)"])


@router.post("", response_model=QuoteResponse)
async def create_quote(
    quote_data: QuoteCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new quote (devis)."""
    quote_service = get_quote_service(db)
    quote = await quote_service.create_quote(current_user["id"], quote_data)
    return QuoteResponse.model_validate(quote)


@router.get("", response_model=List[QuoteResponse])
async def list_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all quotes for the current user."""
    quote_service = get_quote_service(db)
    quotes = await quote_service.list_quotes(
        user_id=current_user["id"],
        skip=skip,
        limit=limit,
        status=status,
        client_id=client_id,
        project_id=project_id,
        include_client=True
    )
    return [QuoteResponse.model_validate(q) for q in quotes]


@router.get("/stats")
async def get_quote_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get quote statistics."""
    quote_service = get_quote_service(db)
    return await quote_service.get_quote_stats(current_user["id"])


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific quote."""
    quote_service = get_quote_service(db)
    quote = await quote_service.get_quote_by_id(
        quote_id,
        current_user["id"],
        include_client=True,
        include_project=True,
        include_signature=True
    )
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devis non trouvé"
        )
    
    return QuoteResponse.model_validate(quote)


@router.put("/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: str,
    quote_data: QuoteUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a quote."""
    quote_service = get_quote_service(db)
    
    try:
        quote = await quote_service.update_quote(quote_id, current_user["id"], quote_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devis non trouvé"
        )
    
    return QuoteResponse.model_validate(quote)


@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a quote."""
    quote_service = get_quote_service(db)
    success = await quote_service.delete_quote(quote_id, current_user["id"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devis non trouvé"
        )
    
    return {"message": "Devis supprimé"}


@router.post("/{quote_id}/duplicate", response_model=QuoteResponse)
async def duplicate_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Duplicate an existing quote."""
    quote_service = get_quote_service(db)
    quote = await quote_service.duplicate_quote(quote_id, current_user["id"])
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devis non trouvé"
        )
    
    return QuoteResponse.model_validate(quote)


@router.post("/{quote_id}/status")
async def update_quote_status(
    quote_id: str,
    new_status: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update quote status."""
    valid_statuses = ["draft", "sent", "signed", "accepted", "rejected", "expired"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Statut invalide. Valeurs autorisées: {valid_statuses}"
        )
    
    quote_service = get_quote_service(db)
    quote = await quote_service.update_status(quote_id, current_user["id"], new_status)
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devis non trouvé"
        )
    
    return {"message": f"Statut mis à jour: {new_status}"}


# ============== ELECTRONIC SIGNATURE ==============

@router.post("/{quote_id}/sign", response_model=QuoteSignatureResponse)
async def sign_quote(
    quote_id: str,
    signature_data: QuoteSignatureCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign a quote electronically.
    This endpoint is public (accessed via signature link).
    """
    quote_service = get_quote_service(db)
    
    # Get client IP and user agent for audit
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    try:
        signature = await quote_service.sign_quote(
            quote_id,
            signature_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devis non trouvé"
        )
    
    return QuoteSignatureResponse.model_validate(signature)


@router.get("/{quote_id}/signature", response_model=QuoteSignatureResponse)
async def get_quote_signature(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get signature for a quote."""
    quote_service = get_quote_service(db)
    
    # Verify quote ownership
    quote = await quote_service.get_quote_by_id(quote_id, current_user["id"])
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devis non trouvé"
        )
    
    signature = await quote_service.get_signature(quote_id)
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature non trouvée"
        )
    
    return QuoteSignatureResponse.model_validate(signature)
