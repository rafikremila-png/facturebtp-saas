"""
Marketing Notification Service
In-app notifications and marketing automation
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging

from app.core.database import db, is_mongodb

logger = logging.getLogger(__name__)

# Notification types
NOTIFICATION_TYPES = {
    "welcome": "Bienvenue",
    "feature_announcement": "Nouvelle fonctionnalité",
    "trial_expiring": "Essai expirant",
    "trial_expired": "Essai expiré",
    "product_update": "Mise à jour produit",
    "tip": "Conseil",
    "promotion": "Promotion",
    "missing_website": "Site web manquant",
    "incomplete_profile": "Profil incomplet",
    "invoice_milestone": "Jalon factures"
}

class MarketingNotificationService:
    """Service for marketing notifications"""
    
    @staticmethod
    async def create_notification(user_id: str, notification_type: str,
                                   title: str, message: str,
                                   action_url: Optional[str] = None,
                                   action_label: Optional[str] = None,
                                   scheduled_at: Optional[datetime] = None) -> Dict[str, Any]:
        """Create a notification for a user"""
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "target_audience": "individual",
            "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
            "sent_at": datetime.now(timezone.utc).isoformat() if not scheduled_at else None,
            "status": "pending" if scheduled_at else "sent",
            "read_at": None,
            "action_url": action_url,
            "action_label": action_label,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if is_mongodb():
            await db.marketing_notifications.insert_one(notification.copy())
        
        return notification
    
    @staticmethod
    async def create_broadcast(notification_type: str, title: str, message: str,
                               target_audience: str = "all",
                               action_url: Optional[str] = None,
                               action_label: Optional[str] = None,
                               scheduled_at: Optional[datetime] = None) -> Dict[str, Any]:
        """Create a broadcast notification for multiple users"""
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": None,  # None means broadcast
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "target_audience": target_audience,
            "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
            "sent_at": None,
            "status": "pending",
            "read_at": None,
            "action_url": action_url,
            "action_label": action_label,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if is_mongodb():
            await db.marketing_notifications.insert_one(notification.copy())
        
        return notification
    
    @staticmethod
    async def get_user_notifications(user_id: str, include_read: bool = False,
                                      limit: int = 50) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        query = {
            "$or": [
                {"user_id": user_id},
                {"user_id": None, "target_audience": {"$in": ["all", "free_users", "paid_users"]}}
            ],
            "status": {"$in": ["sent"]}
        }
        
        if not include_read:
            query["read_at"] = None
        
        if is_mongodb():
            cursor = db.marketing_notifications.find(
                query,
                {"_id": 0}
            ).sort("created_at", -1).limit(limit)
            
            return await cursor.to_list(length=limit)
        return []
    
    @staticmethod
    async def get_unread_count(user_id: str) -> int:
        """Get count of unread notifications"""
        if is_mongodb():
            return await db.marketing_notifications.count_documents({
                "$or": [
                    {"user_id": user_id},
                    {"user_id": None}
                ],
                "status": "sent",
                "read_at": None
            })
        return 0
    
    @staticmethod
    async def mark_as_read(notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        if is_mongodb():
            result = await db.marketing_notifications.update_one(
                {
                    "id": notification_id,
                    "$or": [{"user_id": user_id}, {"user_id": None}]
                },
                {"$set": {"read_at": datetime.now(timezone.utc).isoformat()}}
            )
            return result.modified_count > 0
        return False
    
    @staticmethod
    async def mark_all_as_read(user_id: str) -> int:
        """Mark all notifications as read for a user"""
        if is_mongodb():
            result = await db.marketing_notifications.update_many(
                {
                    "$or": [{"user_id": user_id}, {"user_id": None}],
                    "read_at": None
                },
                {"$set": {"read_at": datetime.now(timezone.utc).isoformat()}}
            )
            return result.modified_count
        return 0
    
    @staticmethod
    async def dismiss_notification(notification_id: str, user_id: str) -> bool:
        """Dismiss a notification"""
        if is_mongodb():
            result = await db.marketing_notifications.update_one(
                {
                    "id": notification_id,
                    "$or": [{"user_id": user_id}, {"user_id": None}]
                },
                {"$set": {"status": "dismissed"}}
            )
            return result.modified_count > 0
        return False
    
    @staticmethod
    async def check_and_create_automated_notifications(user_id: str) -> List[Dict[str, Any]]:
        """Check triggers and create automated notifications"""
        created = []
        
        if is_mongodb():
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            user_settings = await db.user_settings.find_one({"user_id": user_id}, {"_id": 0})
            
            if not user:
                return created
            
            # Check for missing website
            if user_settings and not user_settings.get("company_website"):
                existing = await db.marketing_notifications.find_one({
                    "user_id": user_id,
                    "notification_type": "missing_website",
                    "status": {"$ne": "dismissed"}
                })
                
                if not existing:
                    notif = await MarketingNotificationService.create_notification(
                        user_id=user_id,
                        notification_type="missing_website",
                        title="Créez votre site web professionnel",
                        message="Vous n'avez pas encore de site web. Nous pouvons vous aider à créer un site professionnel pour votre entreprise BTP.",
                        action_url="/services/website",
                        action_label="En savoir plus"
                    )
                    created.append(notif)
            
            # Check for incomplete profile
            if user_settings:
                missing_fields = []
                if not user_settings.get("siret"):
                    missing_fields.append("SIRET")
                if not user_settings.get("iban"):
                    missing_fields.append("IBAN")
                if not user_settings.get("logo_base64"):
                    missing_fields.append("Logo")
                
                if missing_fields:
                    existing = await db.marketing_notifications.find_one({
                        "user_id": user_id,
                        "notification_type": "incomplete_profile",
                        "status": {"$ne": "dismissed"},
                        "created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()}
                    })
                    
                    if not existing:
                        notif = await MarketingNotificationService.create_notification(
                            user_id=user_id,
                            notification_type="incomplete_profile",
                            title="Complétez votre profil",
                            message=f"Il manque des informations dans votre profil : {', '.join(missing_fields)}. Complétez-les pour des factures plus professionnelles.",
                            action_url="/settings",
                            action_label="Compléter mon profil"
                        )
                        created.append(notif)
            
            # Check invoice milestone
            invoice_count = await db.invoices.count_documents({
                "user_id": user_id,
                "status": "paid"
            })
            
            milestones = [10, 50, 100, 500, 1000]
            for milestone in milestones:
                if invoice_count >= milestone:
                    existing = await db.marketing_notifications.find_one({
                        "user_id": user_id,
                        "notification_type": "invoice_milestone",
                        "message": {"$regex": str(milestone)}
                    })
                    
                    if not existing:
                        notif = await MarketingNotificationService.create_notification(
                            user_id=user_id,
                            notification_type="invoice_milestone",
                            title=f"🎉 {milestone} factures payées !",
                            message=f"Félicitations ! Vous avez atteint {milestone} factures payées. Merci de votre confiance.",
                            action_url="/dashboard",
                            action_label="Voir mes statistiques"
                        )
                        created.append(notif)
                        break
        
        return created
    
    @staticmethod
    async def send_welcome_notification(user_id: str, user_name: str) -> Dict[str, Any]:
        """Send welcome notification to new user"""
        return await MarketingNotificationService.create_notification(
            user_id=user_id,
            notification_type="welcome",
            title=f"Bienvenue sur BTP Facture, {user_name} !",
            message="Nous sommes ravis de vous compter parmi nous. Commencez par configurer votre entreprise pour créer des devis et factures professionnels.",
            action_url="/settings",
            action_label="Configurer mon entreprise"
        )


# Create singleton instance
marketing_notification_service = MarketingNotificationService()
