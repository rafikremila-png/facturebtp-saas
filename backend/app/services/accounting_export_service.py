"""
Accounting Export Service
Export financial data to CSV/Excel format
"""
import logging
import csv
import io
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Invoice, Payment, Quote, Client, InvoiceStatus

logger = logging.getLogger(__name__)


class AccountingExportService:
    """Service for exporting financial data"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def export_invoices_csv(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> str:
        """Export invoices to CSV format"""
        
        query = select(Invoice).options(selectinload(Invoice.client)).where(Invoice.user_id == user_id)
        
        if start_date:
            query = query.where(Invoice.invoice_date >= start_date)
        
        if end_date:
            query = query.where(Invoice.invoice_date <= end_date)
        
        if status:
            query = query.where(Invoice.status == status)
        
        query = query.order_by(Invoice.invoice_date)
        
        result = await self.db.execute(query)
        invoices = list(result.scalars().all())
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # Header
        writer.writerow([
            'Numéro Facture',
            'Date Facture',
            'Date Échéance',
            'Client',
            'Montant HT',
            'TVA',
            'Montant TTC',
            'Montant Payé',
            'Reste à Payer',
            'Statut',
            'Type',
            'Projet'
        ])
        
        # Data rows
        for inv in invoices:
            writer.writerow([
                inv.invoice_number,
                inv.invoice_date.strftime('%d/%m/%Y') if inv.invoice_date else '',
                inv.due_date.strftime('%d/%m/%Y') if inv.due_date else '',
                inv.client.name if inv.client else '',
                f"{inv.subtotal_ht:.2f}".replace('.', ','),
                f"{inv.total_vat:.2f}".replace('.', ','),
                f"{inv.total_ttc:.2f}".replace('.', ','),
                f"{inv.amount_paid:.2f}".replace('.', ',') if inv.amount_paid else '0,00',
                f"{inv.amount_due:.2f}".replace('.', ',') if inv.amount_due else '0,00',
                self._translate_status(inv.status),
                'Situation' if inv.invoice_type == 'situation' else 'Standard',
                inv.project_id or ''
            ])
        
        return output.getvalue()
    
    async def export_payments_csv(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export payments to CSV format"""
        
        query = (
            select(Payment)
            .options(selectinload(Payment.invoice))
            .where(Payment.user_id == user_id)
        )
        
        if start_date:
            query = query.where(Payment.payment_date >= start_date)
        
        if end_date:
            query = query.where(Payment.payment_date <= end_date)
        
        query = query.order_by(Payment.payment_date)
        
        result = await self.db.execute(query)
        payments = list(result.scalars().all())
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # Header
        writer.writerow([
            'Date Paiement',
            'Numéro Facture',
            'Montant',
            'Mode de Paiement',
            'Référence',
            'Notes'
        ])
        
        # Data rows
        for pmt in payments:
            writer.writerow([
                pmt.payment_date.strftime('%d/%m/%Y') if pmt.payment_date else '',
                pmt.invoice.invoice_number if pmt.invoice else '',
                f"{pmt.amount:.2f}".replace('.', ','),
                self._translate_payment_method(pmt.payment_method),
                pmt.reference or '',
                pmt.notes or ''
            ])
        
        return output.getvalue()
    
    async def export_vat_summary_csv(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """Export VAT summary for accounting period"""
        
        # Get all invoices in period
        result = await self.db.execute(
            select(Invoice)
            .where(and_(
                Invoice.user_id == user_id,
                Invoice.invoice_date >= start_date,
                Invoice.invoice_date <= end_date,
                Invoice.status != InvoiceStatus.DRAFT
            ))
        )
        invoices = list(result.scalars().all())
        
        # Calculate VAT by rate
        vat_by_rate = {}
        total_ht = 0
        total_vat = 0
        total_ttc = 0
        
        for inv in invoices:
            total_ht += inv.subtotal_ht or 0
            total_vat += inv.total_vat or 0
            total_ttc += inv.total_ttc or 0
            
            # Extract VAT from items
            for item in (inv.items or []):
                rate = item.get('vat_rate', 20)
                ht = item.get('quantity', 0) * item.get('unit_price', 0)
                vat = ht * (rate / 100)
                
                if rate not in vat_by_rate:
                    vat_by_rate[rate] = {'base_ht': 0, 'vat': 0}
                vat_by_rate[rate]['base_ht'] += ht
                vat_by_rate[rate]['vat'] += vat
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # Period info
        writer.writerow(['Récapitulatif TVA'])
        writer.writerow([f"Période: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"])
        writer.writerow([])
        
        # VAT breakdown by rate
        writer.writerow(['Taux TVA', 'Base HT', 'Montant TVA'])
        
        for rate in sorted(vat_by_rate.keys()):
            data = vat_by_rate[rate]
            writer.writerow([
                f"{rate}%",
                f"{data['base_ht']:.2f}".replace('.', ','),
                f"{data['vat']:.2f}".replace('.', ',')
            ])
        
        writer.writerow([])
        
        # Totals
        writer.writerow(['TOTAUX'])
        writer.writerow(['Total HT', f"{total_ht:.2f}".replace('.', ',')])
        writer.writerow(['Total TVA', f"{total_vat:.2f}".replace('.', ',')])
        writer.writerow(['Total TTC', f"{total_ttc:.2f}".replace('.', ',')])
        writer.writerow(['Nombre de factures', len(invoices)])
        
        return output.getvalue()
    
    async def export_client_balance_csv(
        self,
        user_id: str
    ) -> str:
        """Export client balance summary"""
        
        # Get all clients with their invoice totals
        result = await self.db.execute(
            select(
                Client.id,
                Client.name,
                Client.email,
                func.coalesce(func.sum(Invoice.total_ttc), 0).label('total_invoiced'),
                func.coalesce(func.sum(Invoice.amount_paid), 0).label('total_paid'),
                func.coalesce(func.sum(Invoice.amount_due), 0).label('total_due'),
                func.count(Invoice.id).label('invoice_count')
            )
            .outerjoin(Invoice, and_(
                Invoice.client_id == Client.id,
                Invoice.status != InvoiceStatus.DRAFT
            ))
            .where(Client.user_id == user_id)
            .group_by(Client.id, Client.name, Client.email)
            .order_by(Client.name)
        )
        clients = result.all()
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # Header
        writer.writerow([
            'Client',
            'Email',
            'Nb Factures',
            'Total Facturé',
            'Total Payé',
            'Solde Dû'
        ])
        
        # Data rows
        for client in clients:
            writer.writerow([
                client.name,
                client.email or '',
                client.invoice_count,
                f"{float(client.total_invoiced):.2f}".replace('.', ','),
                f"{float(client.total_paid):.2f}".replace('.', ','),
                f"{float(client.total_due):.2f}".replace('.', ',')
            ])
        
        return output.getvalue()
    
    async def get_financial_summary(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get financial summary for a period"""
        
        query = select(Invoice).where(Invoice.user_id == user_id)
        
        if start_date:
            query = query.where(Invoice.invoice_date >= start_date)
        
        if end_date:
            query = query.where(Invoice.invoice_date <= end_date)
        
        result = await self.db.execute(query)
        invoices = list(result.scalars().all())
        
        # Calculate metrics
        total_ht = sum(inv.subtotal_ht or 0 for inv in invoices)
        total_vat = sum(inv.total_vat or 0 for inv in invoices)
        total_ttc = sum(inv.total_ttc or 0 for inv in invoices)
        total_paid = sum(inv.amount_paid or 0 for inv in invoices)
        total_due = sum(inv.amount_due or 0 for inv in invoices)
        
        # Status breakdown
        by_status = {}
        for inv in invoices:
            status = inv.status or 'unknown'
            if status not in by_status:
                by_status[status] = {'count': 0, 'amount': 0}
            by_status[status]['count'] += 1
            by_status[status]['amount'] += inv.total_ttc or 0
        
        # Overdue invoices
        now = datetime.now(timezone.utc)
        overdue = [
            inv for inv in invoices
            if inv.due_date and inv.due_date < now and inv.status != InvoiceStatus.PAID
        ]
        
        return {
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'totals': {
                'total_ht': round(total_ht, 2),
                'total_vat': round(total_vat, 2),
                'total_ttc': round(total_ttc, 2),
                'total_paid': round(total_paid, 2),
                'total_due': round(total_due, 2)
            },
            'by_status': by_status,
            'invoice_count': len(invoices),
            'overdue': {
                'count': len(overdue),
                'amount': round(sum(inv.amount_due or 0 for inv in overdue), 2)
            }
        }
    
    def _translate_status(self, status: str) -> str:
        """Translate invoice status to French"""
        translations = {
            'draft': 'Brouillon',
            'sent': 'Envoyée',
            'partial': 'Partiellement payée',
            'paid': 'Payée',
            'overdue': 'En retard',
            'cancelled': 'Annulée'
        }
        return translations.get(status, status)
    
    def _translate_payment_method(self, method: str) -> str:
        """Translate payment method to French"""
        translations = {
            'bank_transfer': 'Virement bancaire',
            'check': 'Chèque',
            'cash': 'Espèces',
            'card': 'Carte bancaire',
            'stripe': 'Stripe (en ligne)',
            'other': 'Autre'
        }
        return translations.get(method, method)


def get_accounting_export_service(db: AsyncSession) -> AccountingExportService:
    """Factory function for dependency injection"""
    return AccountingExportService(db)
