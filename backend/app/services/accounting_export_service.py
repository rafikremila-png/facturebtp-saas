"""
Accounting Export Service
CSV/Excel export for accounting
"""
import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from app.core.config import settings
from app.core.database import db, is_mongodb

logger = logging.getLogger(__name__)

class AccountingExportService:
    """Service for accounting data export"""
    
    @staticmethod
    async def export_invoices(user_id: str, start_date: datetime, end_date: datetime,
                              format: str = "csv") -> Dict[str, Any]:
        """Export invoices for accounting"""
        invoices = []
        
        if is_mongodb():
            cursor = db.invoices.find({
                "user_id": user_id,
                "invoice_date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                },
                "status": {"$ne": "draft"}
            }, {"_id": 0}).sort("invoice_date", 1)
            
            invoices = await cursor.to_list(length=10000)
            
            # Get clients
            client_ids = list(set(inv.get("client_id") for inv in invoices if inv.get("client_id")))
            clients = {}
            if client_ids:
                clients_cursor = db.clients.find({"id": {"$in": client_ids}}, {"_id": 0})
                clients = {c["id"]: c for c in await clients_cursor.to_list(length=1000)}
        
        # Build export data
        export_rows = []
        
        for inv in invoices:
            client = clients.get(inv.get("client_id"), {})
            
            # Format dates
            invoice_date = inv.get("invoice_date", "")[:10] if inv.get("invoice_date") else ""
            due_date = inv.get("due_date", "")[:10] if inv.get("due_date") else ""
            paid_date = inv.get("paid_date", "")[:10] if inv.get("paid_date") else ""
            
            row = {
                "Date facture": invoice_date,
                "N° facture": inv.get("invoice_number", ""),
                "Client": client.get("company_name") or client.get("name", ""),
                "SIRET client": client.get("siret", ""),
                "N° TVA client": client.get("vat_number", ""),
                "Montant HT": round(inv.get("subtotal_ht", 0), 2),
                "TVA": round(inv.get("total_vat", 0), 2),
                "Montant TTC": round(inv.get("total_ttc", 0), 2),
                "Statut": inv.get("status", ""),
                "Date échéance": due_date,
                "Date paiement": paid_date,
                "Montant payé": round(inv.get("amount_paid", 0), 2),
                "Reste dû": round(inv.get("total_ttc", 0) - inv.get("amount_paid", 0), 2)
            }
            export_rows.append(row)
        
        # Generate file
        if format == "csv":
            return AccountingExportService._generate_csv(export_rows, "factures")
        else:
            return AccountingExportService._generate_excel(export_rows, "factures")
    
    @staticmethod
    async def export_payments(user_id: str, start_date: datetime, end_date: datetime,
                              format: str = "csv") -> Dict[str, Any]:
        """Export payments for accounting"""
        payments = []
        
        if is_mongodb():
            cursor = db.payments.find({
                "user_id": user_id,
                "payment_date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }, {"_id": 0}).sort("payment_date", 1)
            
            payments = await cursor.to_list(length=10000)
            
            # Get invoices
            invoice_ids = list(set(p.get("invoice_id") for p in payments if p.get("invoice_id")))
            invoices = {}
            if invoice_ids:
                inv_cursor = db.invoices.find({"id": {"$in": invoice_ids}}, {"_id": 0})
                invoices = {i["id"]: i for i in await inv_cursor.to_list(length=1000)}
            
            # Get clients
            client_ids = list(set(invoices.get(p.get("invoice_id"), {}).get("client_id") for p in payments))
            clients = {}
            if client_ids:
                clients_cursor = db.clients.find({"id": {"$in": client_ids}}, {"_id": 0})
                clients = {c["id"]: c for c in await clients_cursor.to_list(length=1000)}
        
        # Build export data
        export_rows = []
        
        payment_methods = {
            "bank_transfer": "Virement",
            "check": "Chèque",
            "cash": "Espèces",
            "card": "Carte",
            "stripe": "Stripe"
        }
        
        for payment in payments:
            invoice = invoices.get(payment.get("invoice_id"), {})
            client = clients.get(invoice.get("client_id"), {})
            
            payment_date = payment.get("payment_date", "")[:10] if payment.get("payment_date") else ""
            
            row = {
                "Date paiement": payment_date,
                "N° facture": invoice.get("invoice_number", ""),
                "Client": client.get("company_name") or client.get("name", ""),
                "Montant": round(payment.get("amount", 0), 2),
                "Mode de paiement": payment_methods.get(payment.get("payment_method"), payment.get("payment_method", "")),
                "Référence": payment.get("reference", ""),
                "Transaction ID": payment.get("transaction_id", "")
            }
            export_rows.append(row)
        
        # Generate file
        if format == "csv":
            return AccountingExportService._generate_csv(export_rows, "paiements")
        else:
            return AccountingExportService._generate_excel(export_rows, "paiements")
    
    @staticmethod
    async def export_vat(user_id: str, start_date: datetime, end_date: datetime,
                         format: str = "csv") -> Dict[str, Any]:
        """Export VAT summary for accounting"""
        vat_data = []
        
        if is_mongodb():
            cursor = db.invoices.find({
                "user_id": user_id,
                "invoice_date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                },
                "status": {"$in": ["sent", "paid", "partial"]}
            }, {"_id": 0, "invoice_number": 1, "invoice_date": 1, "items": 1, 
                "subtotal_ht": 1, "total_vat": 1, "total_ttc": 1}).sort("invoice_date", 1)
            
            invoices = await cursor.to_list(length=10000)
        
        # Build VAT breakdown
        export_rows = []
        vat_totals = {}
        
        for inv in invoices:
            invoice_date = inv.get("invoice_date", "")[:10] if inv.get("invoice_date") else ""
            
            # Break down by VAT rate
            vat_by_rate = {}
            for item in inv.get("items", []):
                rate = item.get("vat_rate", 20.0)
                quantity = item.get("quantity", 1)
                unit_price = item.get("unit_price", 0)
                item_ht = quantity * unit_price
                item_vat = item_ht * rate / 100
                
                if rate not in vat_by_rate:
                    vat_by_rate[rate] = {"base_ht": 0, "vat": 0}
                vat_by_rate[rate]["base_ht"] += item_ht
                vat_by_rate[rate]["vat"] += item_vat
                
                # Accumulate totals
                if rate not in vat_totals:
                    vat_totals[rate] = {"base_ht": 0, "vat": 0}
                vat_totals[rate]["base_ht"] += item_ht
                vat_totals[rate]["vat"] += item_vat
            
            for rate, amounts in vat_by_rate.items():
                row = {
                    "Date": invoice_date,
                    "N° facture": inv.get("invoice_number", ""),
                    "Taux TVA (%)": rate,
                    "Base HT": round(amounts["base_ht"], 2),
                    "Montant TVA": round(amounts["vat"], 2)
                }
                export_rows.append(row)
        
        # Add totals
        export_rows.append({})  # Empty row
        export_rows.append({
            "Date": "TOTAUX",
            "N° facture": "",
            "Taux TVA (%)": "",
            "Base HT": "",
            "Montant TVA": ""
        })
        
        for rate, amounts in sorted(vat_totals.items()):
            export_rows.append({
                "Date": "",
                "N° facture": f"TVA {rate}%",
                "Taux TVA (%)": rate,
                "Base HT": round(amounts["base_ht"], 2),
                "Montant TVA": round(amounts["vat"], 2)
            })
        
        # Grand total
        total_ht = sum(a["base_ht"] for a in vat_totals.values())
        total_vat = sum(a["vat"] for a in vat_totals.values())
        export_rows.append({
            "Date": "",
            "N° facture": "TOTAL",
            "Taux TVA (%)": "",
            "Base HT": round(total_ht, 2),
            "Montant TVA": round(total_vat, 2)
        })
        
        # Generate file
        if format == "csv":
            return AccountingExportService._generate_csv(export_rows, "tva")
        else:
            return AccountingExportService._generate_excel(export_rows, "tva")
    
    @staticmethod
    async def export_full_accounting(user_id: str, start_date: datetime, end_date: datetime,
                                     format: str = "csv") -> Dict[str, Any]:
        """Export complete accounting data"""
        # Get all data
        invoices_export = await AccountingExportService.export_invoices(user_id, start_date, end_date, format)
        payments_export = await AccountingExportService.export_payments(user_id, start_date, end_date, format)
        vat_export = await AccountingExportService.export_vat(user_id, start_date, end_date, format)
        
        # For CSV, combine into a single file with sections
        if format == "csv":
            combined_content = "=== FACTURES ===\n"
            combined_content += invoices_export.get("content", "")
            combined_content += "\n\n=== PAIEMENTS ===\n"
            combined_content += payments_export.get("content", "")
            combined_content += "\n\n=== TVA ===\n"
            combined_content += vat_export.get("content", "")
            
            filename = f"export_comptable_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            
            # Save file
            export_path = settings.STORAGE_PATH / "exports"
            export_path.mkdir(exist_ok=True)
            
            file_path = export_path / filename
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.write(combined_content)
            
            return {
                "success": True,
                "filename": filename,
                "file_url": f"/storage/exports/{filename}",
                "content": combined_content,
                "records_count": invoices_export.get("records_count", 0) + payments_export.get("records_count", 0)
            }
        
        return invoices_export
    
    @staticmethod
    def _generate_csv(rows: List[Dict[str, Any]], prefix: str) -> Dict[str, Any]:
        """Generate CSV content"""
        if not rows:
            return {
                "success": True,
                "filename": f"{prefix}_export.csv",
                "content": "",
                "records_count": 0
            }
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys(), delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
        
        content = output.getvalue()
        
        filename = f"{prefix}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Save file
        export_path = settings.STORAGE_PATH / "exports"
        export_path.mkdir(exist_ok=True)
        
        file_path = export_path / filename
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        
        return {
            "success": True,
            "filename": filename,
            "file_url": f"/storage/exports/{filename}",
            "content": content,
            "records_count": len(rows)
        }
    
    @staticmethod
    def _generate_excel(rows: List[Dict[str, Any]], prefix: str) -> Dict[str, Any]:
        """Generate Excel content (placeholder - would need openpyxl)"""
        # For now, fall back to CSV
        # In production, use openpyxl to generate proper Excel files
        return AccountingExportService._generate_csv(rows, prefix)


# Create singleton instance
accounting_export_service = AccountingExportService()
