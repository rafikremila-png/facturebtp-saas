"""
Client Portal Routes
API endpoints for client portal access
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.services.client_portal_service import client_portal_service

router = APIRouter(prefix="/portal", tags=["Client Portal"])


@router.post("/generate-link")
async def generate_portal_link(
    client_id: str,
    document_type: Optional[str] = None,
    document_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Generate a portal access link for a client"""
    try:
        result = await client_portal_service.generate_access_link(
            client_id,
            user["id"],
            document_type,
            document_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/access/{token}")
async def validate_portal_access(token: str):
    """Validate portal access and get client info"""
    result = await client_portal_service.validate_portal_access(token)
    if not result:
        raise HTTPException(status_code=401, detail="Accès non autorisé ou expiré")
    return result


@router.get("/{token}/dashboard")
async def get_portal_dashboard(token: str):
    """Get complete portal dashboard for a client"""
    access = await client_portal_service.validate_portal_access(token)
    if not access:
        raise HTTPException(status_code=401, detail="Accès non autorisé ou expiré")
    
    return await client_portal_service.get_portal_dashboard(access["client_id"])


@router.get("/{token}/quotes")
async def get_portal_quotes(token: str):
    """Get client's quotes"""
    access = await client_portal_service.validate_portal_access(token)
    if not access:
        raise HTTPException(status_code=401, detail="Accès non autorisé ou expiré")
    
    quotes = await client_portal_service.get_client_quotes(access["client_id"])
    return {"quotes": quotes}


@router.get("/{token}/invoices")
async def get_portal_invoices(token: str):
    """Get client's invoices"""
    access = await client_portal_service.validate_portal_access(token)
    if not access:
        raise HTTPException(status_code=401, detail="Accès non autorisé ou expiré")
    
    invoices = await client_portal_service.get_client_invoices(access["client_id"])
    return {"invoices": invoices}


@router.get("/{token}/payments")
async def get_portal_payments(token: str):
    """Get client's payment history"""
    access = await client_portal_service.validate_portal_access(token)
    if not access:
        raise HTTPException(status_code=401, detail="Accès non autorisé ou expiré")
    
    payments = await client_portal_service.get_client_payments(access["client_id"])
    return {"payments": payments}


@router.get("/{token}/quotes/{quote_id}/sign")
async def get_quote_for_signing(token: str, quote_id: str):
    """Get quote details for signing"""
    access = await client_portal_service.validate_portal_access(token)
    if not access:
        raise HTTPException(status_code=401, detail="Accès non autorisé ou expiré")
    
    quote_data = await client_portal_service.get_quote_for_signing(quote_id, access["client_id"])
    if not quote_data:
        raise HTTPException(status_code=404, detail="Devis non trouvé ou déjà signé")
    
    return quote_data


@router.get("/{token}/invoices/{invoice_id}/pay")
async def get_invoice_for_payment(token: str, invoice_id: str):
    """Get invoice details for payment"""
    access = await client_portal_service.validate_portal_access(token)
    if not access:
        raise HTTPException(status_code=401, detail="Accès non autorisé ou expiré")
    
    invoice_data = await client_portal_service.get_invoice_for_payment(invoice_id, access["client_id"])
    if not invoice_data:
        raise HTTPException(status_code=404, detail="Facture non trouvée ou déjà payée")
    
    return invoice_data
