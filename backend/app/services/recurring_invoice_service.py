"""
Recurring Invoice Service
Automatic recurring invoice generation
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import logging

from app.core.database import db, is_mongodb
from app.services.vat_service import vat_service

logger = logging.getLogger(__name__)

class RecurringInvoiceService:
    """Service for managing recurring invoices"""
    
    @staticmethod
    def calculate_next_date(current_date: datetime, frequency: str) -> datetime:
        """Calculate next invoice date based on frequency"""
        if frequency == "monthly":
            return current_date + relativedelta(months=1)
        elif frequency == "quarterly":
            return current_date + relativedelta(months=3)
        elif frequency == "yearly":
            return current_date + relativedelta(years=1)
        else:
            return current_date + relativedelta(months=1)
    
    @staticmethod
    async def create(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new recurring invoice template"""
        # Calculate totals
        items = data.get("items", [])
        totals = vat_service.calculate_document_totals(items)
        
        start_date = data["start_date"]
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        
        recurring = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "client_id": data["client_id"],
            "title": data["title"],
            "description": data.get("description", ""),
            "items": items,
            "subtotal_ht": totals["subtotal_ht"],
            "total_vat": totals["total_vat"],
            "total_ttc": totals["total_ttc"],
            "frequency": data.get("frequency", "monthly"),
            "start_date": start_date.isoformat(),
            "end_date": data.get("end_date"),
            "next_invoice_date": start_date.isoformat(),
            "last_invoice_date": None,
            "status": "active",
            "invoices_generated": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if is_mongodb():
            await db.recurring_invoices.insert_one(recurring.copy())
        
        return recurring
    
    @staticmethod
    async def get_by_id(recurring_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get recurring invoice by ID"""
        if is_mongodb():
            recurring = await db.recurring_invoices.find_one(
                {"id": recurring_id, "user_id": user_id},
                {"_id": 0}
            )
            if recurring:
                # Get client
                client = await db.clients.find_one(
                    {"id": recurring["client_id"]},
                    {"_id": 0}
                )
                recurring["client"] = client
            return recurring
        return None
    
    @staticmethod
    async def get_all(user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all recurring invoices for a user"""
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        if is_mongodb():
            cursor = db.recurring_invoices.find(query, {"_id": 0}).sort("created_at", -1)
            recurring_list = await cursor.to_list(length=100)
            
            # Get clients
            client_ids = list(set(r.get("client_id") for r in recurring_list if r.get("client_id")))
            if client_ids:
                clients_cursor = db.clients.find({"id": {"$in": client_ids}}, {"_id": 0})
                clients = {c["id"]: c for c in await clients_cursor.to_list(length=100)}
                for recurring in recurring_list:
                    if recurring.get("client_id"):
                        recurring["client"] = clients.get(recurring["client_id"])
            
            return recurring_list
        return []
    
    @staticmethod
    async def update(recurring_id: str, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a recurring invoice"""
        update_data = {k: v for k, v in data.items() if v is not None}
        
        # Recalculate totals if items changed
        if "items" in update_data:
            totals = vat_service.calculate_document_totals(update_data["items"])
            update_data.update({
                "subtotal_ht": totals["subtotal_ht"],
                "total_vat": totals["total_vat"],
                "total_ttc": totals["total_ttc"]
            })
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        if is_mongodb():
            result = await db.recurring_invoices.update_one(
                {"id": recurring_id, "user_id": user_id},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                return await RecurringInvoiceService.get_by_id(recurring_id, user_id)
        return None
    
    @staticmethod
    async def pause(recurring_id: str, user_id: str) -> bool:
        """Pause a recurring invoice"""
        if is_mongodb():
            result = await db.recurring_invoices.update_one(
                {"id": recurring_id, "user_id": user_id, "status": "active"},
                {
                    "$set": {
                        "status": "paused",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            return result.modified_count > 0
        return False
    
    @staticmethod
    async def resume(recurring_id: str, user_id: str) -> bool:
        """Resume a paused recurring invoice"""
        if is_mongodb():
            result = await db.recurring_invoices.update_one(
                {"id": recurring_id, "user_id": user_id, "status": "paused"},
                {
                    "$set": {
                        "status": "active",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            return result.modified_count > 0
        return False
    
    @staticmethod
    async def delete(recurring_id: str, user_id: str) -> bool:
        """Delete a recurring invoice"""
        if is_mongodb():
            result = await db.recurring_invoices.delete_one(
                {"id": recurring_id, "user_id": user_id}
            )
            return result.deleted_count > 0
        return False
    
    @staticmethod
    async def generate_invoice_from_recurring(recurring: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a new invoice from a recurring template"""
        from app.services.invoice_service import invoice_service
        
        user_id = recurring["user_id"]
        
        # Create invoice data
        invoice_data = {
            "client_id": recurring["client_id"],
            "title": recurring["title"],
            "description": recurring.get("description", ""),
            "items": recurring["items"],
            "notes": f"Facture récurrente - {recurring['title']}"
        }
        
        # Generate the invoice
        invoice = await invoice_service.create(user_id, invoice_data)
        
        # Update recurring invoice
        now = datetime.now(timezone.utc)
        next_date = RecurringInvoiceService.calculate_next_date(now, recurring["frequency"])
        
        # Check if we've reached the end date
        end_date = recurring.get("end_date")
        new_status = "active"
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            if next_date > end_date:
                new_status = "completed"
        
        if is_mongodb():
            await db.recurring_invoices.update_one(
                {"id": recurring["id"]},
                {
                    "$set": {
                        "last_invoice_date": now.isoformat(),
                        "next_invoice_date": next_date.isoformat(),
                        "status": new_status,
                        "updated_at": now.isoformat()
                    },
                    "$inc": {"invoices_generated": 1}
                }
            )
        
        return invoice
    
    @staticmethod
    async def process_due_recurring_invoices() -> Dict[str, Any]:
        """Process all recurring invoices that are due today"""
        results = {
            "processed": 0,
            "success": 0,
            "errors": []
        }
        
        if is_mongodb():
            now = datetime.now(timezone.utc)
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            # Find all active recurring invoices due today
            cursor = db.recurring_invoices.find({
                "status": "active",
                "next_invoice_date": {
                    "$gte": today.isoformat(),
                    "$lt": tomorrow.isoformat()
                }
            }, {"_id": 0})
            
            recurring_list = await cursor.to_list(length=100)
            
            for recurring in recurring_list:
                results["processed"] += 1
                try:
                    await RecurringInvoiceService.generate_invoice_from_recurring(recurring)
                    results["success"] += 1
                except Exception as e:
                    logger.error(f"Error generating recurring invoice {recurring['id']}: {e}")
                    results["errors"].append({
                        "recurring_id": recurring["id"],
                        "error": str(e)
                    })
        
        return results


# Create singleton instance
recurring_invoice_service = RecurringInvoiceService()
