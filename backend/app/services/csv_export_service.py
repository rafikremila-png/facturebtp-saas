"""
CSV Export Service for BTP Facture
Handles accounting CSV exports (Pro plan feature)
"""

import logging
import csv
import io
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class CSVExportService:
    """Service for generating accounting CSV exports"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.invoices = db.invoices
        self.quotes = db.quotes
        self.clients = db.clients
        self.users = db.users
    
    async def check_user_has_export_feature(self, user_id: str) -> bool:
        """Check if user's plan includes CSV export"""
        user = await self.users.find_one({"id": user_id})
        if not user:
            return False
        
        plan = user.get("subscription_plan", "trial")
        status = user.get("subscription_status", "trial")
        
        # Only Pro and Business plans have CSV export
        if plan in ["pro", "business"] and status == "active":
            return True
        
        return False
    
    def _format_date(self, date_str: Optional[str]) -> str:
        """Format date for CSV"""
        if not date_str:
            return ""
        try:
            if isinstance(date_str, str):
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                dt = date_str
            return dt.strftime("%d/%m/%Y")
        except:
            return date_str
    
    def _format_amount(self, amount: Optional[float]) -> str:
        """Format amount for CSV"""
        if amount is None:
            return "0.00"
        return f"{amount:.2f}"
    
    async def export_invoices_csv(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> str:
        """Export invoices to CSV format"""
        
        # Build query
        query = {"owner_id": user_id}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["issue_date"] = date_query
        
        if status_filter:
            query["status"] = status_filter
        
        # Fetch invoices
        invoices = []
        cursor = self.invoices.find(query).sort("issue_date", 1)
        async for doc in cursor:
            invoices.append(doc)
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
        
        # Header row
        headers = [
            "Numéro facture",
            "Date émission",
            "Date échéance",
            "Client",
            "Email client",
            "Total HT",
            "Total TVA",
            "Total TTC",
            "Statut paiement",
            "Mode paiement",
            "Référence devis",
            "Type"
        ]
        writer.writerow(headers)
        
        # Data rows
        for invoice in invoices:
            # Get client info
            client_name = invoice.get("client_name", "")
            client_id = invoice.get("client_id")
            client_email = ""
            if client_id:
                client = await self.clients.find_one({"id": client_id})
                if client:
                    client_email = client.get("email", "")
            
            row = [
                invoice.get("invoice_number", ""),
                self._format_date(invoice.get("issue_date")),
                self._format_date(invoice.get("due_date")),
                client_name,
                client_email,
                self._format_amount(invoice.get("total_ht")),
                self._format_amount(invoice.get("total_vat")),
                self._format_amount(invoice.get("total_ttc")),
                invoice.get("status", "impayé"),
                invoice.get("payment_method", ""),
                invoice.get("quote_number", ""),
                invoice.get("invoice_type", "standard")
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    async def export_quotes_csv(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> str:
        """Export quotes to CSV format"""
        
        # Build query
        query = {"owner_id": user_id}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["issue_date"] = date_query
        
        if status_filter:
            query["status"] = status_filter
        
        # Fetch quotes
        quotes = []
        cursor = self.quotes.find(query).sort("issue_date", 1)
        async for doc in cursor:
            quotes.append(doc)
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
        
        # Header row
        headers = [
            "Numéro devis",
            "Date émission",
            "Date validité",
            "Client",
            "Email client",
            "Total HT",
            "Total TVA",
            "Total TTC",
            "Statut",
            "Converti en facture"
        ]
        writer.writerow(headers)
        
        # Data rows
        for quote in quotes:
            # Get client info
            client_name = quote.get("client_name", "")
            client_id = quote.get("client_id")
            client_email = ""
            if client_id:
                client = await self.clients.find_one({"id": client_id})
                if client:
                    client_email = client.get("email", "")
            
            row = [
                quote.get("quote_number", ""),
                self._format_date(quote.get("issue_date")),
                self._format_date(quote.get("validity_date")),
                client_name,
                client_email,
                self._format_amount(quote.get("total_ht")),
                self._format_amount(quote.get("total_vat")),
                self._format_amount(quote.get("total_ttc")),
                quote.get("status", "brouillon"),
                "Oui" if quote.get("converted_to_invoice") else "Non"
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    async def export_clients_csv(self, user_id: str) -> str:
        """Export clients to CSV format"""
        
        # Fetch clients
        clients = []
        cursor = self.clients.find({"owner_id": user_id}).sort("name", 1)
        async for doc in cursor:
            clients.append(doc)
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
        
        # Header row
        headers = [
            "Nom",
            "Email",
            "Téléphone",
            "Adresse",
            "Code postal",
            "Ville",
            "SIRET",
            "TVA Intracommunautaire",
            "Date création"
        ]
        writer.writerow(headers)
        
        # Data rows
        for client in clients:
            row = [
                client.get("name", ""),
                client.get("email", ""),
                client.get("phone", ""),
                client.get("address", ""),
                client.get("postal_code", ""),
                client.get("city", ""),
                client.get("siret", ""),
                client.get("vat_number", ""),
                self._format_date(client.get("created_at"))
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    async def export_accounting_summary_csv(
        self,
        user_id: str,
        year: int,
        month: Optional[int] = None
    ) -> str:
        """Export monthly accounting summary"""
        
        # Determine date range
        if month:
            start_date = datetime(year, month, 1, tzinfo=timezone.utc)
            if month == 12:
                end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        else:
            start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        
        # Fetch invoices in date range
        query = {
            "owner_id": user_id,
            "issue_date": {
                "$gte": start_date.isoformat(),
                "$lt": end_date.isoformat()
            }
        }
        
        invoices = []
        cursor = self.invoices.find(query)
        async for doc in cursor:
            invoices.append(doc)
        
        # Calculate totals
        total_ht = sum(inv.get("total_ht", 0) for inv in invoices)
        total_vat = sum(inv.get("total_vat", 0) for inv in invoices)
        total_ttc = sum(inv.get("total_ttc", 0) for inv in invoices)
        
        paid_invoices = [inv for inv in invoices if inv.get("status") == "payé"]
        total_paid_ht = sum(inv.get("total_ht", 0) for inv in paid_invoices)
        total_paid_ttc = sum(inv.get("total_ttc", 0) for inv in paid_invoices)
        
        unpaid_invoices = [inv for inv in invoices if inv.get("status") in ["impayé", "partiel"]]
        total_unpaid_ht = sum(inv.get("total_ht", 0) for inv in unpaid_invoices)
        total_unpaid_ttc = sum(inv.get("total_ttc", 0) for inv in unpaid_invoices)
        
        # Calculate VAT by rate
        vat_by_rate = {}
        for inv in invoices:
            for item in inv.get("items", []):
                rate = item.get("vat_rate", 20)
                amount = item.get("quantity", 1) * item.get("unit_price", 0) * (rate / 100)
                vat_by_rate[rate] = vat_by_rate.get(rate, 0) + amount
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
        
        # Title
        period_label = f"{month:02d}/{year}" if month else str(year)
        writer.writerow([f"Récapitulatif comptable - {period_label}"])
        writer.writerow([])
        
        # Summary section
        writer.writerow(["RÉSUMÉ GLOBAL"])
        writer.writerow(["Indicateur", "Montant"])
        writer.writerow(["Nombre de factures", len(invoices)])
        writer.writerow(["Total HT", self._format_amount(total_ht)])
        writer.writerow(["Total TVA", self._format_amount(total_vat)])
        writer.writerow(["Total TTC", self._format_amount(total_ttc)])
        writer.writerow([])
        
        # Payment status
        writer.writerow(["ÉTAT DES PAIEMENTS"])
        writer.writerow(["Statut", "Nombre", "Total HT", "Total TTC"])
        writer.writerow(["Payé", len(paid_invoices), self._format_amount(total_paid_ht), self._format_amount(total_paid_ttc)])
        writer.writerow(["Impayé/Partiel", len(unpaid_invoices), self._format_amount(total_unpaid_ht), self._format_amount(total_unpaid_ttc)])
        writer.writerow([])
        
        # VAT breakdown
        writer.writerow(["DÉTAIL TVA"])
        writer.writerow(["Taux TVA", "Montant"])
        for rate, amount in sorted(vat_by_rate.items()):
            writer.writerow([f"{rate}%", self._format_amount(amount)])
        writer.writerow(["TOTAL TVA", self._format_amount(total_vat)])
        
        return output.getvalue()


def get_csv_export_service(db: AsyncIOMotorDatabase) -> CSVExportService:
    """Factory function"""
    return CSVExportService(db)
