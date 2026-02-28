"""
Stripe Service for BTP Facture
Handles Stripe checkout sessions, webhooks, and subscription management
"""

import os
import logging
import stripe
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.plans_service import PLANS_CONFIG, get_plans_service, get_stripe_price_ids

logger = logging.getLogger(__name__)

# Initialize Stripe
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

stripe.api_key = STRIPE_API_KEY


class StripeService:
    """Service for Stripe integration"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db.users
        self.plans_service = get_plans_service(db)
    
    async def create_checkout_session(
        self,
        user_id: str,
        plan: str,
        billing_period: str,  # "monthly" or "yearly"
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create a Stripe Checkout session for subscription"""
        
        # Validate plan
        if plan not in ["essentiel", "pro", "business"]:
            raise ValueError(f"Invalid plan: {plan}")
        
        plan_config = PLANS_CONFIG.get(plan)
        if not plan_config:
            raise ValueError(f"Plan config not found: {plan}")
        
        # Get price ID from environment
        price_ids = get_stripe_price_ids()
        plan_prices = price_ids.get(plan)
        if not plan_prices:
            raise ValueError(f"No price configuration for plan: {plan}")
        
        price_id = plan_prices.get(billing_period)
        if not price_id:
            raise ValueError(f"No price ID for {plan} {billing_period}")
        
        # Get user
        user = await self.users.find_one({"id": user_id})
        if not user:
            raise ValueError("User not found")
        
        # Check if user already has a Stripe customer
        customer_id = user.get("stripe_customer_id")
        
        try:
            # Create or retrieve customer
            if customer_id:
                try:
                    customer = stripe.Customer.retrieve(customer_id)
                except stripe.error.InvalidRequestError:
                    customer = None
                    customer_id = None
            
            if not customer_id:
                customer = stripe.Customer.create(
                    email=user.get("email"),
                    name=user.get("name"),
                    metadata={
                        "user_id": user_id,
                        "company_name": user.get("company_name", "")
                    }
                )
                customer_id = customer.id
                
                # Save customer ID
                await self.users.update_one(
                    {"id": user_id},
                    {"$set": {"stripe_customer_id": customer_id}}
                )
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                mode="subscription",
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1
                }],
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}&success=true",
                cancel_url=f"{cancel_url}?canceled=true",
                metadata={
                    "user_id": user_id,
                    "plan": plan,
                    "billing_period": billing_period
                },
                subscription_data={
                    "metadata": {
                        "user_id": user_id,
                        "plan": plan
                    }
                },
                allow_promotion_codes=True,
                billing_address_collection="required",
                locale="fr"
            )
            
            logger.info(f"Checkout session created: {session.id} for user {user_id}, plan {plan}")
            
            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "plan": plan,
                "billing_period": billing_period
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout: {e}")
            raise Exception(f"Erreur Stripe: {str(e)}")
    
    async def check_session_status(self, session_id: str) -> Dict[str, Any]:
        """Check the status of a checkout session"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            return {
                "session_id": session.id,
                "payment_status": session.payment_status,
                "status": session.status,
                "customer_id": session.customer,
                "subscription_id": session.subscription,
                "plan": session.metadata.get("plan"),
                "plan_name": PLANS_CONFIG.get(session.metadata.get("plan", ""), {}).get("name", "Unknown")
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error checking session: {e}")
            raise Exception(f"Erreur Stripe: {str(e)}")
    
    async def handle_webhook_event(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Handle incoming Stripe webhook event"""
        
        try:
            # Verify webhook signature if secret is set
            if STRIPE_WEBHOOK_SECRET:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, STRIPE_WEBHOOK_SECRET
                )
            else:
                # For testing without signature verification
                import json
                event = stripe.Event.construct_from(
                    json.loads(payload), stripe.api_key
                )
            
            event_type = event["type"]
            data = event["data"]["object"]
            
            logger.info(f"Webhook received: {event_type}")
            
            # Handle different event types
            if event_type == "checkout.session.completed":
                return await self._handle_checkout_completed(data)
            
            elif event_type == "invoice.paid":
                return await self._handle_invoice_paid(data)
            
            elif event_type == "invoice.payment_failed":
                return await self._handle_payment_failed(data)
            
            elif event_type == "customer.subscription.deleted":
                return await self._handle_subscription_deleted(data)
            
            elif event_type == "customer.subscription.updated":
                return await self._handle_subscription_updated(data)
            
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
                return {"handled": False, "event_type": event_type}
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise Exception("Invalid signature")
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            raise
    
    async def _handle_checkout_completed(self, session: Dict) -> Dict[str, Any]:
        """Handle checkout.session.completed event"""
        user_id = session.get("metadata", {}).get("user_id")
        plan = session.get("metadata", {}).get("plan")
        billing_cycle = session.get("metadata", {}).get("billing_period", "monthly")
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")
        
        if not user_id or not plan:
            logger.warning("Missing user_id or plan in checkout session")
            return {"handled": False, "reason": "missing_metadata"}
        
        # Get subscription details for period end
        current_period_end = None
        if subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                current_period_end = datetime.fromtimestamp(
                    subscription.current_period_end, tz=timezone.utc
                ).isoformat()
            except Exception as e:
                logger.warning(f"Could not retrieve subscription: {e}")
        
        # Activate subscription with billing cycle
        success = await self.plans_service.activate_subscription(
            user_id=user_id,
            plan=plan,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            current_period_end=current_period_end,
            billing_cycle=billing_cycle
        )
        
        logger.info(f"Checkout completed: user={user_id}, plan={plan}, cycle={billing_cycle}, success={success}")
        
        return {
            "handled": True,
            "event": "checkout_completed",
            "user_id": user_id,
            "plan": plan,
            "billing_cycle": billing_cycle,
            "success": success
        }
    
    async def _handle_invoice_paid(self, invoice: Dict) -> Dict[str, Any]:
        """Handle invoice.paid event (subscription renewal)"""
        subscription_id = invoice.get("subscription")
        customer_id = invoice.get("customer")
        
        if not subscription_id:
            return {"handled": False, "reason": "no_subscription"}
        
        # Find user by subscription ID
        user = await self.users.find_one({"stripe_subscription_id": subscription_id})
        if not user:
            # Try by customer ID
            user = await self.users.find_one({"stripe_customer_id": customer_id})
        
        if not user:
            logger.warning(f"User not found for subscription {subscription_id}")
            return {"handled": False, "reason": "user_not_found"}
        
        # Get new period end
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            current_period_end = datetime.fromtimestamp(
                subscription.current_period_end, tz=timezone.utc
            ).isoformat()
        except Exception as e:
            logger.warning(f"Could not retrieve subscription: {e}")
            current_period_end = None
        
        # Renew subscription
        success = await self.plans_service.renew_subscription(
            user["id"],
            current_period_end
        )
        
        logger.info(f"Invoice paid: user={user['id']}, renewed={success}")
        
        return {
            "handled": True,
            "event": "invoice_paid",
            "user_id": user["id"],
            "success": success
        }
    
    async def _handle_payment_failed(self, invoice: Dict) -> Dict[str, Any]:
        """Handle invoice.payment_failed event"""
        subscription_id = invoice.get("subscription")
        customer_id = invoice.get("customer")
        
        if not subscription_id:
            return {"handled": False, "reason": "no_subscription"}
        
        # Find user
        user = await self.users.find_one({"stripe_subscription_id": subscription_id})
        if not user:
            user = await self.users.find_one({"stripe_customer_id": customer_id})
        
        if not user:
            logger.warning(f"User not found for subscription {subscription_id}")
            return {"handled": False, "reason": "user_not_found"}
        
        # Mark as past due
        success = await self.plans_service.handle_payment_failed(user["id"])
        
        logger.info(f"Payment failed: user={user['id']}, marked_past_due={success}")
        
        return {
            "handled": True,
            "event": "payment_failed",
            "user_id": user["id"],
            "success": success
        }
    
    async def _handle_subscription_deleted(self, subscription: Dict) -> Dict[str, Any]:
        """Handle customer.subscription.deleted event"""
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")
        
        # Find user
        user = await self.users.find_one({"stripe_subscription_id": subscription_id})
        if not user:
            user = await self.users.find_one({"stripe_customer_id": customer_id})
        
        if not user:
            logger.warning(f"User not found for subscription {subscription_id}")
            return {"handled": False, "reason": "user_not_found"}
        
        # Expire subscription
        success = await self.plans_service.expire_subscription(user["id"])
        
        logger.info(f"Subscription deleted: user={user['id']}, expired={success}")
        
        return {
            "handled": True,
            "event": "subscription_deleted",
            "user_id": user["id"],
            "success": success
        }
    
    async def _handle_subscription_updated(self, subscription: Dict) -> Dict[str, Any]:
        """Handle customer.subscription.updated event"""
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")
        status = subscription.get("status")
        
        # Find user
        user = await self.users.find_one({"stripe_subscription_id": subscription_id})
        if not user:
            user = await self.users.find_one({"stripe_customer_id": customer_id})
        
        if not user:
            logger.warning(f"User not found for subscription {subscription_id}")
            return {"handled": False, "reason": "user_not_found"}
        
        # Update based on status
        if status == "active":
            current_period_end = datetime.fromtimestamp(
                subscription.get("current_period_end", 0), tz=timezone.utc
            ).isoformat()
            await self.plans_service.renew_subscription(user["id"], current_period_end)
        elif status == "canceled":
            await self.plans_service.cancel_subscription(user["id"])
        elif status == "past_due":
            await self.plans_service.handle_payment_failed(user["id"])
        
        logger.info(f"Subscription updated: user={user['id']}, status={status}")
        
        return {
            "handled": True,
            "event": "subscription_updated",
            "user_id": user["id"],
            "status": status
        }
    
    async def cancel_subscription(self, user_id: str) -> Dict[str, Any]:
        """Cancel a user's subscription"""
        user = await self.users.find_one({"id": user_id})
        if not user:
            raise ValueError("User not found")
        
        subscription_id = user.get("stripe_subscription_id")
        if not subscription_id:
            raise ValueError("No active subscription")
        
        try:
            # Cancel at period end (not immediately)
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            
            # Update local status
            await self.plans_service.cancel_subscription(user_id)
            
            logger.info(f"Subscription canceled: user={user_id}")
            
            return {
                "success": True,
                "cancel_at": datetime.fromtimestamp(
                    subscription.current_period_end, tz=timezone.utc
                ).isoformat()
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error canceling subscription: {e}")
            raise Exception(f"Erreur Stripe: {str(e)}")
    
    async def get_customer_portal_url(self, user_id: str, return_url: str) -> str:
        """Create a Stripe Customer Portal session"""
        user = await self.users.find_one({"id": user_id})
        if not user:
            raise ValueError("User not found")
        
        customer_id = user.get("stripe_customer_id")
        if not customer_id:
            raise ValueError("No Stripe customer")
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Error creating portal session: {e}")
            raise Exception(f"Erreur Stripe: {str(e)}")


def get_stripe_service(db: AsyncIOMotorDatabase) -> StripeService:
    """Factory function"""
    return StripeService(db)
