"""
Trial and Subscription Service
Manages trial periods, usage limits, and subscription status
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Trial configuration
TRIAL_DURATION_DAYS = 7
DEFAULT_TRIAL_QUOTE_LIMIT = 5
DEFAULT_TRIAL_INVOICE_LIMIT = 5

# Subscription plans
PLANS = {
    "trial": {
        "name": "Essai Gratuit",
        "quote_limit": 5,
        "invoice_limit": 5,
        "duration_days": 7,
    },
    "starter": {
        "name": "Starter",
        "quote_limit": 20,
        "invoice_limit": 20,
        "price_monthly": 19,
    },
    "professional": {
        "name": "Professionnel",
        "quote_limit": 100,
        "invoice_limit": 100,
        "price_monthly": 49,
    },
    "enterprise": {
        "name": "Entreprise",
        "quote_limit": 99999,
        "invoice_limit": 99999,
        "price_monthly": 99,
    },
}


def calculate_trial_status(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate the current trial status for a user
    Returns trial info including remaining days, status, and limits
    """
    now = datetime.now(timezone.utc)
    
    # Super admin has unlimited access
    if user.get("role") == "super_admin":
        return {
            "is_trial": False,
            "trial_status": "converted",
            "trial_days_remaining": 0,
            "trial_expired": False,
            "subscription_active": True,
            "quote_limit": 99999,
            "invoice_limit": 99999,
            "can_create_quotes": True,
            "can_create_invoices": True,
        }
    
    # Check if user has active subscription
    subscription_status = user.get("subscription_status")
    subscription_plan = user.get("subscription_plan", "trial")
    
    if subscription_status == "active" and subscription_plan not in ["trial", "trial_pending", "trial_active"]:
        plan = PLANS.get(subscription_plan, PLANS["professional"])
        return {
            "is_trial": False,
            "trial_status": "converted",
            "trial_days_remaining": 0,
            "trial_expired": False,
            "subscription_active": True,
            "subscription_plan": subscription_plan,
            "quote_limit": plan["quote_limit"],
            "invoice_limit": plan["invoice_limit"],
            "can_create_quotes": True,
            "can_create_invoices": True,
        }
    
    # Calculate trial status
    trial_started_at = user.get("trial_started_at")
    trial_ends_at = user.get("trial_ends_at")
    
    # If no trial dates, calculate from created_at
    if not trial_started_at:
        created_at = user.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                trial_started_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                trial_started_at = created_at
            trial_ends_at = trial_started_at + timedelta(days=TRIAL_DURATION_DAYS)
        else:
            # New user, start trial now
            trial_started_at = now
            trial_ends_at = now + timedelta(days=TRIAL_DURATION_DAYS)
    else:
        if isinstance(trial_started_at, str):
            trial_started_at = datetime.fromisoformat(trial_started_at.replace("Z", "+00:00"))
        if isinstance(trial_ends_at, str):
            trial_ends_at = datetime.fromisoformat(trial_ends_at.replace("Z", "+00:00"))
    
    # Calculate remaining days
    if trial_ends_at:
        time_remaining = trial_ends_at - now
        days_remaining = max(0, time_remaining.days)
    else:
        days_remaining = 0
    
    trial_expired = days_remaining <= 0
    
    # Get limits
    quote_limit = user.get("quote_limit", DEFAULT_TRIAL_QUOTE_LIMIT)
    invoice_limit = user.get("invoice_limit", DEFAULT_TRIAL_INVOICE_LIMIT)
    
    return {
        "is_trial": True,
        "trial_status": "expired" if trial_expired else "active",
        "trial_days_remaining": days_remaining,
        "trial_started_at": trial_started_at.isoformat() if trial_started_at else None,
        "trial_ends_at": trial_ends_at.isoformat() if trial_ends_at else None,
        "trial_expired": trial_expired,
        "subscription_active": False,
        "subscription_plan": "trial",
        "quote_limit": quote_limit,
        "invoice_limit": invoice_limit,
        "can_create_quotes": not trial_expired,
        "can_create_invoices": not trial_expired,
    }


def check_usage_limits(user: Dict[str, Any], quotes_count: int, invoices_count: int) -> Dict[str, Any]:
    """
    Check if user has reached their usage limits
    """
    trial_info = calculate_trial_status(user)
    
    quote_limit = trial_info["quote_limit"]
    invoice_limit = trial_info["invoice_limit"]
    
    quotes_remaining = max(0, quote_limit - quotes_count)
    invoices_remaining = max(0, invoice_limit - invoices_count)
    
    can_create_quote = quotes_count < quote_limit and trial_info["can_create_quotes"]
    can_create_invoice = invoices_count < invoice_limit and trial_info["can_create_invoices"]
    
    return {
        **trial_info,
        "quotes_count": quotes_count,
        "quotes_remaining": quotes_remaining,
        "quotes_limit_reached": not can_create_quote,
        "invoices_count": invoices_count,
        "invoices_remaining": invoices_remaining,
        "invoices_limit_reached": not can_create_invoice,
        "can_create_quote": can_create_quote,
        "can_create_invoice": can_create_invoice,
    }


def get_trial_banner_message(trial_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate banner message based on trial status
    """
    if not trial_info.get("is_trial"):
        return None
    
    days_remaining = trial_info.get("trial_days_remaining", 0)
    trial_expired = trial_info.get("trial_expired", False)
    
    if trial_expired:
        return {
            "type": "error",
            "title": "Période d'essai expirée",
            "message": "Votre période d'essai est terminée. Passez à un abonnement pour continuer à utiliser toutes les fonctionnalités.",
            "action": "upgrade",
            "action_label": "Passer à l'abonnement",
        }
    elif days_remaining <= 2:
        return {
            "type": "warning",
            "title": f"Fin d'essai dans {days_remaining} jour{'s' if days_remaining > 1 else ''}",
            "message": f"Votre essai gratuit se termine dans {days_remaining} jour{'s' if days_remaining > 1 else ''}. Passez à un abonnement pour continuer.",
            "action": "upgrade",
            "action_label": "Passer à l'abonnement",
        }
    else:
        return {
            "type": "info",
            "title": f"Essai gratuit - {days_remaining} jours restants",
            "message": f"Profitez de votre essai gratuit ! Il vous reste {days_remaining} jours.",
            "action": None,
            "action_label": None,
        }


def initialize_trial_for_user(user_id: str, supabase_client) -> Dict[str, Any]:
    """
    Initialize trial period for a new user
    """
    now = datetime.now(timezone.utc)
    trial_ends = now + timedelta(days=TRIAL_DURATION_DAYS)
    
    trial_data = {
        "trial_started_at": now.isoformat(),
        "trial_ends_at": trial_ends.isoformat(),
        "trial_status": "active",
        "subscription_plan": "trial",
        "subscription_status": "trial_active",
        "quote_limit": DEFAULT_TRIAL_QUOTE_LIMIT,
        "invoice_limit": DEFAULT_TRIAL_INVOICE_LIMIT,
    }
    
    try:
        result = supabase_client.from_("users")\
            .update(trial_data)\
            .eq("id", user_id)\
            .execute()
        
        logger.info(f"Trial initialized for user {user_id}")
        return trial_data
    except Exception as e:
        logger.error(f"Error initializing trial for user {user_id}: {e}")
        raise
