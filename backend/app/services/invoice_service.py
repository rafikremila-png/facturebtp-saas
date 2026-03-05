"""
Invoice Service - CRUD operations for invoices (factures)
PostgreSQL/Supabase implementation with BTP-specific features:
- Progress invoicing (factures de situation)
- Retenue de garantie
- Multiple VAT rates
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Invoice, Payment, Client, Project, Quote, InvoiceStatus
from app.schemas.schemas import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceItem,
    PaymentCreate, PaymentResponse
)
from app.core.security import generate_uuid

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for invoice (facture) database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_invoice(self, user_id: str, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice"""
        # Generate invoice number
        count = await self.count_invoices(user_id)
        invoice_number = f"FAC-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
        
        # Calculate totals
        items = [item.model_dump() for item in invoice_data.items]
        subtotal_ht = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in items)
        
        # Calculate VAT per rate
        total_vat = 0
        for item in items:
            item_total = item.get('quantity', 0) * item.get('unit_price', 0)
            item['total_ht'] = item_total
            vat_rate = item.get('vat_rate', 20.0)
            item_vat = item_total * (vat_rate / 100)
            item['vat_amount'] = item_vat
            total_vat += item_vat
        
        # Apply discount
        discount_amount = 0
        if invoice_data.discount_type == 'percentage' and invoice_data.discount_value:
            discount_amount = subtotal_ht * (invoice_data.discount_value / 100)
        elif invoice_data.discount_type == 'fixed' and invoice_data.discount_value:
            discount_amount = invoice_data.discount_value
        
        subtotal_after_discount = subtotal_ht - discount_amount
        total_vat_adjusted = (subtotal_after_discount / subtotal_ht * total_vat) if subtotal_ht > 0 else 0
        
        # Handle progress invoicing
        previous_invoiced = 0
        current_amount = subtotal_after_discount + total_vat_adjusted
        
        if invoice_data.invoice_type == 'situation' and invoice_data.progress_percentage:
            # Calculate current amount based on progress
            current_amount = (subtotal_after_discount + total_vat_adjusted) * (invoice_data.progress_percentage / 100)
            previous_invoiced = invoice_data.progress_percentage  # Will be updated with actual previous amount
        
        # Calculate retention (retenue de garantie)
        retention_amount = 0
        if invoice_data.retention_rate and invoice_data.retention_rate > 0:
            retention_amount = current_amount * (invoice_data.retention_rate / 100)
        
        total_ttc = current_amount - retention_amount
        
        # Default due date
        due_date = invoice_data.due_date
        if not due_date:
            due_date = datetime.now(timezone.utc) + timedelta(days=30)
        
        invoice = Invoice(
            id=generate_uuid(),
            user_id=user_id,
            client_id=invoice_data.client_id,
            project_id=invoice_data.project_id,
            quote_id=invoice_data.quote_id,
            invoice_number=invoice_number,
            title=invoice_data.title,
            description=invoice_data.description,
            status=InvoiceStatus.DRAFT,
            invoice_date=datetime.now(timezone.utc),
            due_date=due_date,
            items=items,
            subtotal_ht=round(subtotal_ht, 2),
            total_vat=round(total_vat_adjusted, 2),
            total_ttc=round(total_ttc, 2),
            discount_type=invoice_data.discount_type,
            discount_value=invoice_data.discount_value or 0,
            discount_amount=round(discount_amount, 2),
            invoice_type=invoice_data.invoice_type or 'standard',
            situation_number=invoice_data.situation_number,
            progress_percentage=invoice_data.progress_percentage or 100,
            previous_invoiced=round(previous_invoiced, 2),
            current_amount=round(current_amount, 2),
            retention_rate=invoice_data.retention_rate or 0,
            retention_amount=round(retention_amount, 2),
            retention_released=False,
            amount_paid=0,
            amount_due=round(total_ttc, 2),
            notes=invoice_data.notes,
            payment_terms=invoice_data.payment_terms,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(invoice)
        await self.db.flush()
        
        # Update project financials if linked
        if invoice_data.project_id:
            await self._update_project_financials(invoice_data.project_id)
        
        return invoice
    
    async def create_situation_invoice(
        self, 
        user_id: str, 
        quote_id: str, 
        progress_percentage: float,
        retention_rate: float = 0,
        notes: Optional[str] = None
    ) -> Invoice:
        """Create a progress invoice (facture de situation) from a quote"""
        # Get the quote
        quote_result = await self.db.execute(
            select(Quote).where(and_(Quote.id == quote_id, Quote.user_id == user_id))
        )
        quote = quote_result.scalar_one_or_none()
        if not quote:
            raise ValueError("Quote not found")
        
        # Get previous situations for this quote
        prev_result = await self.db.execute(
            select(Invoice)
            .where(and_(
                Invoice.quote_id == quote_id,
                Invoice.invoice_type == 'situation'
            ))
            .order_by(Invoice.situation_number.desc())
        )
        previous_situations = list(prev_result.scalars().all())
        
        # Calculate previous percentage
        previous_percentage = sum(s.progress_percentage - (prev_result.scalar().progress_percentage if i > 0 else 0) 
                                   for i, s in enumerate(previous_situations)) if previous_situations else 0
        
        if progress_percentage <= previous_percentage:
            raise ValueError(f"Progress must be greater than previous ({previous_percentage}%)")
        
        situation_number = len(previous_situations) + 1
        current_percentage = progress_percentage - previous_percentage
        
        # Calculate amounts
        base_amount = quote.total_ttc
        current_amount = base_amount * (current_percentage / 100)
        
        # Apply retention
        retention_amount = 0
        if retention_rate > 0:
            retention_amount = current_amount * (retention_rate / 100)
        
        total_ttc = current_amount - retention_amount
        
        # Generate invoice number
        count = await self.count_invoices(user_id)
        invoice_number = f"SIT-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
        
        invoice = Invoice(
            id=generate_uuid(),
            user_id=user_id,
            client_id=quote.client_id,
            project_id=quote.project_id,
            quote_id=quote_id,
            invoice_number=invoice_number,
            title=f"Situation n°{situation_number} - {quote.title or quote.quote_number}",
            status=InvoiceStatus.DRAFT,
            invoice_date=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
            items=quote.items,
            subtotal_ht=quote.subtotal_ht,
            total_vat=quote.total_vat,
            total_ttc=round(total_ttc, 2),
            invoice_type='situation',
            situation_number=situation_number,
            progress_percentage=progress_percentage,
            previous_invoiced=round(base_amount * (previous_percentage / 100), 2),
            current_amount=round(current_amount, 2),
            retention_rate=retention_rate,
            retention_amount=round(retention_amount, 2),
            amount_paid=0,
            amount_due=round(total_ttc, 2),
            notes=notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(invoice)
        await self.db.flush()
        
        return invoice
    
    async def get_invoice_by_id(
        self, 
        invoice_id: str, 
        user_id: Optional[str] = None,
        include_client: bool = False,
        include_project: bool = False,
        include_payments: bool = False
    ) -> Optional[Invoice]:
        """Get invoice by ID"""
        query = select(Invoice).where(Invoice.id == invoice_id)
        
        if user_id:
            query = query.where(Invoice.user_id == user_id)
        
        if include_client:
            query = query.options(selectinload(Invoice.client))
        
        if include_project:
            query = query.options(selectinload(Invoice.project))
        
        if include_payments:
            query = query.options(selectinload(Invoice.payments))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_invoice(
        self, 
        invoice_id: str, 
        user_id: str, 
        invoice_data: InvoiceUpdate
    ) -> Optional[Invoice]:
        """Update invoice information"""
        invoice = await self.get_invoice_by_id(invoice_id, user_id)
        if not invoice:
            return None
        
        # Cannot update paid invoices
        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Cannot modify paid invoice")
        
        update_data = invoice_data.model_dump(exclude_unset=True)
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        for key, value in update_data.items():
            setattr(invoice, key, value)
        
        await self.db.flush()
        return invoice
    
    async def delete_invoice(self, invoice_id: str, user_id: str) -> bool:
        """Delete an invoice"""
        invoice = await self.get_invoice_by_id(invoice_id, user_id)
        if not invoice:
            return False
        
        # Cannot delete paid invoices
        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Cannot delete paid invoice")
        
        project_id = invoice.project_id
        await self.db.delete(invoice)
        
        # Update project financials
        if project_id:
            await self._update_project_financials(project_id)
        
        return True
    
    async def list_invoices(
        self, 
        user_id: str,
        skip: int = 0, 
        limit: int = 50,
        status: Optional[str] = None,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        quote_id: Optional[str] = None,
        include_client: bool = False,
        overdue_only: bool = False
    ) -> List[Invoice]:
        """List invoices for a user"""
        query = select(Invoice).where(Invoice.user_id == user_id)
        
        if status:
            query = query.where(Invoice.status == status)
        
        if client_id:
            query = query.where(Invoice.client_id == client_id)
        
        if project_id:
            query = query.where(Invoice.project_id == project_id)
        
        if quote_id:
            query = query.where(Invoice.quote_id == quote_id)
        
        if include_client:
            query = query.options(selectinload(Invoice.client))
        
        if overdue_only:
            query = query.where(and_(
                Invoice.due_date < datetime.now(timezone.utc),
                Invoice.status != InvoiceStatus.PAID
            ))
        
        query = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_invoices(
        self, 
        user_id: str,
        status: Optional[str] = None
    ) -> int:
        """Count invoices for a user"""
        query = select(func.count(Invoice.id)).where(Invoice.user_id == user_id)
        
        if status:
            query = query.where(Invoice.status == status)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    # ============== PAYMENTS ==============
    
    async def add_payment(self, user_id: str, payment_data: PaymentCreate) -> Payment:
        """Add a payment to an invoice"""
        invoice = await self.get_invoice_by_id(payment_data.invoice_id, user_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        payment = Payment(
            id=generate_uuid(),
            user_id=user_id,
            invoice_id=payment_data.invoice_id,
            amount=payment_data.amount,
            payment_date=payment_data.payment_date or datetime.now(timezone.utc),
            payment_method=payment_data.payment_method or 'bank_transfer',
            reference=payment_data.reference,
            notes=payment_data.notes,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(payment)
        
        # Update invoice amounts
        invoice.amount_paid = (invoice.amount_paid or 0) + payment_data.amount
        invoice.amount_due = invoice.total_ttc - invoice.amount_paid
        
        # Update status
        if invoice.amount_paid >= invoice.total_ttc:
            invoice.status = InvoiceStatus.PAID
            invoice.paid_date = datetime.now(timezone.utc)
        elif invoice.amount_paid > 0:
            invoice.status = InvoiceStatus.PARTIAL
        
        invoice.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        
        # Update project financials
        if invoice.project_id:
            await self._update_project_financials(invoice.project_id)
        
        return payment
    
    async def list_payments(self, invoice_id: str) -> List[Payment]:
        """List payments for an invoice"""
        result = await self.db.execute(
            select(Payment)
            .where(Payment.invoice_id == invoice_id)
            .order_by(Payment.payment_date.desc())
        )
        return list(result.scalars().all())
    
    # ============== RETENTION (RETENUE DE GARANTIE) ==============
    
    async def release_retention(self, invoice_id: str, user_id: str) -> Optional[Invoice]:
        """Release retention amount"""
        invoice = await self.get_invoice_by_id(invoice_id, user_id)
        if not invoice:
            return None
        
        if invoice.retention_released:
            raise ValueError("Retention already released")
        
        if not invoice.retention_amount or invoice.retention_amount <= 0:
            raise ValueError("No retention to release")
        
        invoice.retention_released = True
        invoice.amount_due = (invoice.amount_due or 0) + invoice.retention_amount
        invoice.total_ttc = (invoice.total_ttc or 0) + invoice.retention_amount
        invoice.updated_at = datetime.now(timezone.utc)
        
        # Update status if was paid
        if invoice.status == InvoiceStatus.PAID:
            invoice.status = InvoiceStatus.PARTIAL
        
        await self.db.flush()
        return invoice
    
    async def get_retention_summary(self, user_id: str) -> dict:
        """Get summary of all retentions"""
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(Invoice.retention_amount), 0).label('total_retained'),
                func.sum(
                    func.case(
                        (Invoice.retention_released == True, Invoice.retention_amount),
                        else_=0
                    )
                ).label('total_released')
            )
            .where(and_(
                Invoice.user_id == user_id,
                Invoice.retention_amount > 0
            ))
        )
        stats = result.one()
        
        total_retained = float(stats.total_retained or 0)
        total_released = float(stats.total_released or 0)
        
        return {
            'total_retained': total_retained,
            'total_released': total_released,
            'pending_release': total_retained - total_released
        }
    
    # ============== STATISTICS ==============
    
    async def get_invoice_stats(self, user_id: str) -> dict:
        """Get invoice statistics"""
        # Status breakdown
        status_result = await self.db.execute(
            select(Invoice.status, func.count(Invoice.id))
            .where(Invoice.user_id == user_id)
            .group_by(Invoice.status)
        )
        status_breakdown = {row[0]: row[1] for row in status_result.all()}
        
        # Financial totals
        finance_result = await self.db.execute(
            select(
                func.coalesce(func.sum(Invoice.total_ttc), 0).label('total'),
                func.coalesce(func.sum(Invoice.amount_paid), 0).label('paid'),
                func.coalesce(func.sum(Invoice.amount_due), 0).label('due')
            ).where(Invoice.user_id == user_id)
        )
        finances = finance_result.one()
        
        # Overdue
        overdue_result = await self.db.execute(
            select(
                func.count(Invoice.id).label('count'),
                func.coalesce(func.sum(Invoice.amount_due), 0).label('amount')
            ).where(and_(
                Invoice.user_id == user_id,
                Invoice.due_date < datetime.now(timezone.utc),
                Invoice.status != InvoiceStatus.PAID
            ))
        )
        overdue = overdue_result.one()
        
        return {
            'total_invoices': sum(status_breakdown.values()),
            'total_amount': float(finances.total),
            'total_paid': float(finances.paid),
            'total_due': float(finances.due),
            'overdue_count': overdue.count,
            'overdue_amount': float(overdue.amount),
            'status_breakdown': status_breakdown
        }
    
    async def _update_project_financials(self, project_id: str):
        """Update project financial totals"""
        from app.models.models import Project
        
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(Invoice.total_ttc), 0).label('total_invoiced'),
                func.coalesce(func.sum(Invoice.amount_paid), 0).label('total_paid')
            ).where(Invoice.project_id == project_id)
        )
        stats = result.one()
        
        await self.db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(
                total_invoiced=float(stats.total_invoiced),
                total_paid=float(stats.total_paid),
                updated_at=datetime.now(timezone.utc)
            )
        )


def get_invoice_service(db: AsyncSession) -> InvoiceService:
    """Factory function for dependency injection"""
    return InvoiceService(db)
