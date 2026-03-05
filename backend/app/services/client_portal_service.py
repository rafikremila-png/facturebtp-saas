"""
Client Portal Service
Secure token-based access for clients to view quotes, invoices, and sign documents
No client account required - access via secure token links
"""
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Client, Quote, Invoice, QuoteSignature, Payment
from app.core.security import generate_uuid

logger = logging.getLogger(__name__)


class ClientPortalService:
    """Service for client portal functionality"""
    
    TOKEN_VALIDITY_DAYS = 7
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_portal_token(
        self, 
        client_id: str, 
        user_id: str,
        validity_days: int = None
    ) -> Optional[str]:
        """Generate a secure access token for client portal"""
        # Verify client belongs to user
        result = await self.db.execute(
            select(Client).where(and_(
                Client.id == client_id,
                Client.user_id == user_id
            ))
        )
        client = result.scalar_one_or_none()
        
        if not client:
            return None
        
        # Generate secure token
        token = secrets.token_urlsafe(48)
        validity = validity_days or self.TOKEN_VALIDITY_DAYS
        expires_at = datetime.now(timezone.utc) + timedelta(days=validity)
        
        # Store token
        client.access_token = token
        client.token_expires_at = expires_at
        client.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        
        return token
    
    async def validate_token(self, token: str) -> Optional[Client]:
        """Validate portal token and return client if valid"""
        result = await self.db.execute(
            select(Client).where(and_(
                Client.access_token == token,
                Client.token_expires_at > datetime.now(timezone.utc)
            ))
        )
        return result.scalar_one_or_none()
    
    async def get_client_portal_data(self, token: str) -> Optional[Dict[str, Any]]:
        """Get all portal data for a client"""
        client = await self.validate_token(token)
        if not client:
            return None
        
        # Get quotes for this client
        quotes = await self._get_client_quotes(client.id)
        
        # Get invoices for this client
        invoices = await self._get_client_invoices(client.id)
        
        return {
            "client": {
                "id": client.id,
                "name": client.name,
                "email": client.email,
                "company_name": client.company_name
            },
            "quotes": quotes,
            "invoices": invoices,
            "pending_signatures": [q for q in quotes if q.get("status") in ["draft", "sent"]],
            "unpaid_invoices": [i for i in invoices if i.get("status") not in ["paid"]]
        }
    
    async def get_quote_for_signature(self, token: str, quote_id: str) -> Optional[Dict]:
        """Get quote details for signing"""
        client = await self.validate_token(token)
        if not client:
            return None
        
        result = await self.db.execute(
            select(Quote)
            .options(selectinload(Quote.signature))
            .where(and_(
                Quote.id == quote_id,
                Quote.client_id == client.id
            ))
        )
        quote = result.scalar_one_or_none()
        
        if not quote:
            return None
        
        return self._format_quote(quote)
    
    async def sign_quote_from_portal(
        self,
        token: str,
        quote_id: str,
        signer_name: str,
        signer_email: str,
        signature_data: str,
        signer_title: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict]:
        """Sign a quote from the client portal"""
        client = await self.validate_token(token)
        if not client:
            return None
        
        # Get the quote
        result = await self.db.execute(
            select(Quote).where(and_(
                Quote.id == quote_id,
                Quote.client_id == client.id
            ))
        )
        quote = result.scalar_one_or_none()
        
        if not quote:
            return None
        
        if quote.status not in ["draft", "sent"]:
            return {"error": "Ce devis ne peut plus être signé"}
        
        # Create signature
        signature = QuoteSignature(
            id=generate_uuid(),
            quote_id=quote_id,
            signer_name=signer_name,
            signer_email=signer_email,
            signer_title=signer_title,
            signature_data=signature_data,
            ip_address=ip_address,
            user_agent=user_agent,
            signed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(signature)
        
        # Update quote status
        quote.status = "signed"
        quote.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        
        return {
            "success": True,
            "quote_id": quote_id,
            "signed_at": signature.signed_at.isoformat(),
            "message": "Devis signé avec succès"
        }
    
    async def get_invoice_for_payment(self, token: str, invoice_id: str) -> Optional[Dict]:
        """Get invoice details for payment"""
        client = await self.validate_token(token)
        if not client:
            return None
        
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.payments))
            .where(and_(
                Invoice.id == invoice_id,
                Invoice.client_id == client.id
            ))
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return None
        
        return self._format_invoice(invoice)
    
    async def _get_client_quotes(self, client_id: str) -> List[Dict]:
        """Get all quotes for a client"""
        result = await self.db.execute(
            select(Quote)
            .options(selectinload(Quote.signature))
            .where(Quote.client_id == client_id)
            .order_by(Quote.created_at.desc())
        )
        quotes = list(result.scalars().all())
        
        return [self._format_quote(q) for q in quotes]
    
    async def _get_client_invoices(self, client_id: str) -> List[Dict]:
        """Get all invoices for a client"""
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.payments))
            .where(Invoice.client_id == client_id)
            .order_by(Invoice.created_at.desc())
        )
        invoices = list(result.scalars().all())
        
        return [self._format_invoice(i) for i in invoices]
    
    def _format_quote(self, quote: Quote) -> Dict:
        """Format quote for portal response"""
        return {
            "id": quote.id,
            "quote_number": quote.quote_number,
            "title": quote.title,
            "description": quote.description,
            "status": quote.status,
            "quote_date": quote.quote_date.isoformat() if quote.quote_date else None,
            "validity_date": quote.validity_date.isoformat() if quote.validity_date else None,
            "items": quote.items or [],
            "subtotal_ht": float(quote.subtotal_ht or 0),
            "total_vat": float(quote.total_vat or 0),
            "total_ttc": float(quote.total_ttc or 0),
            "discount_amount": float(quote.discount_amount or 0),
            "retention_amount": float(quote.retention_amount or 0),
            "notes": quote.notes,
            "terms": quote.terms,
            "is_signed": quote.signature is not None,
            "signature": {
                "signer_name": quote.signature.signer_name,
                "signed_at": quote.signature.signed_at.isoformat()
            } if quote.signature else None
        }
    
    def _format_invoice(self, invoice: Invoice) -> Dict:
        """Format invoice for portal response"""
        return {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "title": invoice.title,
            "status": invoice.status,
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            "items": invoice.items or [],
            "subtotal_ht": float(invoice.subtotal_ht or 0),
            "total_vat": float(invoice.total_vat or 0),
            "total_ttc": float(invoice.total_ttc or 0),
            "amount_paid": float(invoice.amount_paid or 0),
            "amount_due": float(invoice.amount_due or 0),
            "invoice_type": invoice.invoice_type,
            "situation_number": invoice.situation_number,
            "progress_percentage": invoice.progress_percentage,
            "retention_amount": float(invoice.retention_amount or 0),
            "notes": invoice.notes,
            "is_overdue": invoice.due_date and invoice.due_date < datetime.now(timezone.utc) and invoice.status != "paid",
            "payments": [
                {
                    "amount": float(p.amount),
                    "date": p.payment_date.isoformat() if p.payment_date else None,
                    "method": p.payment_method
                }
                for p in (invoice.payments or [])
            ]
        }


def get_client_portal_service(db: AsyncSession) -> ClientPortalService:
    """Factory function"""
    return ClientPortalService(db)
