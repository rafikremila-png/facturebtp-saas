"""
Plans Service for BTP Facture SaaS
Handles subscription plans, limits, and feature gating
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from enum import Enum

logger = logging.getLogger(__name__)

# ============== PLAN DEFINITIONS ==============

class PlanType(str, Enum):
    TRIAL = "trial"
    ESSENTIEL = "essentiel"
    PRO = "pro"
    BUSINESS = "business"


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


# Load Stripe Price IDs from environment
def get_stripe_price_ids():
    """Load Stripe Price IDs from environment variables"""
    return {
        "essentiel": {
            "monthly": os.environ.get("STRIPE_PRICE_ESSENTIEL_MONTHLY"),
            "yearly": os.environ.get("STRIPE_PRICE_ESSENTIEL_YEARLY"),
        },
        "pro": {
            "monthly": os.environ.get("STRIPE_PRICE_PRO_MONTHLY"),
            "yearly": os.environ.get("STRIPE_PRICE_PRO_YEARLY"),
        },
        "business": {
            "monthly": os.environ.get("STRIPE_PRICE_BUSINESS_MONTHLY"),
            "yearly": os.environ.get("STRIPE_PRICE_BUSINESS_YEARLY"),
        },
    }


# Plan configuration with pricing and features
PLANS_CONFIG = {
    "essentiel": {
        "name": "Essentiel",
        "description": "Pour les artisans débutants",
        "price_monthly": 19.00,
        "price_yearly": 182.40,  # 19 * 12 * 0.8 = 20% discount
        "limits": {
            "quotes_per_month": 30,
            "invoices_per_month": 30,
            "max_users": 1,
        },
        "features": {
            "pdf_export": True,
            "full_article_library": True,
            "email_support": True,
            "automatic_reminders": False,
            "csv_export": False,
            "priority_support": False,
            "branding_customization": False,
            "api_access": False,
        },
        "highlight": False,
        "badge": None,
    },
    "pro": {
        "name": "Pro",
        "description": "Pour les professionnels actifs",
        "price_monthly": 29.00,
        "price_yearly": 278.40,  # 29 * 12 * 0.8 = 20% discount
        "limits": {
            "quotes_per_month": -1,  # Unlimited
            "invoices_per_month": -1,  # Unlimited
            "max_users": 3,
        },
        "features": {
            "pdf_export": True,
            "full_article_library": True,
            "email_support": True,
            "automatic_reminders": True,
            "csv_export": True,
            "priority_support": True,
            "branding_customization": False,
            "api_access": False,
        },
        "highlight": True,
        "badge": "Le plus populaire",
    },
    "business": {
        "name": "Business",
        "description": "Pour les entreprises en croissance",
        "price_monthly": 59.00,
        "price_yearly": 566.40,  # 59 * 12 * 0.8 = 20% discount
        "limits": {
            "quotes_per_month": -1,  # Unlimited
            "invoices_per_month": -1,  # Unlimited
            "max_users": 5,  # 5 users for Business
        },
        "features": {
            "pdf_export": True,
            "full_article_library": True,
            "email_support": True,
            "automatic_reminders": True,
            "csv_export": True,
            "priority_support": True,
            "branding_customization": True,
            "api_access": True,
        },
        "highlight": False,
        "badge": "Entreprise",
    },
    "trial": {
        "name": "Essai gratuit",
        "description": "14 jours d'essai gratuit",
        "price_monthly": 0,
        "price_yearly": 0,
        "limits": {
            "quotes_per_month": 9,  # Total during trial, not monthly
            "invoices_per_month": 9,  # Total during trial, not monthly
            "max_users": 1,
        },
        "features": {
            "pdf_export": True,
            "full_article_library": True,
            "email_support": True,
            "automatic_reminders": False,
            "csv_export": False,
            "priority_support": False,
            "branding_customization": False,
            "api_access": False,
        },
        "highlight": False,
        "badge": None,
    },
}

# Feature labels for display
FEATURE_LABELS = {
    "pdf_export": "Export PDF",
    "full_article_library": "Bibliothèque d'articles complète",
    "email_support": "Support email",
    "automatic_reminders": "Relances automatiques impayés",
    "csv_export": "Export comptable CSV",
    "priority_support": "Support prioritaire",
    "branding_customization": "Personnalisation marque",
    "api_access": "Accès API (bientôt)",
}

TRIAL_DURATION_DAYS = 14


class PlansService:
    """Service for managing subscription plans and usage"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db.users
        self.invoices = db.invoices
        self.quotes = db.quotes
    
    # ============== PLAN CONFIGURATION ==============
    
    def get_plan_config(self, plan: str) -> Dict[str, Any]:
        """Get configuration for a specific plan"""
        return PLANS_CONFIG.get(plan, PLANS_CONFIG["essentiel"])
    
    def get_all_plans(self, include_trial: bool = False) -> List[Dict[str, Any]]:
        """Get all available plans for display"""
        plans = []
        for plan_id, config in PLANS_CONFIG.items():
            if plan_id == "trial" and not include_trial:
                continue
            plans.append({
                "id": plan_id,
                **config
            })
        return plans
    
    def get_plan_limits(self, plan: str) -> Dict[str, int]:
        """Get limits for a plan"""
        config = self.get_plan_config(plan)
        return config.get("limits", {})
    
    def get_plan_features(self, plan: str) -> Dict[str, bool]:
        """Get features for a plan"""
        config = self.get_plan_config(plan)
        return config.get("features", {})
    
    def get_stripe_price_id(self, plan: str, billing_period: str = "monthly") -> Optional[str]:
        """Get Stripe Price ID for a plan and billing period from environment"""
        price_ids = get_stripe_price_ids()
        plan_prices = price_ids.get(plan)
        if not plan_prices:
            return None
        return plan_prices.get(billing_period)
    
    # ============== MONTHLY USAGE TRACKING ==============
    
    def _get_current_month_range(self) -> tuple:
        """Get start and end of current calendar month"""
        now = datetime.now(timezone.utc)
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate last day of month
        if now.month == 12:
            next_month = first_of_month.replace(year=now.year + 1, month=1)
        else:
            next_month = first_of_month.replace(month=now.month + 1)
        
        return first_of_month, next_month
    
    async def get_monthly_invoice_count(self, user_id: str) -> int:
        """Count invoices created in current calendar month"""
        first_of_month, next_month = self._get_current_month_range()
        
        count = await self.invoices.count_documents({
            "owner_id": user_id,
            "created_at": {
                "$gte": first_of_month.isoformat(),
                "$lt": next_month.isoformat()
            }
        })
        return count
    
    async def get_monthly_quote_count(self, user_id: str) -> int:
        """Count quotes created in current calendar month"""
        first_of_month, next_month = self._get_current_month_range()
        
        count = await self.quotes.count_documents({
            "owner_id": user_id,
            "created_at": {
                "$gte": first_of_month.isoformat(),
                "$lt": next_month.isoformat()
            }
        })
        return count
    
    async def get_total_invoice_count(self, user_id: str) -> int:
        """Count total invoices (for trial)"""
        return await self.invoices.count_documents({"owner_id": user_id})
    
    async def get_total_quote_count(self, user_id: str) -> int:
        """Count total quotes (for trial)"""
        return await self.quotes.count_documents({"owner_id": user_id})
    
    # ============== USER SUBSCRIPTION STATUS ==============
    
    async def get_user_subscription_info(self, user_id: str) -> Dict[str, Any]:
        """Get complete subscription info for a user"""
        user = await self.users.find_one({"id": user_id})
        if not user:
            raise ValueError("User not found")
        
        plan = user.get("subscription_plan", "trial")
        status = user.get("subscription_status", "trial")
        
        # Get plan config
        plan_config = self.get_plan_config(plan)
        limits = plan_config.get("limits", {})
        features = plan_config.get("features", {})
        
        # Calculate trial info
        trial_info = await self._get_trial_info(user)
        
        # Get usage based on plan type
        if status == "trial" or plan == "trial":
            # Trial uses total counts
            invoice_usage = await self.get_total_invoice_count(user_id)
            quote_usage = await self.get_total_quote_count(user_id)
            invoice_limit = limits.get("invoices_per_month", 9)
            quote_limit = limits.get("quotes_per_month", 9)
        else:
            # Paid plans use monthly counts
            invoice_usage = await self.get_monthly_invoice_count(user_id)
            quote_usage = await self.get_monthly_quote_count(user_id)
            invoice_limit = limits.get("invoices_per_month", 30)
            quote_limit = limits.get("quotes_per_month", 30)
        
        # Determine if can create documents
        is_active = self._is_subscription_active(user)
        can_create_invoice = is_active and (invoice_limit == -1 or invoice_usage < invoice_limit)
        can_create_quote = is_active and (quote_limit == -1 or quote_usage < quote_limit)
        
        return {
            "plan": plan,
            "plan_name": plan_config.get("name", plan),
            "plan_description": plan_config.get("description", ""),
            "status": status,
            "is_active": is_active,
            "is_trial": status == "trial" or plan == "trial",
            
            # Trial info
            "trial_start": trial_info.get("trial_start"),
            "trial_end": trial_info.get("trial_end"),
            "trial_days_remaining": trial_info.get("days_remaining"),
            "trial_expired": trial_info.get("expired", False),
            
            # Usage
            "invoice_usage": invoice_usage,
            "invoice_limit": invoice_limit,
            "quote_usage": quote_usage,
            "quote_limit": quote_limit,
            
            # Permissions
            "can_create_invoice": can_create_invoice,
            "can_create_quote": can_create_quote,
            
            # Features
            "features": features,
            "limits": limits,
            
            # Stripe info
            "stripe_customer_id": user.get("stripe_customer_id"),
            "stripe_subscription_id": user.get("stripe_subscription_id"),
            "current_period_end": user.get("current_period_end"),
        }
    
    async def _get_trial_info(self, user: Dict) -> Dict[str, Any]:
        """Get trial information for a user"""
        trial_start = user.get("trial_start")
        trial_end = user.get("trial_end")
        
        if not trial_end:
            return {"trial_start": None, "trial_end": None, "days_remaining": None, "expired": False}
        
        # Parse trial end date
        if isinstance(trial_end, str):
            try:
                end_date = datetime.fromisoformat(trial_end.replace("Z", "+00:00"))
            except:
                return {"trial_start": trial_start, "trial_end": trial_end, "days_remaining": 0, "expired": True}
        else:
            end_date = trial_end
        
        now = datetime.now(timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        days_remaining = max(0, (end_date - now).days)
        expired = now > end_date
        
        return {
            "trial_start": trial_start,
            "trial_end": trial_end if isinstance(trial_end, str) else trial_end.isoformat(),
            "days_remaining": days_remaining,
            "expired": expired
        }
    
    def _is_subscription_active(self, user: Dict) -> bool:
        """Check if user subscription is active"""
        status = user.get("subscription_status", "trial")
        plan = user.get("subscription_plan", "trial")
        role = user.get("role", "user")
        
        # Super admin always active
        if role == "super_admin":
            return True
        
        # Check paid subscription
        if status == "active":
            return True
        
        # Check trial
        if status == "trial" or plan == "trial":
            trial_end = user.get("trial_end")
            if trial_end:
                if isinstance(trial_end, str):
                    try:
                        end_date = datetime.fromisoformat(trial_end.replace("Z", "+00:00"))
                    except:
                        return False
                else:
                    end_date = trial_end
                
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                
                return datetime.now(timezone.utc) <= end_date
        
        return False
    
    # ============== PERMISSION CHECKS ==============
    
    async def check_invoice_permission(self, user: Dict) -> Dict[str, Any]:
        """Check if user can create an invoice"""
        user_id = user.get("id")
        role = user.get("role", "user")
        
        # Super admin bypass
        if role == "super_admin":
            return {"allowed": True, "reason": "super_admin"}
        
        # Get subscription info
        try:
            sub_info = await self.get_user_subscription_info(user_id)
        except ValueError:
            return {"allowed": False, "reason": "user_not_found", "message": "Utilisateur non trouvé"}
        
        # Check if active
        if not sub_info["is_active"]:
            if sub_info["trial_expired"]:
                return {
                    "allowed": False,
                    "reason": "trial_expired",
                    "message": "Votre période d'essai a expiré. Passez à un plan payant pour continuer."
                }
            return {
                "allowed": False,
                "reason": "subscription_inactive",
                "message": "Votre abonnement n'est pas actif."
            }
        
        # Check limits
        if not sub_info["can_create_invoice"]:
            limit = sub_info["invoice_limit"]
            usage = sub_info["invoice_usage"]
            
            if sub_info["is_trial"]:
                return {
                    "allowed": False,
                    "reason": "trial_limit_reached",
                    "message": f"Limite d'essai atteinte ({usage}/{limit} factures). Passez au plan Essentiel pour continuer."
                }
            else:
                return {
                    "allowed": False,
                    "reason": "monthly_limit_reached",
                    "message": f"Limite mensuelle atteinte ({usage}/{limit} factures). Passez au plan Pro pour des factures illimitées."
                }
        
        return {"allowed": True, "reason": "ok"}
    
    async def check_quote_permission(self, user: Dict) -> Dict[str, Any]:
        """Check if user can create a quote"""
        user_id = user.get("id")
        role = user.get("role", "user")
        
        # Super admin bypass
        if role == "super_admin":
            return {"allowed": True, "reason": "super_admin"}
        
        # Get subscription info
        try:
            sub_info = await self.get_user_subscription_info(user_id)
        except ValueError:
            return {"allowed": False, "reason": "user_not_found", "message": "Utilisateur non trouvé"}
        
        # Check if active
        if not sub_info["is_active"]:
            if sub_info["trial_expired"]:
                return {
                    "allowed": False,
                    "reason": "trial_expired",
                    "message": "Votre période d'essai a expiré. Passez à un plan payant pour continuer."
                }
            return {
                "allowed": False,
                "reason": "subscription_inactive",
                "message": "Votre abonnement n'est pas actif."
            }
        
        # Check limits
        if not sub_info["can_create_quote"]:
            limit = sub_info["quote_limit"]
            usage = sub_info["quote_usage"]
            
            if sub_info["is_trial"]:
                return {
                    "allowed": False,
                    "reason": "trial_limit_reached",
                    "message": f"Limite d'essai atteinte ({usage}/{limit} devis). Passez au plan Essentiel pour continuer."
                }
            else:
                return {
                    "allowed": False,
                    "reason": "monthly_limit_reached",
                    "message": f"Limite mensuelle atteinte ({usage}/{limit} devis). Passez au plan Pro pour des devis illimités."
                }
        
        return {"allowed": True, "reason": "ok"}
    
    async def check_feature_access(self, user_id: str, feature: str) -> Dict[str, Any]:
        """Check if user has access to a specific feature"""
        try:
            sub_info = await self.get_user_subscription_info(user_id)
        except ValueError:
            return {"allowed": False, "reason": "user_not_found"}
        
        features = sub_info.get("features", {})
        has_feature = features.get(feature, False)
        
        if has_feature:
            return {"allowed": True}
        
        # Determine upgrade plan
        current_plan = sub_info.get("plan", "trial")
        upgrade_plan = "essentiel"
        if current_plan == "essentiel":
            upgrade_plan = "pro"
        elif current_plan == "pro":
            upgrade_plan = "business"
        
        return {
            "allowed": False,
            "reason": "feature_not_available",
            "message": f"Fonctionnalité disponible avec le plan {upgrade_plan.capitalize()}",
            "upgrade_plan": upgrade_plan
        }
    
    # ============== SUBSCRIPTION MANAGEMENT ==============
    
    async def activate_subscription(
        self,
        user_id: str,
        plan: str,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        current_period_end: Optional[str] = None
    ) -> bool:
        """Activate a paid subscription"""
        if plan not in ["essentiel", "pro", "business"]:
            logger.error(f"Invalid plan: {plan}")
            return False
        
        update_data = {
            "subscription_plan": plan,
            "subscription_status": "active",
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "current_period_end": current_period_end,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = await self.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Subscription activated: user={user_id}, plan={plan}")
            return True
        return False
    
    async def cancel_subscription(self, user_id: str) -> bool:
        """Cancel subscription (effective at period end)"""
        result = await self.users.update_one(
            {"id": user_id},
            {"$set": {
                "subscription_status": "canceled",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count > 0:
            logger.info(f"Subscription canceled: user={user_id}")
            return True
        return False
    
    async def expire_subscription(self, user_id: str) -> bool:
        """Mark subscription as expired"""
        result = await self.users.update_one(
            {"id": user_id},
            {"$set": {
                "subscription_status": "expired",
                "subscription_plan": "trial",
                "stripe_subscription_id": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count > 0:
            logger.info(f"Subscription expired: user={user_id}")
            return True
        return False
    
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
    
    async def renew_subscription(self, user_id: str, current_period_end: str) -> bool:
        """Handle subscription renewal"""
        result = await self.users.update_one(
            {"id": user_id},
            {"$set": {
                "subscription_status": "active",
                "current_period_end": current_period_end,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return result.modified_count > 0


def get_plans_service(db: AsyncIOMotorDatabase) -> PlansService:
    """Factory function"""
    return PlansService(db)
