"""
Financial Tools Routes
Recurring invoices, reminders, and accounting exports
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import io
import logging

from app.core.database import get_db
from app.services.recurring_reminder_service import (
    get_recurring_invoice_service,
    get_invoice_reminder_service
)
from app.services.accounting_export_service import get_accounting_export_service
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)


# ============== SCHEMAS ==============

class RecurringInvoiceCreate(BaseModel):
    client_id: str
    title: str
    items: List[dict]
    frequency: str = Field("monthly", pattern="^(weekly|monthly|quarterly|yearly)$")
    start_date: datetime
    end_date: Optional[datetime] = None
    payment_days: int = Field(30, ge=1, le=365)
    notes: Optional[str] = None


class RecurringInvoiceUpdate(BaseModel):
    title: Optional[str] = None
    items: Optional[List[dict]] = None
    frequency: Optional[str] = None
    end_date: Optional[datetime] = None
    payment_days: Optional[int] = None
    notes: Optional[str] = None


class ReminderCreate(BaseModel):
    invoice_id: str
    reminder_type: str = "custom"
    scheduled_date: datetime
    subject: Optional[str] = None
    message: Optional[str] = None


router = APIRouter(prefix="/financial", tags=["Financial Tools"])


# ============== RECURRING INVOICES ==============

@router.post("/recurring")
async def create_recurring_invoice(
    data: RecurringInvoiceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new recurring invoice template."""
    service = get_recurring_invoice_service(db)
    recurring = await service.create_recurring_invoice(
        user_id=current_user["id"],
        **data.model_dump()
    )
    return _format_recurring(recurring)


