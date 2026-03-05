"""
Financial Dashboard Routes
API endpoints for financial analytics
"""
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.schemas import FinancialSummary
from app.services.financial_dashboard_service import financial_dashboard_service

router = APIRouter(prefix="/financial", tags=["Financial Dashboard"])

# Dependency placeholder
async def get_current_user():
    pass

@router.get("/summary")
async def get_financial_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Get financial summary"""
    summary = await financial_dashboard_service.get_summary(user["id"], start_date, end_date)
    return summary

@router.get("/monthly-revenue")
async def get_monthly_revenue(
    months: int = Query(12, ge=1, le=24),
    user: dict = Depends(get_current_user)
):
    """Get monthly revenue breakdown"""
    data = await financial_dashboard_service.get_monthly_revenue(user["id"], months)
    return {"data": data}

@router.get("/cashflow")
async def get_cashflow(
    months: int = Query(6, ge=1, le=12),
    user: dict = Depends(get_current_user)
):
    """Get cashflow data"""
    data = await financial_dashboard_service.get_cashflow(user["id"], months)
    return {"data": data}

@router.get("/invoice-status")
async def get_invoice_status_breakdown(user: dict = Depends(get_current_user)):
    """Get invoice count by status"""
    breakdown = await financial_dashboard_service.get_invoice_status_breakdown(user["id"])
    return breakdown

@router.get("/top-clients")
async def get_top_clients(
    limit: int = Query(5, ge=1, le=20),
    user: dict = Depends(get_current_user)
):
    """Get top clients by revenue"""
    clients = await financial_dashboard_service.get_top_clients(user["id"], limit)
    return {"clients": clients}

@router.get("/vat-summary")
async def get_vat_summary(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    user: dict = Depends(get_current_user)
):
    """Get VAT summary for accounting"""
    summary = await financial_dashboard_service.get_vat_summary(user["id"], start_date, end_date)
    return summary

@router.get("/aging-report")
async def get_aging_report(user: dict = Depends(get_current_user)):
    """Get accounts receivable aging report"""
    report = await financial_dashboard_service.get_aging_report(user["id"])
    return {"report": report}
