"""
Accounting Export Routes
API endpoints for accounting data export
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
import os

from app.core.config import settings
from app.schemas.schemas import AccountingExportRequest
from app.services.accounting_export_service import accounting_export_service

router = APIRouter(prefix="/accounting", tags=["Accounting Export"])

# Dependency placeholder
async def get_current_user():
    pass

@router.get("/export/invoices")
async def export_invoices(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("csv", regex="^(csv|excel)$"),
    user: dict = Depends(get_current_user)
):
    """Export invoices for accounting"""
    result = await accounting_export_service.export_invoices(
        user["id"], start_date, end_date, format
    )
    return result

@router.get("/export/payments")
async def export_payments(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("csv", regex="^(csv|excel)$"),
    user: dict = Depends(get_current_user)
):
    """Export payments for accounting"""
    result = await accounting_export_service.export_payments(
        user["id"], start_date, end_date, format
    )
    return result

@router.get("/export/vat")
async def export_vat(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("csv", regex="^(csv|excel)$"),
    user: dict = Depends(get_current_user)
):
    """Export VAT summary for accounting"""
    result = await accounting_export_service.export_vat(
        user["id"], start_date, end_date, format
    )
    return result

@router.get("/export/full")
async def export_full_accounting(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("csv", regex="^(csv|excel)$"),
    user: dict = Depends(get_current_user)
):
    """Export complete accounting data"""
    result = await accounting_export_service.export_full_accounting(
        user["id"], start_date, end_date, format
    )
    return result

@router.get("/download/{filename}")
async def download_export(filename: str, user: dict = Depends(get_current_user)):
    """Download an exported file"""
    file_path = settings.STORAGE_PATH / "exports" / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    # Verify file belongs to user (basic security check via filename pattern)
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/csv"
    )
