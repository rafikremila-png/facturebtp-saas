"""
Invoice Reminder Routes
API endpoints for automatic invoice reminders
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.schemas import InvoiceReminderCreate, InvoiceReminderResponse
from app.services.invoice_reminder_service import invoice_reminder_service

router = APIRouter(prefix="/reminders", tags=["Invoice Reminders"])

# Dependency placeholder
async def get_current_user():
    pass

@router.get("")
async def list_reminders(
    invoice_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """List reminder history"""
    reminders = await invoice_reminder_service.get_reminder_history(user["id"], invoice_id)
    return {"reminders": reminders}

@router.get("/pending")
async def list_pending_reminders(user: dict = Depends(get_current_user)):
    """List pending reminders"""
    reminders = await invoice_reminder_service.get_pending_reminders(user["id"])
    return {"reminders": reminders}

@router.post("/invoices/{invoice_id}/schedule")
async def schedule_reminders(invoice_id: str, user: dict = Depends(get_current_user)):
    """Schedule automatic reminders for an invoice"""
    from app.core.database import db, is_mongodb
    
    # Get invoice
    if is_mongodb():
        invoice = await db.invoices.find_one(
            {"id": invoice_id, "user_id": user["id"]},
            {"_id": 0}
        )
        if not invoice:
            raise HTTPException(status_code=404, detail="Facture non trouvée")
        
        if not invoice.get("due_date"):
            raise HTTPException(status_code=400, detail="La facture n'a pas de date d'échéance")
        
        reminders = await invoice_reminder_service.create_reminders_for_invoice(invoice)
        return {"message": f"{len(reminders)} rappels programmés", "reminders": reminders}
    
    raise HTTPException(status_code=500, detail="Base de données non disponible")

@router.post("/invoices/{invoice_id}/cancel")
async def cancel_reminders(invoice_id: str, user: dict = Depends(get_current_user)):
    """Cancel all pending reminders for an invoice"""
    cancelled = await invoice_reminder_service.cancel_reminders_for_invoice(invoice_id)
    return {"message": f"{cancelled} rappels annulés"}

@router.post("/process")
async def process_pending_reminders(user: dict = Depends(get_current_user)):
    """Process and send all pending reminders (admin/cron endpoint)"""
    # Check if admin
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    results = await invoice_reminder_service.process_pending_reminders()
    return results

@router.get("/invoices/{invoice_id}")
async def get_invoice_reminders(invoice_id: str, user: dict = Depends(get_current_user)):
    """Get reminders for a specific invoice"""
    reminders = await invoice_reminder_service.get_reminders_for_invoice(invoice_id)
    return {"reminders": reminders}
