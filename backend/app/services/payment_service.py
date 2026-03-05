"""
Payment Service
Stripe payment integration for invoices
"""
import stripe
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY

class PaymentService:
    """Service for handling payments via Stripe"""
    
    @staticmethod
    async def create_checkout_session(invoice_id: str, user_id: str,
                                       success_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create a Stripe checkout session for invoice payment"""
        from app.core.database import db, is_mongodb
        
        if not settings.STRIPE_API_KEY:
            raise ValueError("Stripe n'est pas configuré")
        
        # Get invoice
        if is_mongodb():
            invoice = await db.invoices.find_one(
                {"id": invoice_id, "user_id": user_id},
                {"_id": 0}
            )
            if not invoice:
                raise ValueError("Facture non trouvée")
            
            # Get client
            client = None
            if invoice.get("client_id"):
                client = await db.clients.find_one({"id": invoice["client_id"]}, {"_id": 0})
            
            # Get company settings
            user_settings = await db.user_settings.find_one({"user_id": user_id}, {"_id": 0})
        else:
            raise ValueError("Base de données non disponible")
        
        # Check if already paid
        if invoice.get("status") == "paid":
            raise ValueError("Cette facture est déjà payée")
        
        # Calculate amount to pay (in cents)
        amount_due = invoice.get("amount_due", 0)
        if amount_due <= 0:
            raise ValueError("Aucun montant à payer")
        
        amount_cents = int(amount_due * 100)
        
        # Create Stripe checkout session
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": f"Facture {invoice.get('invoice_number')}",
                            "description": invoice.get("title") or f"Paiement facture {invoice.get('invoice_number')}"
                        }
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                customer_email=client.get("email") if client else None,
                metadata={
                    "invoice_id": invoice_id,
                    "user_id": user_id,
                    "invoice_number": invoice.get("invoice_number")
                }
            )
            
            # Store session ID on invoice
            if is_mongodb():
                await db.invoices.update_one(
                    {"id": invoice_id},
                    {"$set": {"stripe_checkout_session_id": session.id}}
                )
            
            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "amount": amount_due
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise ValueError(f"Erreur Stripe: {str(e)}")
    
    @staticmethod
    async def handle_checkout_completed(session_id: str) -> Dict[str, Any]:
        """Handle completed checkout session"""
        from app.core.database import db, is_mongodb
        from app.services.invoice_service import invoice_service
        
        if not settings.STRIPE_API_KEY:
            raise ValueError("Stripe n'est pas configuré")
        
        try:
            # Retrieve session from Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status != "paid":
                raise ValueError("Le paiement n'est pas complété")
            
            invoice_id = session.metadata.get("invoice_id")
            user_id = session.metadata.get("user_id")
            
            if not invoice_id or not user_id:
                raise ValueError("Métadonnées de session invalides")
            
            # Get payment amount
            amount = session.amount_total / 100  # Convert from cents
            
            # Record payment
            result = await invoice_service.record_payment(
                invoice_id=invoice_id,
                user_id=user_id,
                amount=amount,
                payment_method="stripe",
                stripe_payment_id=session.payment_intent
            )
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "amount_paid": amount,
                "payment_intent": session.payment_intent,
                **result
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error verifying session: {e}")
            raise ValueError(f"Erreur de vérification Stripe: {str(e)}")
    
    @staticmethod
    async def create_payment_intent(invoice_id: str, user_id: str) -> Dict[str, Any]:
        """Create a payment intent for client-side payment"""
        from app.core.database import db, is_mongodb
        
        if not settings.STRIPE_API_KEY:
            raise ValueError("Stripe n'est pas configuré")
        
        # Get invoice
        if is_mongodb():
            invoice = await db.invoices.find_one(
                {"id": invoice_id, "user_id": user_id},
                {"_id": 0}
            )
            if not invoice:
                raise ValueError("Facture non trouvée")
        else:
            raise ValueError("Base de données non disponible")
        
        amount_due = invoice.get("amount_due", 0)
        if amount_due <= 0:
            raise ValueError("Aucun montant à payer")
        
        amount_cents = int(amount_due * 100)
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="eur",
                metadata={
                    "invoice_id": invoice_id,
                    "user_id": user_id,
                    "invoice_number": invoice.get("invoice_number")
                }
            )
            
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": amount_due
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            raise ValueError(f"Erreur Stripe: {str(e)}")
    
    @staticmethod
    async def verify_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """Verify a payment intent and record payment if successful"""
        from app.services.invoice_service import invoice_service
        
        if not settings.STRIPE_API_KEY:
            raise ValueError("Stripe n'est pas configuré")
        
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status != "succeeded":
                return {
                    "success": False,
                    "status": intent.status,
                    "message": "Le paiement n'est pas complété"
                }
            
            invoice_id = intent.metadata.get("invoice_id")
            user_id = intent.metadata.get("user_id")
            
            if not invoice_id or not user_id:
                raise ValueError("Métadonnées invalides")
            
            amount = intent.amount / 100
            
            result = await invoice_service.record_payment(
                invoice_id=invoice_id,
                user_id=user_id,
                amount=amount,
                payment_method="stripe",
                stripe_payment_id=payment_intent_id
            )
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "amount_paid": amount,
                **result
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error verifying payment: {e}")
            raise ValueError(f"Erreur Stripe: {str(e)}")


# Create singleton instance
payment_service = PaymentService()
