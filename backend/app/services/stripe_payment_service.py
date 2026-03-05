"""
Stripe Payment Service
Handle invoice payments via Stripe Checkout
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from dotenv import load_dotenv
load_dotenv()

from app.models.models import Invoice, Payment
from app.core.security import generate_uuid

logger = logging.getLogger(__name__)


class StripePaymentService:
    """Service for Stripe payment integration"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_key = os.getenv("STRIPE_API_KEY")
        if not self.api_key:
            raise ValueError("STRIPE_API_KEY not configured")
    
    async def create_invoice_checkout(
        self,
        invoice_id: str,
        user_id: str,
        base_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for invoice payment
        
        Args:
            invoice_id: The invoice to pay
            user_id: Owner of the invoice (for verification)
            base_url: Base URL for success/cancel redirects
        
        Returns:
            Checkout session URL and ID
        """
        from emergentintegrations.payments.stripe.checkout import (
            StripeCheckout, CheckoutSessionRequest
        )
        
        # Get invoice
        result = await self.db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return {"error": "Facture non trouvée"}
        
        if invoice.user_id != user_id:
            return {"error": "Accès non autorisé"}
        
        if invoice.status == "paid":
            return {"error": "Cette facture est déjà payée"}
        
        # Calculate amount to pay (remaining due)
        amount_due = float(invoice.amount_due or invoice.total_ttc or 0)
        
        if amount_due <= 0:
            return {"error": "Aucun montant à payer"}
        
        # Initialize Stripe
        webhook_url = f"{base_url}/api/payments/webhook"
        stripe_checkout = StripeCheckout(api_key=self.api_key, webhook_url=webhook_url)
        
        # Build URLs
        success_url = f"{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}&invoice_id={invoice_id}"
        cancel_url = f"{base_url}/payment/cancel?invoice_id={invoice_id}"
        
        # Create checkout session
        checkout_request = CheckoutSessionRequest(
            amount=amount_due,
            currency="eur",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "invoice_id": invoice_id,
                "invoice_number": invoice.invoice_number or "",
                "user_id": user_id,
                "type": "invoice_payment"
            }
        )
        
        try:
            session = await stripe_checkout.create_checkout_session(checkout_request)
            
            # Store payment intent in database
            payment = Payment(
                id=generate_uuid(),
                user_id=user_id,
                invoice_id=invoice_id,
                amount=amount_due,
                payment_date=datetime.now(timezone.utc),
                payment_method="stripe",
                reference=session.session_id,
                notes=f"Stripe checkout: {session.session_id}",
                stripe_session_id=session.session_id,
                stripe_status="pending",
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(payment)
            await self.db.flush()
            
            return {
                "url": session.url,
                "session_id": session.session_id,
                "amount": amount_due,
                "currency": "EUR"
            }
            
        except Exception as e:
            logger.error(f"Stripe checkout error: {e}")
            return {"error": f"Erreur Stripe: {str(e)}"}
    
    async def check_payment_status(self, session_id: str) -> Dict[str, Any]:
        """Check the status of a Stripe checkout session"""
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        
        stripe_checkout = StripeCheckout(api_key=self.api_key, webhook_url="")
        
        try:
            status = await stripe_checkout.get_checkout_status(session_id)
            
            # Update payment record if completed
            if status.payment_status == "paid":
                await self._complete_payment(session_id, status)
            
            return {
                "status": status.status,
                "payment_status": status.payment_status,
                "amount": status.amount_total / 100,  # Convert from cents
                "currency": status.currency.upper(),
                "metadata": status.metadata
            }
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {"error": str(e)}
    
    async def _complete_payment(self, session_id: str, status) -> bool:
        """Mark payment as completed and update invoice"""
        # Find the payment record
        result = await self.db.execute(
            select(Payment).where(Payment.stripe_session_id == session_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            return False
        
        # Check if already processed
        if payment.stripe_status == "paid":
            return True
        
        # Update payment
        payment.stripe_status = "paid"
        payment.payment_date = datetime.now(timezone.utc)
        
        # Update invoice
        invoice_result = await self.db.execute(
            select(Invoice).where(Invoice.id == payment.invoice_id)
        )
        invoice = invoice_result.scalar_one_or_none()
        
        if invoice:
            invoice.amount_paid = (invoice.amount_paid or 0) + payment.amount
            invoice.amount_due = invoice.total_ttc - invoice.amount_paid
            
            if invoice.amount_paid >= invoice.total_ttc:
                invoice.status = "paid"
                invoice.paid_date = datetime.now(timezone.utc)
            else:
                invoice.status = "partial"
            
            invoice.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        return True
    
    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook"""
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        
        stripe_checkout = StripeCheckout(api_key=self.api_key, webhook_url="")
        
        try:
            event = await stripe_checkout.handle_webhook(payload, signature)
            
            if event.payment_status == "paid":
                await self._complete_payment(event.session_id, event)
            
            return {
                "event_type": event.event_type,
                "session_id": event.session_id,
                "status": event.payment_status
            }
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {"error": str(e)}


def get_stripe_payment_service(db: AsyncSession) -> StripePaymentService:
    """Factory function"""
    return StripePaymentService(db)
