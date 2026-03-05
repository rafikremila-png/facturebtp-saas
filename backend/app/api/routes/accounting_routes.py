"""
Accounting Export Routes
API endpoints for accounting data export
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.api.deps import get_current_user
from app.core.config import settings
from app.services.accounting_export_service import accounting_export_service

router = APIRouter(prefix="/accounting", tags=["Accounting Export"])


@router.get("/export/invoices")
async def export_invoices(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("csv"),
    user: dict = Depends(get_current_user)
):
    """Export invoices for accounting"""
    return await accounting_export_service.export_invoices(
        user["id"], start_date, end_date, format
    )


@router.get("/export/payments")
async def export_payments(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("csv"),
    user: dict = Depends(get_current_user)
):
    """Export payments for accounting"""
    return await accounting_export_service.export_payments(
        user["id"], start_date, end_date, format
    )


@router.get("/export/vat")
async def export_vat(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("csv"),
    user: dict = Depends(get_current_user)
):
    """Export VAT summary for accounting"""
    return await accounting_export_service.export_vat(
        user["id"], start_date, end_date, format
    )


@router.get("/export/full")
async def export_full_accounting(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("csv"),
    user: dict = Depends(get_current_user)
):
    """Export complete accounting data"""
    return await accounting_export_service.export_full_accounting(
        user["id"], start_date, end_date, format
    )


@router.get("/download/{filename}")
async def download_export(filename: str, user: dict = Depends(get_current_user)):
    """Download an exported file"""
    file_path = settings.STORAGE_PATH / "exports" / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/csv"
    )
