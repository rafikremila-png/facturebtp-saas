"""
Invoice Reminder Service
Automatic payment reminders
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging

from app.core.database import db, is_mongodb
from app.core.config import settings

logger = logging.getLogger(__name__)

# Reminder schedule (days relative to due date)
REMINDER_SCHEDULE = {
    "before_7": -7,      # 7 days before due
    "on_due": 0,         # On due date
    "after_7": 7,        # 7 days after
    "after_14": 14,      # 14 days after
    "after_30": 30       # 30 days after (final notice)
}

REMINDER_TEMPLATES = {
    "before_7": {
        "subject": "Rappel : Facture {invoice_number} à échéance dans 7 jours",
        "body": """Bonjour {client_name},

Nous vous rappelons que la facture n°{invoice_number} d'un montant de {amount}€ arrive à échéance le {due_date}.

Merci de procéder au règlement dans les délais convenus.

Cordialement,
{company_name}"""
    },
    "on_due": {
        "subject": "Facture {invoice_number} - Échéance aujourd'hui",
        "body": """Bonjour {client_name},

La facture n°{invoice_number} d'un montant de {amount}€ arrive à échéance aujourd'hui ({due_date}).

Merci de procéder au règlement.

Cordialement,
{company_name}"""
    },
    "after_7": {
        "subject": "Relance : Facture {invoice_number} en retard de paiement",
        "body": """Bonjour {client_name},

Sauf erreur de notre part, la facture n°{invoice_number} d'un montant de {amount}€, dont l'échéance était le {due_date}, reste impayée.

Nous vous remercions de bien vouloir procéder au règlement dans les plus brefs délais.

Cordialement,
{company_name}"""
    },
    "after_14": {
        "subject": "2ème relance : Facture {invoice_number} impayée",
        "body": """Bonjour {client_name},

Malgré notre précédent rappel, la facture n°{invoice_number} d'un montant de {amount}€ reste impayée depuis le {due_date}.

Nous vous prions de régulariser cette situation dans les meilleurs délais.

Sans réponse de votre part sous 7 jours, nous serons contraints d'engager une procédure de recouvrement.

Cordialement,
{company_name}"""
    },
    "after_30": {
        "subject": "Mise en demeure : Facture {invoice_number}",
        "body": """Bonjour {client_name},

La présente constitue une mise en demeure concernant la facture n°{invoice_number} d'un montant de {amount}€, impayée depuis le {due_date}.

Sans règlement sous 8 jours, nous transmettrons ce dossier à notre service contentieux.

