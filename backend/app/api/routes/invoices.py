"""
Invoice Routes (Factures)
CRUD operations for invoices with BTP-specific features:
- Progress invoicing (factures de situation)
- Retenue de garantie
- Payments
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.database import get_db
from app.services.invoice_service import get_invoice_service
from app.schemas.schemas import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    PaymentCreate, PaymentResponse
)
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoices", tags=["Invoices (Factures)"])


@router.post("", response_model=InvoiceResponse)
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new invoice (facture)."""
    invoice_service = get_invoice_service(db)
    invoice = await invoice_service.create_invoice(current_user["id"], invoice_data)
    return InvoiceResponse.model_validate(invoice)


@router.post("/situation")
async def create_situation_invoice(
    quote_id: str,
    progress_percentage: float,
    retention_rate: float = 0,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a progress invoice (facture de situation) from a quote.
    
    Args:
        quote_id: The quote to create situation from
        progress_percentage: Cumulative progress (e.g., 30, 60, 100)
        retention_rate: Retention percentage (0-5% typically)
        notes: Additional notes
    """
    invoice_service = get_invoice_service(db)
    
    try:
        invoice = await invoice_service.create_situation_invoice(
            user_id=current_user["id"],
            quote_id=quote_id,
            progress_percentage=progress_percentage,
            retention_rate=retention_rate,
            notes=notes
        )
        return InvoiceResponse.model_validate(invoice)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[InvoiceResponse])
async def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    project_id: Optional[str] = None,
    overdue_only: bool = False,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all invoices for the current user."""
    invoice_service = get_invoice_service(db)
    invoices = await invoice_service.list_invoices(
        user_id=current_user["id"],
        skip=skip,
        limit=limit,
        status=status,
        client_id=client_id,
        project_id=project_id,
        include_client=True,
        overdue_only=overdue_only
    )
    return [InvoiceResponse.model_validate(i) for i in invoices]


@router.get("/stats")
async def get_invoice_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get invoice statistics."""
    invoice_service = get_invoice_service(db)
    return await invoice_service.get_invoice_stats(current_user["id"])


@router.get("/retention-summary")
async def get_retention_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get summary of all retentions (retenues de garantie)."""
    invoice_service = get_invoice_service(db)
    return await invoice_service.get_retention_summary(current_user["id"])


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific invoice."""
    invoice_service = get_invoice_service(db)
    invoice = await invoice_service.get_invoice_by_id(
        invoice_id,
        current_user["id"],
        include_client=True,
        include_project=True,
        include_payments=True
    )
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facture non trouvée"
        )
    
    return InvoiceResponse.model_validate(invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    invoice_data: InvoiceUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an invoice."""
    invoice_service = get_invoice_service(db)
    
    try:
        invoice = await invoice_service.update_invoice(invoice_id, current_user["id"], invoice_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facture non trouvée"
        )
    
    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an invoice."""
    invoice_service = get_invoice_service(db)
    
    try:
        success = await invoice_service.delete_invoice(invoice_id, current_user["id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facture non trouvée"
        )
    
    return {"message": "Facture supprimée"}


# ============== PAYMENTS ==============

@router.post("/{invoice_id}/payments", response_model=PaymentResponse)
async def add_payment(
    invoice_id: str,
    payment_data: PaymentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a payment to an invoice."""
    invoice_service = get_invoice_service(db)
    
    # Override invoice_id from URL
    payment_data.invoice_id = invoice_id
    
    try:
        payment = await invoice_service.add_payment(current_user["id"], payment_data)
        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{invoice_id}/payments", response_model=List[PaymentResponse])
async def list_payments(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all payments for an invoice."""
    invoice_service = get_invoice_service(db)
    
    # Verify invoice ownership
    invoice = await invoice_service.get_invoice_by_id(invoice_id, current_user["id"])
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facture non trouvée"
        )
    
    payments = await invoice_service.list_payments(invoice_id)
    return [PaymentResponse.model_validate(p) for p in payments]


# ============== RETENTION ==============

@router.post("/{invoice_id}/release-retention")
async def release_retention(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Release retention amount (libérer la retenue de garantie)."""
    invoice_service = get_invoice_service(db)
    
    try:
        invoice = await invoice_service.release_retention(invoice_id, current_user["id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facture non trouvée"
        )
    
    return {
        "message": "Retenue de garantie libérée",
        "amount": invoice.retention_amount
    }