@router.get("/recurring")
async def list_recurring_invoices(
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List recurring invoice templates."""
    service = get_recurring_invoice_service(db)
    items = await service.list_recurring_invoices(
        user_id=current_user["id"],
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return [_format_recurring(item) for item in items]


@router.get("/recurring/{recurring_id}")
async def get_recurring_invoice(
    recurring_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a recurring invoice template."""
    service = get_recurring_invoice_service(db)
    recurring = await service.get_recurring_invoice_by_id(recurring_id, current_user["id"])
    
    if not recurring:
        raise HTTPException(status_code=404, detail="Facture récurrente non trouvée")
    
    return _format_recurring(recurring)


@router.put("/recurring/{recurring_id}")
async def update_recurring_invoice(
    recurring_id: str,
    data: RecurringInvoiceUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a recurring invoice template."""
    service = get_recurring_invoice_service(db)
    recurring = await service.update_recurring_invoice(
        recurring_id,
        current_user["id"],
        **data.model_dump(exclude_unset=True)
    )
    
    if not recurring:
        raise HTTPException(status_code=404, detail="Facture récurrente non trouvée")
    
    return _format_recurring(recurring)


@router.post("/recurring/{recurring_id}/toggle")
async def toggle_recurring_invoice(
    recurring_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle active status of a recurring invoice."""
    service = get_recurring_invoice_service(db)
    recurring = await service.toggle_active(recurring_id, current_user["id"])
    
    if not recurring:
        raise HTTPException(status_code=404, detail="Facture récurrente non trouvée")
    
    return {
        "message": f"Facture récurrente {'activée' if recurring.is_active else 'désactivée'}",
        "is_active": recurring.is_active
    }


@router.delete("/recurring/{recurring_id}")
async def delete_recurring_invoice(
    recurring_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a recurring invoice template."""
    service = get_recurring_invoice_service(db)
    success = await service.delete_recurring_invoice(recurring_id, current_user["id"])
    
    if not success:
        raise HTTPException(status_code=404, detail="Facture récurrente non trouvée")
    
    return {"message": "Facture récurrente supprimée"}


# ============== REMINDERS ==============

@router.post("/reminders")
async def create_reminder(
    data: ReminderCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new invoice reminder."""
    service = get_invoice_reminder_service(db)
    reminder = await service.create_reminder(
        user_id=current_user["id"],
        **data.model_dump()
    )
    return _format_reminder(reminder)


@router.get("/reminders")
async def list_reminders(
    invoice_id: Optional[str] = None,
    is_sent: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List invoice reminders."""
    service = get_invoice_reminder_service(db)
    items = await service.list_reminders(
        user_id=current_user["id"],
        invoice_id=invoice_id,
        is_sent=is_sent,
        skip=skip,
        limit=limit
    )
    return [_format_reminder(item) for item in items]


@router.post("/reminders/{invoice_id}/schedule")
async def schedule_reminders(
    invoice_id: str,
    due_date: datetime,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule automatic reminders for an invoice."""
    service = get_invoice_reminder_service(db)
    reminders = await service.schedule_reminders_for_invoice(
        user_id=current_user["id"],
        invoice_id=invoice_id,
        due_date=due_date
    )
    return {
        "message": f"{len(reminders)} rappels programmés",
        "reminders": [_format_reminder(r) for r in reminders]
    }


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a reminder."""
    service = get_invoice_reminder_service(db)
    success = await service.delete_reminder(reminder_id, current_user["id"])
    
    if not success:
        raise HTTPException(status_code=404, detail="Rappel non trouvé")
    
    return {"message": "Rappel supprimé"}


# ============== EXPORTS ==============

@router.get("/export/invoices")
async def export_invoices_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export invoices to CSV."""
    service = get_accounting_export_service(db)
    csv_content = await service.export_invoices_csv(
        user_id=current_user["id"],
        start_date=start_date,
        end_date=end_date,
        status=status
    )
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=factures_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/export/payments")
async def export_payments_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export payments to CSV."""
    service = get_accounting_export_service(db)
    csv_content = await service.export_payments_csv(
        user_id=current_user["id"],
        start_date=start_date,
        end_date=end_date
    )
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=paiements_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/export/vat-summary")
async def export_vat_summary_csv(
    start_date: datetime,
    end_date: datetime,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export VAT summary to CSV."""
    service = get_accounting_export_service(db)
    csv_content = await service.export_vat_summary_csv(
        user_id=current_user["id"],
        start_date=start_date,
        end_date=end_date
    )
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=tva_{start_date.strftime('%Y%m')}_{end_date.strftime('%Y%m')}.csv"
        }
    )


@router.get("/export/client-balance")
async def export_client_balance_csv(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export client balance summary to CSV."""
    service = get_accounting_export_service(db)
    csv_content = await service.export_client_balance_csv(
        user_id=current_user["id"]
    )
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=soldes_clients_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/summary")
async def get_financial_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get financial summary for a period."""
    service = get_accounting_export_service(db)
    return await service.get_financial_summary(
        user_id=current_user["id"],
        start_date=start_date,
        end_date=end_date
    )


# ============== HELPERS ==============

def _format_recurring(recurring) -> dict:
    return {
        'id': recurring.id,
        'user_id': recurring.user_id,
        'client_id': recurring.client_id,
        'title': recurring.title,
        'items': recurring.items,
        'subtotal_ht': float(recurring.subtotal_ht or 0),
        'total_vat': float(recurring.total_vat or 0),
        'total_ttc': float(recurring.total_ttc or 0),
        'frequency': recurring.frequency,
        'start_date': recurring.start_date.isoformat() if recurring.start_date else None,
        'end_date': recurring.end_date.isoformat() if recurring.end_date else None,
        'next_generation_date': recurring.next_generation_date.isoformat() if recurring.next_generation_date else None,
        'payment_days': recurring.payment_days,
        'is_active': recurring.is_active,
        'generated_count': recurring.generated_count,
        'notes': recurring.notes,
        'created_at': recurring.created_at.isoformat() if recurring.created_at else None
    }


def _format_reminder(reminder) -> dict:
    return {
        'id': reminder.id,
        'user_id': reminder.user_id,
        'invoice_id': reminder.invoice_id,
        'reminder_type': reminder.reminder_type,
        'scheduled_date': reminder.scheduled_date.isoformat() if reminder.scheduled_date else None,
        'subject': reminder.subject,
        'message': reminder.message,
        'is_sent': reminder.is_sent,
        'sent_date': reminder.sent_date.isoformat() if reminder.sent_date else None,
        'created_at': reminder.created_at.isoformat() if reminder.created_at else None
    }