Cordialement,
{company_name}"""
    }
}

class InvoiceReminderService:
    """Service for managing invoice reminders"""
    
    @staticmethod
    async def create_reminders_for_invoice(invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create all scheduled reminders for an invoice"""
        reminders = []
        
        due_date_str = invoice.get("due_date")
        if not due_date_str:
            return reminders
        
        try:
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
        except:
            return reminders
        
        user_id = invoice["user_id"]
        invoice_id = invoice["id"]
        
        for reminder_type, days_offset in REMINDER_SCHEDULE.items():
            reminder_date = due_date + timedelta(days=days_offset)
            
            # Don't create reminders in the past
            if reminder_date < datetime.now(timezone.utc):
                continue
            
            reminder = {
                "id": str(uuid.uuid4()),
                "invoice_id": invoice_id,
                "user_id": user_id,
                "reminder_type": reminder_type,
                "reminder_date": reminder_date.isoformat(),
                "status": "pending",
                "sent_at": None,
                "email_subject": None,
                "email_body": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            reminders.append(reminder)
        
        if is_mongodb() and reminders:
            await db.invoice_reminders.insert_many(reminders)
        
        return reminders
    
    @staticmethod
    async def get_reminders_for_invoice(invoice_id: str) -> List[Dict[str, Any]]:
        """Get all reminders for an invoice"""
        if is_mongodb():
            cursor = db.invoice_reminders.find(
                {"invoice_id": invoice_id},
                {"_id": 0}
            ).sort("reminder_date", 1)
            return await cursor.to_list(length=50)
        return []
    
    @staticmethod
    async def get_pending_reminders(user_id: str = None) -> List[Dict[str, Any]]:
        """Get all pending reminders due today or earlier"""
        now = datetime.now(timezone.utc)
        
        query = {
            "status": "pending",
            "reminder_date": {"$lte": now.isoformat()}
        }
        
        if user_id:
            query["user_id"] = user_id
        
        if is_mongodb():
            cursor = db.invoice_reminders.find(query, {"_id": 0}).sort("reminder_date", 1)
            return await cursor.to_list(length=500)
        return []
    
    @staticmethod
    async def cancel_reminders_for_invoice(invoice_id: str) -> int:
        """Cancel all pending reminders for an invoice (e.g., when paid)"""
        if is_mongodb():
            result = await db.invoice_reminders.update_many(
                {"invoice_id": invoice_id, "status": "pending"},
                {"$set": {"status": "cancelled"}}
            )
            return result.modified_count
        return 0
    
    @staticmethod
    async def send_reminder(reminder: Dict[str, Any]) -> Dict[str, Any]:
        """Send a reminder email"""
        from app.services.email_service import send_email
        
        invoice_id = reminder["invoice_id"]
        reminder_type = reminder["reminder_type"]
        
        if is_mongodb():
            # Get invoice
            invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
            if not invoice:
                return {"success": False, "error": "Invoice not found"}
            
            # Check if invoice is already paid
            if invoice.get("status") == "paid":
                await InvoiceReminderService.cancel_reminders_for_invoice(invoice_id)
                return {"success": False, "error": "Invoice already paid"}
            
            # Get client
            client = await db.clients.find_one({"id": invoice.get("client_id")}, {"_id": 0})
            if not client or not client.get("email"):
                return {"success": False, "error": "Client email not found"}
            
            # Get user settings for company info
            user_settings = await db.user_settings.find_one(
                {"user_id": invoice["user_id"]},
                {"_id": 0}
            )
            
            # Get template
            template = REMINDER_TEMPLATES.get(reminder_type)
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Format due date
            due_date_str = invoice.get("due_date", "")
            try:
                due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                due_date_formatted = due_date.strftime("%d/%m/%Y")
            except:
                due_date_formatted = due_date_str
            
            # Build email content
            amount_due = invoice.get("total_ttc", 0) - invoice.get("amount_paid", 0)
            
            replacements = {
                "invoice_number": invoice.get("invoice_number", ""),
                "client_name": client.get("company_name") or client.get("name", ""),
                "amount": f"{amount_due:.2f}",
                "due_date": due_date_formatted,
                "company_name": user_settings.get("company_name", "BTP Facture") if user_settings else "BTP Facture"
            }
            
            subject = template["subject"]
            body = template["body"]
            
            for key, value in replacements.items():
                subject = subject.replace(f"{{{key}}}", str(value))
                body = body.replace(f"{{{key}}}", str(value))
            
            # Send email
            try:
                await send_email(
                    to_email=client["email"],
                    subject=subject,
                    body=body
                )
                
                # Update reminder status
                await db.invoice_reminders.update_one(
                    {"id": reminder["id"]},
                    {
                        "$set": {
                            "status": "sent",
                            "sent_at": datetime.now(timezone.utc).isoformat(),
                            "email_subject": subject,
                            "email_body": body
                        }
                    }
                )
                
                return {"success": True, "reminder_id": reminder["id"]}
                
            except Exception as e:
                logger.error(f"Error sending reminder {reminder['id']}: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Database not available"}
    
    @staticmethod
    async def process_pending_reminders() -> Dict[str, Any]:
        """Process all pending reminders"""
        results = {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        pending = await InvoiceReminderService.get_pending_reminders()
        
        for reminder in pending:
            results["processed"] += 1
            
            result = await InvoiceReminderService.send_reminder(reminder)
            
            if result.get("success"):
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "reminder_id": reminder["id"],
                    "error": result.get("error")
                })
        
        return results
    
    @staticmethod
    async def get_reminder_history(user_id: str, invoice_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get reminder history"""
        query = {"user_id": user_id}
        if invoice_id:
            query["invoice_id"] = invoice_id
        
        if is_mongodb():
            cursor = db.invoice_reminders.find(query, {"_id": 0}).sort("created_at", -1).limit(100)
            return await cursor.to_list(length=100)
        return []


# Create singleton instance
invoice_reminder_service = InvoiceReminderService()
