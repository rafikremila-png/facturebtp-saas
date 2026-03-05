"""
Client Portal Service
Secure client access for quotes, invoices, and payments
"""
import uuid
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import logging

from app.core.config import settings
from app.core.database import db, is_mongodb
from app.core.security import create_client_access_token, decode_token

logger = logging.getLogger(__name__)

class ClientPortalService:
    """Service for client portal access"""
    
    @staticmethod
    async def generate_access_link(client_id: str, user_id: str, 
                                   document_type: str = None,
                                   document_id: str = None) -> Dict[str, Any]:
        """Generate a secure access link for a client"""
        # Verify client belongs to user
        if is_mongodb():
            client = await db.clients.find_one(
                {"id": client_id, "user_id": user_id},
                {"_id": 0}
            )
            if not client:
                raise ValueError("Client non trouvé")
        
        # Generate access token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Store token
        if is_mongodb():
            await db.clients.update_one(
                {"id": client_id},
                {
                    "$set": {
                        "access_token": token,
                        "token_expires_at": expires_at.isoformat()
                    }
                }
            )
        
        # Build URL
        portal_url = f"{settings.FRONTEND_URL}/portal/{token}"
        
        if document_type and document_id:
            portal_url += f"?type={document_type}&id={document_id}"
        
        return {
            "access_url": portal_url,
            "token": token,
            "expires_at": expires_at.isoformat(),
            "client_name": client.get("name") if client else None
        }
    
    @staticmethod
    async def validate_portal_access(token: str) -> Optional[Dict[str, Any]]:
        """Validate portal access token and return client data"""
        if is_mongodb():
            client = await db.clients.find_one(
                {"access_token": token},
                {"_id": 0}
            )
            
            if not client:
                return None
            
            # Check expiration
            expires_at_str = client.get("token_expires_at")
            if expires_at_str:
                try:
                    expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                    if expires_at < datetime.now(timezone.utc):
                        return None
                except:
                    pass
            
            return {
                "client_id": client["id"],
                "client_name": client.get("name"),
                "client_email": client.get("email"),
                "user_id": client.get("user_id")
            }
        
        return None
    
    @staticmethod
    async def get_client_quotes(client_id: str) -> List[Dict[str, Any]]:
        """Get all quotes for a client (portal view)"""
        if is_mongodb():
            cursor = db.quotes.find(
                {
                    "client_id": client_id,
                    "status": {"$in": ["sent", "signed", "accepted"]}
                },
                {
                    "_id": 0,
                    "id": 1,
                    "quote_number": 1,
                    "title": 1,
                    "quote_date": 1,
                    "validity_date": 1,
                    "total_ttc": 1,
                    "status": 1
                }
            ).sort("quote_date", -1)
            
            quotes = await cursor.to_list(length=100)
            
            # Add signature status
            for quote in quotes:
                signature = await db.quote_signatures.find_one(
                    {"quote_id": quote["id"]},
                    {"_id": 0, "signed_at": 1, "signer_name": 1}
                )
                quote["signature"] = signature
                quote["can_sign"] = quote.get("status") in ["sent"] and not signature
            
            return quotes
        return []
    
    @staticmethod
    async def get_client_invoices(client_id: str) -> List[Dict[str, Any]]:
        """Get all invoices for a client (portal view)"""
        if is_mongodb():
            cursor = db.invoices.find(
                {
                    "client_id": client_id,
                    "status": {"$in": ["sent", "paid", "partial", "overdue"]}
                },
                {
                    "_id": 0,
                    "id": 1,
                    "invoice_number": 1,
                    "title": 1,
                    "invoice_date": 1,
                    "due_date": 1,
                    "total_ttc": 1,
                    "amount_paid": 1,
                    "status": 1
                }
            ).sort("invoice_date", -1)
            
            invoices = await cursor.to_list(length=100)
            
            # Add computed fields
            for inv in invoices:
                inv["amount_due"] = inv.get("total_ttc", 0) - inv.get("amount_paid", 0)
                inv["can_pay"] = inv.get("status") in ["sent", "partial", "overdue"] and inv["amount_due"] > 0
            
            return invoices
        return []
    
    @staticmethod
    async def get_client_payments(client_id: str) -> List[Dict[str, Any]]:
        """Get payment history for a client"""
        if is_mongodb():
            # First get client's invoices
            invoice_cursor = db.invoices.find(
                {"client_id": client_id},
                {"_id": 0, "id": 1, "invoice_number": 1}
            )
            invoices = await invoice_cursor.to_list(length=1000)
            invoice_ids = [inv["id"] for inv in invoices]
            invoice_map = {inv["id"]: inv["invoice_number"] for inv in invoices}
            
            if not invoice_ids:
                return []
            
            # Get payments
            payments_cursor = db.payments.find(
                {"invoice_id": {"$in": invoice_ids}},
                {"_id": 0}
            ).sort("payment_date", -1)
            
            payments = await payments_cursor.to_list(length=500)
            
            # Add invoice number
            for payment in payments:
                payment["invoice_number"] = invoice_map.get(payment.get("invoice_id"))
            
            return payments
        return []
    
    @staticmethod
    async def get_quote_for_signing(quote_id: str, client_id: str) -> Optional[Dict[str, Any]]:
        """Get quote details for signature page"""
        if is_mongodb():
            quote = await db.quotes.find_one(
                {
                    "id": quote_id,
                    "client_id": client_id,
                    "status": {"$in": ["sent", "draft"]}
                },
                {"_id": 0}
            )
            
            if not quote:
                return None
            
            # Check if already signed
            signature = await db.quote_signatures.find_one(
                {"quote_id": quote_id},
                {"_id": 0}
            )
            
            if signature:
                return None  # Already signed
            
            # Get company info
            user_settings = await db.user_settings.find_one(
                {"user_id": quote["user_id"]},
                {"_id": 0}
            )
            
            # Get client
            client = await db.clients.find_one(
                {"id": client_id},
                {"_id": 0}
            )
            
            return {
                "quote": quote,
                "company": user_settings,
                "client": client,
                "can_sign": True
            }
        
        return None
    
    @staticmethod
    async def get_invoice_for_payment(invoice_id: str, client_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice details for payment page"""
        if is_mongodb():
            invoice = await db.invoices.find_one(
                {
                    "id": invoice_id,
                    "client_id": client_id,
                    "status": {"$in": ["sent", "partial", "overdue"]}
                },
                {"_id": 0}
            )
            
            if not invoice:
                return None
            
            amount_due = invoice.get("total_ttc", 0) - invoice.get("amount_paid", 0)
            
            if amount_due <= 0:
                return None
            
            # Get company info
            user_settings = await db.user_settings.find_one(
                {"user_id": invoice["user_id"]},
                {"_id": 0}
            )
            
            # Get client
            client = await db.clients.find_one(
                {"id": client_id},
                {"_id": 0}
            )
            
            # Get payment history
            payments_cursor = db.payments.find(
                {"invoice_id": invoice_id},
                {"_id": 0}
            ).sort("payment_date", -1)
            payments = await payments_cursor.to_list(length=100)
            
            return {
                "invoice": invoice,
                "company": user_settings,
                "client": client,
                "amount_due": amount_due,
                "payments": payments,
                "can_pay": True
            }
        
        return None
    
    @staticmethod
    async def get_portal_dashboard(client_id: str) -> Dict[str, Any]:
        """Get complete portal dashboard for a client"""
        quotes = await ClientPortalService.get_client_quotes(client_id)
        invoices = await ClientPortalService.get_client_invoices(client_id)
        payments = await ClientPortalService.get_client_payments(client_id)
        
        # Calculate summary
        total_quotes = len(quotes)
        pending_signatures = len([q for q in quotes if q.get("can_sign")])
        
        total_invoiced = sum(inv.get("total_ttc", 0) for inv in invoices)
        total_paid = sum(inv.get("amount_paid", 0) for inv in invoices)
        total_due = total_invoiced - total_paid
        
        pending_invoices = len([inv for inv in invoices if inv.get("can_pay")])
        
        return {
            "quotes": quotes,
            "invoices": invoices,
            "payments": payments[:10],  # Last 10 payments
            "summary": {
                "total_quotes": total_quotes,
                "pending_signatures": pending_signatures,
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "total_due": total_due,
                "pending_invoices": pending_invoices
            }
        }


# Create singleton instance
client_portal_service = ClientPortalService()
