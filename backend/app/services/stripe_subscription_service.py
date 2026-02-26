"""
Subscription Service for BTP Facture
Manages Stripe subscriptions, feature gating, and plan management
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

# ============== SUBSCRIPTION PLANS ==============

class PlanType(str, Enum):
    TRIAL_PENDING = "trial_pending"
    TRIAL = "trial"
    ESSENTIEL = "essentiel"
    PRO = "pro"
    BUSINESS = "business"
    EXPIRED = "expired"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


# Plan configuration with pricing and features
PLANS = {
    "essentiel": {
        "name": "Essentiel",
        "price_monthly": 19.00,
        "stripe_price_id": "essentiel_monthly",
        "features": {
            "unlimited_quotes": True,
            "max_invoices_per_month": 30,
            "basic_article_library": True,
            "manual_line_creation": True,
            "max_users": 1,
            "predefined_kits": False,
            "smart_pricing": False,
            "advanced_dashboard": False,
            "priority_support": False,
        },
        "description": "Pour les artisans débutants"
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 29.00,
        "stripe_price_id": "pro_monthly",
        "features": {
            "unlimited_quotes": True,
            "max_invoices_per_month": -1,  # Unlimited
            "basic_article_library": True,
            "manual_line_creation": True,
            "max_users": 1,
            "predefined_kits": True,
            "smart_pricing": True,
            "advanced_dashboard": False,
            "priority_support": False,
        },
        "description": "Pour les professionnels actifs"
    },
    "business": {
        "name": "Business",
        "price_monthly": 59.00,
        "stripe_price_id": "business_monthly",
        "features": {
            "unlimited_quotes": True,
            "max_invoices_per_month": -1,  # Unlimited
            "basic_article_library": True,
            "manual_line_creation": True,
            "max_users": 10,  # Multi-user
            "predefined_kits": True,
            "smart_pricing": True,
            "advanced_dashboard": True,
            "priority_support": True,
        },
        "description": "Pour les entreprises en croissance"
    },
    # Trial grants PRO-level access
    "trial": {
        "name": "Essai gratuit",
        "price_monthly": 0,
        "stripe_price_id": None,
        "features": {
            "unlimited_quotes": True,
            "max_invoices_per_month": 9,  # Trial limit
            "basic_article_library": True,
            "manual_line_creation": True,
            "max_users": 1,
            "predefined_kits": True,
            "smart_pricing": True,
            "advanced_dashboard": False,
            "priority_support": False,
        },
        "description": "14 jours d'essai gratuit"
    }
}


# ============== MODELS ==============

class PlanInfo(BaseModel):
    plan: str
    name: str
    price_monthly: float
    features: Dict[str, Any]
    description: str


class SubscriptionInfo(BaseModel):
    plan: str
    plan_name: str
    status: str
    is_active: bool
    is_trial: bool
    trial_end_date: Optional[str] = None
    trial_days_remaining: Optional[int] = None
    current_period_end: Optional[str] = None
    subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    can_create_invoices: bool
    can_create_quotes: bool
    invoices_this_month: int
    invoices_limit: int
    features: Dict[str, Any]


class FeatureAccess(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    upgrade_required: bool = False
    upgrade_plan: Optional[str] = None


# ============== SUBSCRIPTION SERVICE ==============

class StripeSubscriptionService:
    """Service for managing subscriptions and feature gating"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db.users
        self.invoices = db.invoices
        self.payment_transactions = db.payment_transactions
    
    # ============== PLAN HELPERS ==============
    
    def get_plan_config(self, plan: str) -> Dict[str, Any]:
        """Get plan configuration"""
        return PLANS.get(plan, PLANS["essentiel"])
    
    def get_all_plans(self) -> List[Dict[str, Any]]:
        """Get all available plans for display"""
        return [
            {
                "id": plan_id,
                **config
            }
            for plan_id, config in PLANS.items()
            if plan_id not in ["trial", "trial_pending", "expired"]
        ]
    
    def get_plan_features(self, plan: str) -> Dict[str, Any]:
        """Get features for a plan"""
        config = self.get_plan_config(plan)
        return config.get("features", {})
    
    # ============== USER SUBSCRIPTION STATUS ==============
    
    async def get_user_subscription(self, user_id: str) -> SubscriptionInfo:
        """Get complete subscription status for a user"""
        user = await self.users.find_one({"id": user_id})
        if not user:
            raise ValueError("User not found")
        
        plan = user.get("plan", "trial_pending")
        subscription_status = user.get("subscription_status", "")
        
        # Determine if trial
        is_trial = plan in ["trial", "trial_pending"]
        trial_end_date = user.get("trial_end")
        trial_days_remaining = None
        
        if trial_end_date:
            if isinstance(trial_end_date, str):
                trial_end = datetime.fromisoformat(trial_end_date.replace("Z", "+00:00"))
            else:
                trial_end = trial_end_date
            
            now = datetime.now(timezone.utc)
            if trial_end > now:
                trial_days_remaining = (trial_end - now).days
            else:
                trial_days_remaining = 0
        
        # Check if subscription is active
        is_active = self._is_subscription_active(user)
        
        # Get invoice count this month
        invoices_this_month = await self._count_invoices_this_month(user_id)
        
        # Get plan config
        effective_plan = plan if plan in PLANS else "essentiel"
        plan_config = self.get_plan_config(effective_plan)
        features = plan_config.get("features", {})
        
        # Calculate invoice limit
        invoices_limit = features.get("max_invoices_per_month", 30)
        if invoices_limit == -1:
            invoices_limit = 999999  # Effectively unlimited
        
        # Can create invoices/quotes
        can_create_invoices = is_active and (invoices_limit == 999999 or invoices_this_month < invoices_limit)
        can_create_quotes = is_active
        
        return SubscriptionInfo(
            plan=plan,
            plan_name=plan_config.get("name", plan),
            status=subscription_status or ("active" if is_active else "inactive"),
            is_active=is_active,
            is_trial=is_trial,
            trial_end_date=trial_end_date if isinstance(trial_end_date, str) else (trial_end_date.isoformat() if trial_end_date else None),
            trial_days_remaining=trial_days_remaining,
            current_period_end=user.get("current_period_end"),
            subscription_id=user.get("stripe_subscription_id"),
            stripe_customer_id=user.get("stripe_customer_id"),
            can_create_invoices=can_create_invoices,
            can_create_quotes=can_create_quotes,
            invoices_this_month=invoices_this_month,
            invoices_limit=invoices_limit if invoices_limit != 999999 else -1,
            features=features
        )
    
    def _is_subscription_active(self, user: Dict) -> bool:
        """Check if user has active subscription or valid trial"""
        plan = user.get("plan", "trial_pending")
        subscription_status = user.get("subscription_status")
        
        # Check paid subscription
        if subscription_status in ["active", "trialing"]:
            return True
        
        # Check trial
        if plan in ["trial", "trial_pending"]:
            trial_end = user.get("trial_end")
            if trial_end:
                if isinstance(trial_end, str):
                    trial_end = datetime.fromisoformat(trial_end.replace("Z", "+00:00"))
                
                if trial_end > datetime.now(timezone.utc):
                    return True
        
        # Check if plan is paid and not canceled
        if plan in ["essentiel", "pro", "business"] and subscription_status != "canceled":
            return True
        
        return False
    
    async def _count_invoices_this_month(self, user_id: str) -> int:
        """Count invoices created this month"""
        now = datetime.now(timezone.utc)
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        count = await self.invoices.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": first_of_month.isoformat()}
        })
        
        return count
    
    # ============== FEATURE GATING ==============
    
    async def check_feature_access(self, user_id: str, feature: str) -> FeatureAccess:
        """Check if user has access to a specific feature"""
        try:
            subscription = await self.get_user_subscription(user_id)
        except ValueError:
            return FeatureAccess(
                allowed=False,
                reason="Utilisateur non trouvé",
                upgrade_required=False
            )
        
        if not subscription.is_active:
            return FeatureAccess(
                allowed=False,
                reason="Abonnement inactif ou période d'essai expirée",
                upgrade_required=True,
                upgrade_plan="essentiel"
            )
        
        features = subscription.features
        
        # Special case for invoice creation - check monthly limit
        if feature == "create_invoice":
            if not subscription.can_create_invoices:
                if subscription.invoices_limit != -1 and subscription.invoices_this_month >= subscription.invoices_limit:
                    return FeatureAccess(
                        allowed=False,
                        reason=f"Limite de {subscription.invoices_limit} factures/mois atteinte",
                        upgrade_required=True,
                        upgrade_plan="pro" if subscription.plan == "essentiel" else "business"
                    )
                else:
                    return FeatureAccess(
                        allowed=False,
                        reason="Abonnement requis pour créer des factures",
                        upgrade_required=True,
                        upgrade_plan="essentiel"
                    )
            return FeatureAccess(allowed=True)
        
        # Special case for quote creation
        if feature == "create_quote":
            if not subscription.can_create_quotes:
                return FeatureAccess(
                    allowed=False,
                    reason="Abonnement requis pour créer des devis",
                    upgrade_required=True,
                    upgrade_plan="essentiel"
                )
            return FeatureAccess(allowed=True)
        
        # Check feature flags
        feature_value = features.get(feature)
        
        if feature_value is None:
            return FeatureAccess(allowed=True)  # Unknown feature, allow by default
        
        if isinstance(feature_value, bool):
            if feature_value:
                return FeatureAccess(allowed=True)
            else:
                # Determine upgrade plan
                upgrade_plan = "pro" if subscription.plan == "essentiel" else "business"
                return FeatureAccess(
                    allowed=False,
                    reason=f"Fonctionnalité non disponible avec le plan {subscription.plan_name}",
                    upgrade_required=True,
                    upgrade_plan=upgrade_plan
                )
        
        return FeatureAccess(allowed=True)
    
    async def can_use_kits(self, user_id: str) -> bool:
        """Check if user can use predefined kits"""
        access = await self.check_feature_access(user_id, "predefined_kits")
        return access.allowed
    
    async def can_use_smart_pricing(self, user_id: str) -> bool:
        """Check if user can use smart pricing"""
        access = await self.check_feature_access(user_id, "smart_pricing")
        return access.allowed
    
    async def can_manage_users(self, user_id: str) -> bool:
        """Check if user can manage multiple users (Business only)"""
        subscription = await self.get_user_subscription(user_id)
        return subscription.plan == "business"
    
    # ============== SUBSCRIPTION MANAGEMENT ==============
    
    async def activate_subscription(
        self,
        user_id: str,
        plan: str,
        stripe_subscription_id: str,
        stripe_customer_id: str,
        current_period_end: Optional[str] = None
    ) -> bool:
        """Activate a subscription after successful Stripe payment"""
        if plan not in ["essentiel", "pro", "business"]:
            logger.error(f"Invalid plan: {plan}")
            return False
        
        update_data = {
            "plan": plan,
            "subscription_status": "active",
            "stripe_subscription_id": stripe_subscription_id,
            "stripe_customer_id": stripe_customer_id,
            "current_period_end": current_period_end,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Reset trial fields since user is now subscribed
        update_data["trial_end"] = None
        
        # Set invoice limit based on plan
        plan_config = self.get_plan_config(plan)
        update_data["invoice_limit"] = plan_config["features"].get("max_invoices_per_month", 30)
        
        result = await self.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Subscription activated for user {user_id}: {plan}")
            return True
        
        return False
    
    async def cancel_subscription(self, user_id: str) -> bool:
        """Cancel subscription (will end at period end)"""
        result = await self.users.update_one(
            {"id": user_id},
            {"$set": {
                "subscription_status": "canceled",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count > 0:
            logger.info(f"Subscription canceled for user {user_id}")
            return True
        
        return False
    
    async def handle_subscription_renewed(
        self,
        user_id: str,
        current_period_end: str
    ) -> bool:
        """Handle successful subscription renewal"""
        result = await self.users.update_one(
            {"id": user_id},
            {"$set": {
                "subscription_status": "active",
                "current_period_end": current_period_end,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return result.modified_count > 0
    
    async def handle_payment_failed(self, user_id: str) -> bool:
        """Handle failed payment"""
        result = await self.users.update_one(
            {"id": user_id},
            {"$set": {
                "subscription_status": "past_due",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return result.modified_count > 0
    
    async def upgrade_subscription(
        self,
        user_id: str,
        new_plan: str,
        stripe_subscription_id: str
    ) -> bool:
        """Upgrade to a higher plan (immediate)"""
        current_user = await self.users.find_one({"id": user_id})
        if not current_user:
            return False
        
        current_plan = current_user.get("plan")
        plan_order = ["trial", "trial_pending", "essentiel", "pro", "business"]
        
        # Check if it's actually an upgrade
        current_idx = plan_order.index(current_plan) if current_plan in plan_order else 0
        new_idx = plan_order.index(new_plan) if new_plan in plan_order else 0
        
        if new_idx <= current_idx:
            logger.warning(f"Not an upgrade: {current_plan} -> {new_plan}")
            # Still allow, Stripe handles proration
        
        return await self.activate_subscription(
            user_id,
            new_plan,
            stripe_subscription_id,
            current_user.get("stripe_customer_id", ""),
            current_user.get("current_period_end")
        )
    
    async def downgrade_subscription(self, user_id: str, new_plan: str) -> bool:
        """Schedule downgrade for next billing cycle"""
        # Just mark as pending downgrade - Stripe handles actual downgrade
        result = await self.users.update_one(
            {"id": user_id},
            {"$set": {
                "pending_downgrade": new_plan,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return result.modified_count > 0


def get_stripe_subscription_service(db: AsyncIOMotorDatabase) -> StripeSubscriptionService:
    """Factory function for StripeSubscriptionService"""
    return StripeSubscriptionService(db)
