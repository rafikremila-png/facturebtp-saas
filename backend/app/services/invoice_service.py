"""
Invoice Service
Handles invoices including BTP progress invoicing (factures de situation)
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging

from app.core.database import db, is_mongodb
from app.services.vat_service import vat_service

logger = logging.getLogger(__name__)

class InvoiceService:
    """Service for managing invoices"""
    
    @staticmethod
    async def generate_invoice_number(user_id: str) -> str:
        """Generate unique invoice number"""
        year = datetime.now().year
        
        # Get user prefix
        prefix = "FAC"
        if is_mongodb():
            settings = await db.user_settings.find_one({"user_id": user_id}, {"invoice_prefix": 1})
            if settings and settings.get("invoice_prefix"):
                prefix = settings["invoice_prefix"]
            
            count = await db.invoices.count_documents({
                "user_id": user_id,
                "created_at": {"$regex": f"^{year}"}
            })
        else:
            count = 0
        
        return f"{prefix}-{year}-{(count + 1):05d}"
    
    @staticmethod
    async def create(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new invoice"""
        invoice_number = await InvoiceService.generate_invoice_number(user_id)
        
        # Get user settings for defaults
        user_settings = None
        if is_mongodb():
            user_settings = await db.user_settings.find_one({"user_id": user_id}, {"_id": 0})
        
        # Calculate due date
        payment_days = data.get("payment_days")
        if not payment_days and user_settings:
            payment_days = user_settings.get("default_payment_days", 30)
        else:
            payment_days = payment_days or 30
        
        invoice_date = datetime.now(timezone.utc)
        due_date = data.get("due_date") or (invoice_date + timedelta(days=payment_days))
        
        # Calculate totals
        items = data.get("items", [])
        invoice_type = data.get("invoice_type", "standard")
        
        if invoice_type == "situation":
            # Progress invoice calculation
            progress_percentage = data.get("progress_percentage", 100)
            previous_invoiced = data.get("previous_invoiced", 0)
            
            totals = vat_service.calculate_situation_invoice(
                items,
                progress_percentage,
                previous_invoiced,
                data.get("discount_type"),
                data.get("discount_value", 0),
                data.get("retention_rate", 0)
            )
            
            subtotal_ht = totals["current_amount_ht"]
            total_vat = totals["current_vat"]
            total_ttc = totals["current_ttc"]
            retention_amount = totals["retention_amount"]
        else:
            # Standard invoice calculation
            totals = vat_service.calculate_document_totals(
                items,
                data.get("discount_type"),
                data.get("discount_value", 0),
                data.get("retention_rate", 0)
            )
            
            subtotal_ht = totals["subtotal_after_discount"]
            total_vat = totals["total_vat"]
            total_ttc = totals["total_ttc"]
            retention_amount = totals["retention_amount"]
            progress_percentage = 100
            previous_invoiced = 0
        
        invoice = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "client_id": data.get("client_id"),
            "project_id": data.get("project_id"),
            "quote_id": data.get("quote_id"),
            "invoice_number": invoice_number,
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "status": "draft",
            "invoice_date": invoice_date.isoformat(),
            "due_date": due_date.isoformat() if isinstance(due_date, datetime) else due_date,
            "paid_date": None,
            "items": items,
            "subtotal_ht": subtotal_ht,
            "total_vat": total_vat,
            "total_ttc": total_ttc,
            "discount_type": data.get("discount_type"),
            "discount_value": data.get("discount_value", 0),
            "discount_amount": totals.get("discount_amount", 0),
            "invoice_type": invoice_type,
            "situation_number": data.get("situation_number"),
            "progress_percentage": progress_percentage,
            "previous_invoiced": previous_invoiced,
            "current_amount": subtotal_ht,
            "retention_rate": data.get("retention_rate", 0),
            "retention_amount": retention_amount,
            "retention_released": False,
            "amount_paid": 0,
            "amount_due": total_ttc - retention_amount,
            "stripe_payment_id": None,
            "stripe_checkout_session_id": None,
            "notes": data.get("notes", ""),
            "payment_terms": data.get("payment_terms", ""),
            "pdf_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if is_mongodb():
            await db.invoices.insert_one(invoice.copy())
            
            # Update project totals if linked
            if invoice.get("project_id"):
                from app.services.project_service import project_service
                await project_service.update_financials(invoice["project_id"], user_id)
        
        return invoice
    
    @staticmethod
    async def get_by_id(invoice_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice by ID"""
        if is_mongodb():
            invoice = await db.invoices.find_one(
                {"id": invoice_id, "user_id": user_id},
                {"_id": 0}
            )
            if invoice:
                # Get client
                if invoice.get("client_id"):
                    client = await db.clients.find_one({"id": invoice["client_id"]}, {"_id": 0})
                    invoice["client"] = client
                # Get project
                if invoice.get("project_id"):
                    project = await db.projects.find_one({"id": invoice["project_id"]}, {"_id": 0})
                    invoice["project"] = project
            return invoice
        return None
    
    @staticmethod
    async def get_all(user_id: str, status: Optional[str] = None,
                      client_id: Optional[str] = None,
                      project_id: Optional[str] = None,
                      skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all invoices for a user"""
        query = {"user_id": user_id}
        
        if status:
            query["status"] = status
        if client_id:
            query["client_id"] = client_id
        if project_id:
            query["project_id"] = project_id
        
        if is_mongodb():
            cursor = db.invoices.find(query, {"_id": 0}).sort("invoice_date", -1).skip(skip).limit(limit)
            invoices = await cursor.to_list(length=limit)
            
            # Get clients
            client_ids = list(set(i.get("client_id") for i in invoices if i.get("client_id")))
            if client_ids:
                clients_cursor = db.clients.find({"id": {"$in": client_ids}}, {"_id": 0})
                clients = {c["id"]: c for c in await clients_cursor.to_list(length=100)}
                for invoice in invoices:
                    if invoice.get("client_id"):
                        invoice["client"] = clients.get(invoice["client_id"])
            
            return invoices
        return []
    
    @staticmethod
    async def update(invoice_id: str, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an invoice"""
        # Get existing invoice
        invoice = await InvoiceService.get_by_id(invoice_id, user_id)
        if not invoice:
            return None
        
        # Don't allow updating paid invoices
        if invoice.get("status") == "paid" and "status" not in data:
            pass  # Allow status changes
        
        update_data = {k: v for k, v in data.items() if v is not None}
        
        # Recalculate if items changed
        if "items" in update_data:
            invoice_type = update_data.get("invoice_type", invoice.get("invoice_type", "standard"))
            
            if invoice_type == "situation":
                totals = vat_service.calculate_situation_invoice(
                    update_data["items"],
                    update_data.get("progress_percentage", invoice.get("progress_percentage", 100)),
                    update_data.get("previous_invoiced", invoice.get("previous_invoiced", 0)),
                    update_data.get("discount_type", invoice.get("discount_type")),
                    update_data.get("discount_value", invoice.get("discount_value", 0)),
                    update_data.get("retention_rate", invoice.get("retention_rate", 0))
                )
                update_data.update({
                    "subtotal_ht": totals["current_amount_ht"],
                    "total_vat": totals["current_vat"],
                    "total_ttc": totals["current_ttc"],
                    "retention_amount": totals["retention_amount"],
                    "amount_due": totals["net_to_pay"] - invoice.get("amount_paid", 0)
                })
            else:
                totals = vat_service.calculate_document_totals(
                    update_data["items"],
                    update_data.get("discount_type", invoice.get("discount_type")),
                    update_data.get("discount_value", invoice.get("discount_value", 0)),
                    update_data.get("retention_rate", invoice.get("retention_rate", 0))
                )
                update_data.update({
                    "subtotal_ht": totals["subtotal_after_discount"],
                    "total_vat": totals["total_vat"],
                    "total_ttc": totals["total_ttc"],
                    "discount_amount": totals["discount_amount"],
                    "retention_amount": totals["retention_amount"],
                    "amount_due": totals["net_to_pay"] - invoice.get("amount_paid", 0)
                })
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        if is_mongodb():
            result = await db.invoices.update_one(
                {"id": invoice_id, "user_id": user_id},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                return await InvoiceService.get_by_id(invoice_id, user_id)
        
        return None
    
    @staticmethod
    async def delete(invoice_id: str, user_id: str) -> bool:
        """Delete an invoice"""
        if is_mongodb():
            # Get invoice first for project update
            invoice = await db.invoices.find_one({"id": invoice_id, "user_id": user_id})
            project_id = invoice.get("project_id") if invoice else None
            
            result = await db.invoices.delete_one(
                {"id": invoice_id, "user_id": user_id}
            )
            
            if result.deleted_count > 0 and project_id:
                from app.services.project_service import project_service
                await project_service.update_financials(project_id, user_id)
            
            return result.deleted_count > 0
        return False
    
    @staticmethod
    async def mark_as_sent(invoice_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Mark invoice as sent"""
        return await InvoiceService.update(invoice_id, user_id, {"status": "sent"})
    
    @staticmethod
    async def record_payment(invoice_id: str, user_id: str, amount: float, 
                             payment_method: str = "bank_transfer",
                             reference: str = None,
                             stripe_payment_id: str = None) -> Dict[str, Any]:
        """Record a payment for an invoice"""
        invoice = await InvoiceService.get_by_id(invoice_id, user_id)
        if not invoice:
            raise ValueError("Facture non trouvée")
        
        # Create payment record
        payment = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "invoice_id": invoice_id,
            "amount": amount,
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "payment_method": payment_method,
            "reference": reference,
            "transaction_id": stripe_payment_id,
            "stripe_payment_intent_id": stripe_payment_id,
            "notes": "",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if is_mongodb():
            await db.payments.insert_one(payment.copy())
        
        # Update invoice
        new_amount_paid = invoice.get("amount_paid", 0) + amount
        net_amount = invoice.get("total_ttc", 0) - invoice.get("retention_amount", 0)
        new_amount_due = net_amount - new_amount_paid
        
        new_status = invoice.get("status")
        if new_amount_due <= 0:
            new_status = "paid"
        elif new_amount_paid > 0:
            new_status = "partial"
        
        update_data = {
            "amount_paid": new_amount_paid,
            "amount_due": max(0, new_amount_due),
            "status": new_status
        }
        
        if new_status == "paid":
            update_data["paid_date"] = datetime.now(timezone.utc).isoformat()
        
        if stripe_payment_id:
            update_data["stripe_payment_id"] = stripe_payment_id
        
        await InvoiceService.update(invoice_id, user_id, update_data)
        
        # Update project financials
        if invoice.get("project_id"):
            from app.services.project_service import project_service
            await project_service.update_financials(invoice["project_id"], user_id)
        
        # Cancel reminders if fully paid
        if new_status == "paid":
            from app.services.invoice_reminder_service import invoice_reminder_service
            await invoice_reminder_service.cancel_reminders_for_invoice(invoice_id)
        
        return {
            "payment": payment,
            "invoice_status": new_status,
            "amount_paid": new_amount_paid,
            "amount_due": max(0, new_amount_due)
        }
    
    @staticmethod
    async def create_situation_invoice(user_id: str, project_id: str,
                                        progress_percentage: float,
                                        items: List[Dict[str, Any]],
                                        retention_rate: float = 5.0) -> Dict[str, Any]:
        """Create a progress invoice (facture de situation)"""
        # Get previous situation invoices
        if is_mongodb():
            previous = await db.invoices.find({
                "user_id": user_id,
                "project_id": project_id,
                "invoice_type": "situation",
                "status": {"$ne": "cancelled"}
            }, {"_id": 0, "situation_number": 1, "progress_percentage": 1, "subtotal_ht": 1}).to_list(length=100)
        else:
            previous = []
        
        # Calculate previous invoiced amount
        previous_invoiced = sum(inv.get("subtotal_ht", 0) for inv in previous)
        situation_number = len(previous) + 1
        
        # Get project
        project = None
        client_id = None
        if is_mongodb():
            project = await db.projects.find_one({"id": project_id, "user_id": user_id})
            if project:
                client_id = project.get("client_id")
        
        return await InvoiceService.create(user_id, {
            "project_id": project_id,
            "client_id": client_id,
            "title": f"Situation n°{situation_number}" + (f" - {project['project_name']}" if project else ""),
            "items": items,
            "invoice_type": "situation",
            "situation_number": situation_number,
            "progress_percentage": progress_percentage,
            "previous_invoiced": previous_invoiced,
            "retention_rate": retention_rate
        })


# Create singleton instance
invoice_service = InvoiceService()
