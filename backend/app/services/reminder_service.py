"""
Reminder Service for BTP Facture
Handles automatic unpaid invoice reminders (Pro plan feature)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import os

logger = logging.getLogger(__name__)

# Reminder schedule: days after due date
REMINDER_SCHEDULE = [7, 14, 30]  # First reminder after 7 days, then 14, then 30


class ReminderService:
    """Service for managing automatic invoice reminders"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.invoices = db.invoices
        self.users = db.users
        self.clients = db.clients
        self.reminders = db.reminders
    
    async def get_unpaid_invoices_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all unpaid invoices past due date"""
        now = datetime.now(timezone.utc)
        
        invoices = []
        cursor = self.invoices.find({
            "owner_id": user_id,
            "status": {"$in": ["impayé", "partiel"]},
            "due_date": {"$lt": now.isoformat()}
        })
        
        async for doc in cursor:
            doc.pop("_id", None)
            invoices.append(doc)
        
        return invoices
    
    async def check_user_has_reminder_feature(self, user_id: str) -> bool:
        """Check if user's plan includes automatic reminders"""
        user = await self.users.find_one({"id": user_id})
        if not user:
            return False
        
        plan = user.get("subscription_plan", "trial")
        status = user.get("subscription_status", "trial")
        
        # Only Pro and Business plans have reminders
        if plan in ["pro", "business"] and status == "active":
            return True
        
        return False
    
    async def get_reminder_history(self, invoice_id: str) -> List[Dict[str, Any]]:
        """Get reminder history for an invoice"""
        reminders = []
        cursor = self.reminders.find({"invoice_id": invoice_id}).sort("sent_at", -1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            reminders.append(doc)
        
        return reminders
    
    async def get_last_reminder(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent reminder for an invoice"""
        doc = await self.reminders.find_one(
            {"invoice_id": invoice_id},
            sort=[("sent_at", -1)]
        )
        if doc:
            doc.pop("_id", None)
        return doc
    
    async def should_send_reminder(self, invoice: Dict, user_id: str) -> Dict[str, Any]:
        """Check if a reminder should be sent for an invoice"""
        # Check feature access
        has_feature = await self.check_user_has_reminder_feature(user_id)
        if not has_feature:
            return {"should_send": False, "reason": "feature_not_available"}
        
        # Parse due date
        due_date_str = invoice.get("due_date")
        if not due_date_str:
            return {"should_send": False, "reason": "no_due_date"}
        
        try:
            if isinstance(due_date_str, str):
                due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
            else:
                due_date = due_date_str
        except:
            return {"should_send": False, "reason": "invalid_due_date"}
        
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        days_overdue = (now - due_date).days
        
        if days_overdue < REMINDER_SCHEDULE[0]:
            return {"should_send": False, "reason": "not_overdue_enough", "days_overdue": days_overdue}
        
        # Check last reminder
        last_reminder = await self.get_last_reminder(invoice["id"])
        reminder_count = 0
        
        if last_reminder:
            reminder_count = last_reminder.get("reminder_number", 0)
            last_sent = last_reminder.get("sent_at")
            
            if last_sent:
                if isinstance(last_sent, str):
                    last_sent_date = datetime.fromisoformat(last_sent.replace("Z", "+00:00"))
                else:
                    last_sent_date = last_sent
                
                if last_sent_date.tzinfo is None:
                    last_sent_date = last_sent_date.replace(tzinfo=timezone.utc)
                
                # Don't send more than once per week
                if (now - last_sent_date).days < 7:
                    return {"should_send": False, "reason": "too_recent", "days_since_last": (now - last_sent_date).days}
        
        # Determine which reminder to send
        next_reminder_number = reminder_count + 1
        if next_reminder_number > len(REMINDER_SCHEDULE):
            return {"should_send": False, "reason": "max_reminders_sent", "reminder_count": reminder_count}
        
        # Check if enough days have passed for this reminder
        required_days = REMINDER_SCHEDULE[next_reminder_number - 1]
        if days_overdue < required_days:
            return {
                "should_send": False,
                "reason": "waiting_for_schedule",
                "days_overdue": days_overdue,
                "required_days": required_days
            }
        
        return {
            "should_send": True,
            "reminder_number": next_reminder_number,
            "days_overdue": days_overdue
        }
    
    async def create_reminder_record(
        self,
        invoice_id: str,
        user_id: str,
        client_email: str,
        reminder_number: int,
        sent_successfully: bool = True
    ) -> Dict[str, Any]:
        """Record that a reminder was sent"""
        import uuid
        
        reminder_doc = {
            "id": str(uuid.uuid4()),
            "invoice_id": invoice_id,
            "user_id": user_id,
            "client_email": client_email,
            "reminder_number": reminder_number,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "sent_successfully": sent_successfully
        }
        
        await self.reminders.insert_one(reminder_doc)
        reminder_doc.pop("_id", None)
        
        logger.info(f"Reminder #{reminder_number} recorded for invoice {invoice_id}")
        return reminder_doc
    
    async def get_invoices_needing_reminders(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all invoices that need reminders"""
        # Check feature access first
        has_feature = await self.check_user_has_reminder_feature(user_id)
        if not has_feature:
            return []
        
        unpaid_invoices = await self.get_unpaid_invoices_for_user(user_id)
        invoices_needing_reminders = []
        
        for invoice in unpaid_invoices:
            check = await self.should_send_reminder(invoice, user_id)
            if check.get("should_send"):
                invoices_needing_reminders.append({
                    "invoice": invoice,
                    "reminder_number": check.get("reminder_number"),
                    "days_overdue": check.get("days_overdue")
                })
        
        return invoices_needing_reminders
    
    def generate_reminder_email_content(
        self,
        invoice: Dict,
        client: Dict,
        company_settings: Dict,
        reminder_number: int
    ) -> Dict[str, str]:
        """Generate email content for a reminder"""
        company_name = company_settings.get("company_name", "Notre entreprise")
        invoice_number = invoice.get("invoice_number", "N/A")
        total_ttc = invoice.get("total_ttc", 0)
        due_date = invoice.get("due_date", "N/A")
        client_name = client.get("name", "Client")
        
        # Format due date
        if isinstance(due_date, str) and due_date != "N/A":
            try:
                due_date_obj = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                due_date = due_date_obj.strftime("%d/%m/%Y")
            except:
                pass
        
        # Different tone based on reminder number
        if reminder_number == 1:
            subject = f"Rappel : Facture {invoice_number} en attente de paiement"
            tone = "Nous nous permettons de vous rappeler"
            urgency = ""
        elif reminder_number == 2:
            subject = f"2ème rappel : Facture {invoice_number} impayée"
            tone = "Sauf erreur de notre part, nous n'avons pas encore reçu votre règlement pour"
            urgency = "Merci de régulariser cette situation dans les plus brefs délais."
        else:
            subject = f"URGENT : Facture {invoice_number} - Dernier rappel avant procédure"
            tone = "Malgré nos précédents rappels, nous constatons que"
            urgency = "Sans paiement de votre part sous 8 jours, nous serons contraints d'engager une procédure de recouvrement."
        
        body = f"""Bonjour {client_name},

{tone} la facture n°{invoice_number} d'un montant de {total_ttc:.2f}€ TTC, échue le {due_date}, reste impayée.

{urgency}

Nous vous remercions de procéder au règlement dès réception de ce message.

Si vous avez déjà effectué le paiement, merci de ne pas tenir compte de ce rappel.

Cordialement,
{company_name}"""

        return {
            "subject": subject,
            "body": body
        }
    
    async def get_reminder_stats(self, user_id: str) -> Dict[str, Any]:
        """Get reminder statistics for a user"""
        has_feature = await self.check_user_has_reminder_feature(user_id)
        
        if not has_feature:
            return {
                "feature_available": False,
                "total_reminders_sent": 0,
                "invoices_with_reminders": 0,
                "unpaid_invoices": 0
            }
        
        # Count total reminders
        total_reminders = await self.reminders.count_documents({"user_id": user_id})
        
        # Count unique invoices with reminders
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$invoice_id"}},
            {"$count": "count"}
        ]
        result = await self.reminders.aggregate(pipeline).to_list(1)
        invoices_with_reminders = result[0]["count"] if result else 0
        
        # Count unpaid invoices
        unpaid_invoices = await self.invoices.count_documents({
            "owner_id": user_id,
            "status": {"$in": ["impayé", "partiel"]}
        })
        
        return {
            "feature_available": True,
            "total_reminders_sent": total_reminders,
            "invoices_with_reminders": invoices_with_reminders,
            "unpaid_invoices": unpaid_invoices
        }


def get_reminder_service(db: AsyncIOMotorDatabase) -> ReminderService:
    """Factory function"""
    return ReminderService(db)
