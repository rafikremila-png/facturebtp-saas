"""
Subscription Service for BTP Facture
Handles trial limits and subscription checks for invoice and quote creation
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Constants
TRIAL_INVOICE_LIMIT = 9
TRIAL_QUOTE_LIMIT = 9
ROLE_SUPER_ADMIN = "super_admin"


class SubscriptionError(Exception):
    """Custom exception for subscription-related errors"""
    def __init__(self, message: str, status_code: int = 403):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


async def check_invoice_permission(
    user: Dict[str, Any],
    db: AsyncIOMotorDatabase,
    raise_exception: bool = True
) -> Dict[str, Any]:
    """
    Check if user has permission to create a new invoice.
    
    Args:
        user: User document from database
        db: MongoDB database instance
        raise_exception: If True, raises HTTPException on failure
        
    Returns:
        Dict with permission status and details:
        {
            "allowed": bool,
            "reason": str,
            "invoice_count": int,
            "invoice_limit": int or None,
            "trial_status": str,
            "subscription_status": str
        }
        
    Raises:
        HTTPException: 403 if not allowed and raise_exception=True
    """
    user_id = user.get("id")
    role = user.get("role", "user")
    trial_status = user.get("plan")  # trial_pending, trial_active, trial_expired, paid
    subscription_status = user.get("subscription_status")  # active, canceled, past_due, None
    invoice_limit = user.get("invoice_limit", TRIAL_INVOICE_LIMIT)
    
    # Super admin always bypasses
    if role == ROLE_SUPER_ADMIN:
        logger.debug(f"[INVOICE GUARD] Super admin {user_id} - bypassing check")
        return {
            "allowed": True,
            "reason": "super_admin_bypass",
            "invoice_count": 0,
            "invoice_limit": None,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
    
    # Count existing invoices for this user
    try:
        invoice_count = await db.invoices.count_documents({"owner_id": user_id})
    except Exception as e:
        logger.error(f"[INVOICE GUARD] Database error counting invoices: {e}")
        if raise_exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la vérification des droits"
            )
        return {
            "allowed": False,
            "reason": "database_error",
            "invoice_count": 0,
            "invoice_limit": invoice_limit,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
    
    logger.debug(f"[INVOICE GUARD] User {user_id}: {invoice_count} invoices, trial={trial_status}, sub={subscription_status}")
    
    # Check paid subscription - unlimited invoices
    if subscription_status == "active":
        logger.debug(f"[INVOICE GUARD] User {user_id} has active subscription - allowed")
        return {
            "allowed": True,
            "reason": "paid_subscription",
            "invoice_count": invoice_count,
            "invoice_limit": None,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
    
    # Check trial expired
    if trial_status == "trial_expired" or trial_status is None:
        logger.warning(f"[INVOICE GUARD] User {user_id} trial expired - blocked")
        if raise_exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Votre période d'essai a expiré. Veuillez mettre à niveau votre abonnement."
            )
        return {
            "allowed": False,
            "reason": "trial_expired",
            "invoice_count": invoice_count,
            "invoice_limit": invoice_limit,
            "trial_status": trial_status or "unknown",
            "subscription_status": subscription_status
        }
    
    # Check trial pending (email not verified)
    if trial_status == "trial_pending":
        logger.warning(f"[INVOICE GUARD] User {user_id} trial pending - blocked")
        if raise_exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Veuillez vérifier votre email pour activer votre période d'essai."
            )
        return {
            "allowed": False,
            "reason": "trial_pending",
            "invoice_count": invoice_count,
            "invoice_limit": invoice_limit,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
    
    # Check trial active with limit
    if trial_status == "trial_active":
        # Check if trial has expired by date
        trial_end = user.get("trial_end")
        if trial_end:
            try:
                if isinstance(trial_end, str):
                    end_date = datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
                else:
                    end_date = trial_end
                
                # Make timezone aware if needed
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                
                if datetime.now(timezone.utc) > end_date:
                    logger.warning(f"[INVOICE GUARD] User {user_id} trial expired by date - blocked")
                    # Update trial status in background (don't block the request)
                    if raise_exception:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Votre période d'essai a expiré. Veuillez mettre à niveau votre abonnement."
                        )
                    return {
                        "allowed": False,
                        "reason": "trial_expired_by_date",
                        "invoice_count": invoice_count,
                        "invoice_limit": invoice_limit,
                        "trial_status": "trial_expired",
                        "subscription_status": subscription_status
                    }
            except Exception as e:
                logger.warning(f"[INVOICE GUARD] Error parsing trial_end date: {e}")
        
        # Check invoice limit
        if invoice_count >= invoice_limit:
            logger.warning(f"[INVOICE GUARD] User {user_id} reached trial limit ({invoice_count}/{invoice_limit}) - blocked")
            if raise_exception:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Limite d'essai atteinte ({invoice_limit} factures). Veuillez mettre à niveau pour continuer."
                )
            return {
                "allowed": False,
                "reason": "trial_limit_reached",
                "invoice_count": invoice_count,
                "invoice_limit": invoice_limit,
                "trial_status": trial_status,
                "subscription_status": subscription_status
            }
        
        # Trial active and within limit
        logger.debug(f"[INVOICE GUARD] User {user_id} trial active ({invoice_count}/{invoice_limit}) - allowed")
        return {
            "allowed": True,
            "reason": "trial_active",
            "invoice_count": invoice_count,
            "invoice_limit": invoice_limit,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
    
    # Fallback - unknown status, block by default
    logger.warning(f"[INVOICE GUARD] User {user_id} unknown status ({trial_status}) - blocked")
    if raise_exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Statut d'abonnement inconnu. Veuillez contacter le support."
        )
    return {
        "allowed": False,
        "reason": "unknown_status",
        "invoice_count": invoice_count,
        "invoice_limit": invoice_limit,
        "trial_status": trial_status or "unknown",
        "subscription_status": subscription_status
    }


async def get_user_invoice_stats(
    user_id: str,
    db: AsyncIOMotorDatabase
) -> Dict[str, Any]:
    """
    Get invoice statistics for a user.
    
    Args:
        user_id: User's unique identifier
        db: MongoDB database instance
        
    Returns:
        Dict with invoice stats
    """
    try:
        invoice_count = await db.invoices.count_documents({"owner_id": user_id})
        
        # Get user info
        user = await db.users.find_one({"id": user_id})
        if not user:
            return {
                "invoice_count": 0,
                "invoice_limit": TRIAL_INVOICE_LIMIT,
                "can_create": False,
                "trial_status": "unknown"
            }
        
        trial_status = user.get("plan", "trial_pending")
        subscription_status = user.get("subscription_status")
        invoice_limit = user.get("invoice_limit", TRIAL_INVOICE_LIMIT)
        
        # Determine if can create
        can_create = False
        if user.get("role") == ROLE_SUPER_ADMIN:
            can_create = True
            invoice_limit = None
        elif subscription_status == "active":
            can_create = True
            invoice_limit = None
        elif trial_status == "trial_active":
            can_create = invoice_count < invoice_limit
        
        return {
            "invoice_count": invoice_count,
            "invoice_limit": invoice_limit,
            "invoices_remaining": (invoice_limit - invoice_count) if invoice_limit else None,
            "can_create": can_create,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
        
    except Exception as e:
        logger.error(f"Error getting invoice stats for user {user_id}: {e}")
        return {
            "invoice_count": 0,
            "invoice_limit": TRIAL_INVOICE_LIMIT,
            "can_create": False,
            "trial_status": "error"
        }


async def check_quote_permission(
    user: Dict[str, Any],
    db: AsyncIOMotorDatabase,
    raise_exception: bool = True
) -> Dict[str, Any]:
    """
    Check if user has permission to create a new quote.
    
    Args:
        user: User document from database
        db: MongoDB database instance
        raise_exception: If True, raises HTTPException on failure
        
    Returns:
        Dict with permission status and details:
        {
            "allowed": bool,
            "reason": str,
            "quote_count": int,
            "quote_limit": int or None,
            "trial_status": str,
            "subscription_status": str
        }
        
    Raises:
        HTTPException: 403 if not allowed and raise_exception=True
    """
    user_id = user.get("id")
    role = user.get("role", "user")
    trial_status = user.get("plan")  # trial_pending, trial_active, trial_expired, paid
    subscription_status = user.get("subscription_status")  # active, canceled, past_due, None
    quote_limit = user.get("quote_limit", TRIAL_QUOTE_LIMIT)
    
    # Super admin always bypasses
    if role == ROLE_SUPER_ADMIN:
        logger.debug(f"[QUOTE GUARD] Super admin {user_id} - bypassing check")
        return {
            "allowed": True,
            "reason": "super_admin_bypass",
            "quote_count": 0,
            "quote_limit": None,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
    
    # Count existing quotes for this user
    try:
        quote_count = await db.quotes.count_documents({"owner_id": user_id})
    except Exception as e:
        logger.error(f"[QUOTE GUARD] Database error counting quotes: {e}")
        if raise_exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la vérification des droits"
            )
        return {
            "allowed": False,
            "reason": "database_error",
            "quote_count": 0,
            "quote_limit": quote_limit,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
    
    logger.debug(f"[QUOTE GUARD] User {user_id}: {quote_count} quotes, trial={trial_status}, sub={subscription_status}")
    
    # Check paid subscription - unlimited quotes
    if subscription_status == "active":
        logger.debug(f"[QUOTE GUARD] User {user_id} has active subscription - allowed")
        return {
            "allowed": True,
            "reason": "paid_subscription",
            "quote_count": quote_count,
            "quote_limit": None,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
    
    # Check trial expired
    if trial_status == "trial_expired" or trial_status is None:
        logger.warning(f"[QUOTE GUARD] User {user_id} trial expired - blocked")
        if raise_exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Votre période d'essai a expiré. Veuillez mettre à niveau votre abonnement."
            )
        return {
            "allowed": False,
            "reason": "trial_expired",
            "quote_count": quote_count,
            "quote_limit": quote_limit,
            "trial_status": trial_status or "unknown",
            "subscription_status": subscription_status
        }
    
    # Check trial pending (email not verified)
    if trial_status == "trial_pending":
        logger.warning(f"[QUOTE GUARD] User {user_id} trial pending - blocked")
        if raise_exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Veuillez vérifier votre email pour activer votre période d'essai."
            )
        return {
            "allowed": False,
            "reason": "trial_pending",
            "quote_count": quote_count,
            "quote_limit": quote_limit,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
    
    # Check trial active with limit
    if trial_status == "trial_active":
        # Check if trial has expired by date
        trial_end = user.get("trial_end")
        if trial_end:
            try:
                if isinstance(trial_end, str):
                    end_date = datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
                else:
                    end_date = trial_end
                
                # Make timezone aware if needed
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                
                if datetime.now(timezone.utc) > end_date:
                    logger.warning(f"[QUOTE GUARD] User {user_id} trial expired by date - blocked")
                    if raise_exception:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Votre période d'essai a expiré. Veuillez mettre à niveau votre abonnement."
                        )
                    return {
                        "allowed": False,
                        "reason": "trial_expired_by_date",
                        "quote_count": quote_count,
                        "quote_limit": quote_limit,
                        "trial_status": "trial_expired",
                        "subscription_status": subscription_status
                    }
            except Exception as e:
                logger.warning(f"[QUOTE GUARD] Error parsing trial_end date: {e}")
        
        # Check quote limit
        if quote_count >= quote_limit:
            logger.warning(f"[QUOTE GUARD] User {user_id} reached trial limit ({quote_count}/{quote_limit}) - blocked")
            if raise_exception:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Limite d'essai atteinte ({quote_limit} devis). Veuillez mettre à niveau pour continuer."
                )
            return {
                "allowed": False,
                "reason": "trial_limit_reached",
                "quote_count": quote_count,
                "quote_limit": quote_limit,
                "trial_status": trial_status,
                "subscription_status": subscription_status
            }
        
        # Trial active and within limit
        logger.debug(f"[QUOTE GUARD] User {user_id} trial active ({quote_count}/{quote_limit}) - allowed")
        return {
            "allowed": True,
            "reason": "trial_active",
            "quote_count": quote_count,
            "quote_limit": quote_limit,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
    
    # Fallback - unknown status, block by default
    logger.warning(f"[QUOTE GUARD] User {user_id} unknown status ({trial_status}) - blocked")
    if raise_exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Statut d'abonnement inconnu. Veuillez contacter le support."
        )
    return {
        "allowed": False,
        "reason": "unknown_status",
        "quote_count": quote_count,
        "quote_limit": quote_limit,
        "trial_status": trial_status or "unknown",
        "subscription_status": subscription_status
    }


async def get_user_quote_stats(
    user_id: str,
    db: AsyncIOMotorDatabase
) -> Dict[str, Any]:
    """
    Get quote statistics for a user.
    
    Args:
        user_id: User's unique identifier
        db: MongoDB database instance
        
    Returns:
        Dict with quote stats
    """
    try:
        quote_count = await db.quotes.count_documents({"owner_id": user_id})
        
        # Get user info
        user = await db.users.find_one({"id": user_id})
        if not user:
            return {
                "quote_count": 0,
                "quote_limit": TRIAL_QUOTE_LIMIT,
                "can_create": False,
                "trial_status": "unknown"
            }
        
        trial_status = user.get("plan", "trial_pending")
        subscription_status = user.get("subscription_status")
        quote_limit = user.get("quote_limit", TRIAL_QUOTE_LIMIT)
        
        # Determine if can create
        can_create = False
        if user.get("role") == ROLE_SUPER_ADMIN:
            can_create = True
            quote_limit = None
        elif subscription_status == "active":
            can_create = True
            quote_limit = None
        elif trial_status == "trial_active":
            can_create = quote_count < quote_limit
        
        return {
            "quote_count": quote_count,
            "quote_limit": quote_limit,
            "quotes_remaining": (quote_limit - quote_count) if quote_limit else None,
            "can_create": can_create,
            "trial_status": trial_status,
            "subscription_status": subscription_status
        }
        
    except Exception as e:
        logger.error(f"Error getting quote stats for user {user_id}: {e}")
        return {
            "quote_count": 0,
            "quote_limit": TRIAL_QUOTE_LIMIT,
            "can_create": False,
            "trial_status": "error"
        }
