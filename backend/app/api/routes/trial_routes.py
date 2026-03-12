"""
Trial and Subscription API Routes
Endpoints for managing trial status and usage limits
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime, timezone

from app.services.supabase_auth_service import get_current_user, get_supabase_client
from app.services.trial_service import (
    calculate_trial_status,
    check_usage_limits,
    get_trial_banner_message,
    initialize_trial_for_user,
    PLANS,
)

router = APIRouter(prefix="/trial", tags=["Trial"])


@router.get("/status")
async def get_trial_status(user: Dict = Depends(get_current_user)):
    """
    Get current trial status and usage limits for the logged-in user
    """
    supabase = get_supabase_client()
    user_id = user["id"]
    
    # Get full user data with trial info
    user_result = supabase.from_("users")\
        .select("*")\
        .eq("id", user_id)\
        .single()\
        .execute()
    
    if not user_result.data:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user_data = user_result.data
    
    # Count quotes and invoices
    quotes_result = supabase.from_("quotes")\
        .select("id", count="exact")\
        .eq("user_id", user_id)\
        .execute()
    quotes_count = quotes_result.count or 0
    
    invoices_result = supabase.from_("invoices")\
        .select("id", count="exact")\
        .eq("user_id", user_id)\
        .execute()
    invoices_count = invoices_result.count or 0
    
    # Calculate trial status and limits
    usage_info = check_usage_limits(user_data, quotes_count, invoices_count)
    
    # Get banner message
    banner = get_trial_banner_message(usage_info)
    
    return {
        **usage_info,
        "banner": banner,
        "user_role": user_data.get("role", "user"),
    }


@router.get("/limits")
async def get_usage_limits(user: Dict = Depends(get_current_user)):
    """
    Get current usage limits and remaining counts
    """
    supabase = get_supabase_client()
    user_id = user["id"]
    
    # Get user data
    user_result = supabase.from_("users")\
        .select("role, subscription_plan, subscription_status, trial_status, trial_ends_at, quote_limit, invoice_limit")\
        .eq("id", user_id)\
        .single()\
        .execute()
    
    if not user_result.data:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user_data = user_result.data
    
    # Count quotes and invoices
    quotes_result = supabase.from_("quotes")\
        .select("id", count="exact")\
        .eq("user_id", user_id)\
        .execute()
    quotes_count = quotes_result.count or 0
    
    invoices_result = supabase.from_("invoices")\
        .select("id", count="exact")\
        .eq("user_id", user_id)\
        .execute()
    invoices_count = invoices_result.count or 0
    
    # Get limits
    quote_limit = user_data.get("quote_limit", 5)
    invoice_limit = user_data.get("invoice_limit", 5)
    
    # Super admin has unlimited
    if user_data.get("role") == "super_admin":
        quote_limit = 99999
        invoice_limit = 99999
    
    return {
        "quotes": {
            "used": quotes_count,
            "limit": quote_limit,
            "remaining": max(0, quote_limit - quotes_count),
            "can_create": quotes_count < quote_limit,
        },
        "invoices": {
            "used": invoices_count,
            "limit": invoice_limit,
            "remaining": max(0, invoice_limit - invoices_count),
            "can_create": invoices_count < invoice_limit,
        },
    }


@router.post("/check-limit/{resource_type}")
async def check_can_create(resource_type: str, user: Dict = Depends(get_current_user)):
    """
    Check if user can create a new quote or invoice
    """
    if resource_type not in ["quote", "invoice"]:
        raise HTTPException(status_code=400, detail="Type de ressource invalide")
    
    supabase = get_supabase_client()
    user_id = user["id"]
    
    # Get user data
    user_result = supabase.from_("users")\
        .select("role, subscription_status, trial_status, trial_ends_at, quote_limit, invoice_limit")\
        .eq("id", user_id)\
        .single()\
        .execute()
    
    user_data = user_result.data or {}
    
    # Super admin always allowed
    if user_data.get("role") == "super_admin":
        return {"allowed": True, "message": "Accès illimité"}
    
    # Check trial expiration
    trial_info = calculate_trial_status(user_data)
    if trial_info.get("trial_expired") and not trial_info.get("subscription_active"):
        return {
            "allowed": False,
            "message": "Votre période d'essai est expirée. Passez à un abonnement pour continuer.",
            "reason": "trial_expired",
        }
    
    # Count resources
    table = "quotes" if resource_type == "quote" else "invoices"
    result = supabase.from_(table)\
        .select("id", count="exact")\
        .eq("user_id", user_id)\
        .execute()
    current_count = result.count or 0
    
    # Get limit
    limit_field = "quote_limit" if resource_type == "quote" else "invoice_limit"
    limit = user_data.get(limit_field, 5)
    
    if current_count >= limit:
        resource_name = "devis" if resource_type == "quote" else "factures"
        return {
            "allowed": False,
            "message": f"Vous avez atteint la limite de {limit} {resource_name} pour votre période d'essai. Passez à un abonnement pour créer plus.",
            "reason": "limit_reached",
            "current": current_count,
            "limit": limit,
        }
    
    return {
        "allowed": True,
        "message": "OK",
        "current": current_count,
        "limit": limit,
        "remaining": limit - current_count,
    }


@router.get("/plans")
async def get_subscription_plans():
    """
    Get available subscription plans (unified with /subscription/plans)
    """
    return {
        "plans": [
            {
                "id": "essentiel",
                "name": "Essentiel",
                "price": 19,
                "price_monthly": 19,
                "quote_limit": 99999,
                "invoice_limit": 30,
                "max_users": 1,
                "features": ["Devis illimités", "30 factures/mois", "Bibliothèque articles", "Support email"],
                "description": "Pour les artisans débutants"
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 29,
                "price_monthly": 29,
                "quote_limit": 99999,
                "invoice_limit": 99999,
                "max_users": 1,
                "features": ["Devis illimités", "Factures illimitées", "Kits prédéfinis", "Prix intelligents", "Support prioritaire"],
                "popular": True,
                "description": "Pour les professionnels actifs"
            },
            {
                "id": "business",
                "name": "Business",
                "price": 59,
                "price_monthly": 59,
                "quote_limit": 99999,
                "invoice_limit": 99999,
                "max_users": 10,
                "features": ["Tout Pro +", "10 utilisateurs", "Dashboard avancé", "API access", "Support dédié"],
                "description": "Pour les entreprises en croissance"
            },
        ],
    }
