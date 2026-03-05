"""
Recurring Invoice Routes
API endpoints for recurring invoices
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.schemas import (
    RecurringInvoiceCreate, RecurringInvoiceUpdate, RecurringInvoiceResponse
)
from app.services.recurring_invoice_service import recurring_invoice_service

router = APIRouter(prefix="/recurring-invoices", tags=["Recurring Invoices"])

# Dependency placeholder
async def get_current_user():
    pass

@router.post("", response_model=RecurringInvoiceResponse)
async def create_recurring_invoice(
    data: RecurringInvoiceCreate,
    user: dict = Depends(get_current_user)
):
    """Create a new recurring invoice"""
    recurring = await recurring_invoice_service.create(user["id"], data.model_dump())
    return recurring

@router.get("", response_model=List[RecurringInvoiceResponse])
async def list_recurring_invoices(
    status: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """List all recurring invoices"""
    return await recurring_invoice_service.get_all(user["id"], status)

@router.get("/{recurring_id}", response_model=RecurringInvoiceResponse)
async def get_recurring_invoice(
    recurring_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a recurring invoice by ID"""
    recurring = await recurring_invoice_service.get_by_id(recurring_id, user["id"])
    if not recurring:
        raise HTTPException(status_code=404, detail="Facture récurrente non trouvée")
    return recurring

@router.put("/{recurring_id}", response_model=RecurringInvoiceResponse)
async def update_recurring_invoice(
    recurring_id: str,
    data: RecurringInvoiceUpdate,
    user: dict = Depends(get_current_user)
):
    """Update a recurring invoice"""
    recurring = await recurring_invoice_service.update(
        recurring_id, user["id"], data.model_dump(exclude_unset=True)
    )
    if not recurring:
        raise HTTPException(status_code=404, detail="Facture récurrente non trouvée")
    return recurring

@router.post("/{recurring_id}/pause")
async def pause_recurring_invoice(
    recurring_id: str,
    user: dict = Depends(get_current_user)
):
    """Pause a recurring invoice"""
    success = await recurring_invoice_service.pause(recurring_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Facture récurrente non trouvée ou déjà en pause")
    return {"message": "Facture récurrente mise en pause"}

@router.post("/{recurring_id}/resume")
async def resume_recurring_invoice(
    recurring_id: str,
    user: dict = Depends(get_current_user)
):
    """Resume a paused recurring invoice"""
    success = await recurring_invoice_service.resume(recurring_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Facture récurrente non trouvée ou non en pause")
    return {"message": "Facture récurrente reprise"}

@router.delete("/{recurring_id}")
async def delete_recurring_invoice(
    recurring_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a recurring invoice"""
    success = await recurring_invoice_service.delete(recurring_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Facture récurrente non trouvée")
    return {"message": "Facture récurrente supprimée"}

@router.post("/{recurring_id}/generate")
async def generate_invoice_now(
    recurring_id: str,
    user: dict = Depends(get_current_user)
):
    """Generate an invoice from this recurring template now"""
    recurring = await recurring_invoice_service.get_by_id(recurring_id, user["id"])
    if not recurring:
        raise HTTPException(status_code=404, detail="Facture récurrente non trouvée")
    
    invoice = await recurring_invoice_service.generate_invoice_from_recurring(recurring)
    return {"message": "Facture générée", "invoice_id": invoice["id"]}
