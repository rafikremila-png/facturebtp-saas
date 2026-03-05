"""
Recurring Invoice & Reminder Service
Handles automatic invoice generation and payment reminders
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import RecurringInvoice, InvoiceReminder, Invoice, Client, InvoiceStatus
from app.core.security import generate_uuid

logger = logging.getLogger(__name__)


class RecurringInvoiceService:
    """Service for recurring invoice management"""
    
    FREQUENCIES = ['weekly', 'monthly', 'quarterly', 'yearly']
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_recurring_invoice(
        self,
        user_id: str,
        client_id: str,
        title: str,
        items: List[dict],
        frequency: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        payment_days: int = 30,
        notes: Optional[str] = None
    ) -> RecurringInvoice:
        """Create a new recurring invoice template"""
        
        if frequency not in self.FREQUENCIES:
            frequency = 'monthly'
        
        # Calculate totals
        subtotal_ht = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in items)
        total_vat = sum(
            (item.get('quantity', 0) * item.get('unit_price', 0)) * (item.get('vat_rate', 20) / 100)
            for item in items
        )
        total_ttc = subtotal_ht + total_vat
        
        recurring = RecurringInvoice(
            id=generate_uuid(),
            user_id=user_id,
            client_id=client_id,
            title=title,
            items=items,
            subtotal_ht=round(subtotal_ht, 2),
            total_vat=round(total_vat, 2),
            total_ttc=round(total_ttc, 2),
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            next_generation_date=start_date,
            payment_days=payment_days,
            is_active=True,
            notes=notes,
            generated_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(recurring)
        await self.db.flush()
        return recurring
    
    async def get_recurring_invoice_by_id(
        self, 
        recurring_id: str, 
        user_id: Optional[str] = None
    ) -> Optional[RecurringInvoice]:
        """Get recurring invoice by ID"""
        query = select(RecurringInvoice).where(RecurringInvoice.id == recurring_id)
        
        if user_id:
            query = query.where(RecurringInvoice.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_recurring_invoices(
        self, 
        user_id: str,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[RecurringInvoice]:
        """List recurring invoices for a user"""
        query = select(RecurringInvoice).where(RecurringInvoice.user_id == user_id)
        
        if is_active is not None:
            query = query.where(RecurringInvoice.is_active == is_active)
        
        query = query.order_by(RecurringInvoice.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_recurring_invoice(
        self,
        recurring_id: str,
        user_id: str,
        **kwargs
    ) -> Optional[RecurringInvoice]:
        """Update a recurring invoice"""
        recurring = await self.get_recurring_invoice_by_id(recurring_id, user_id)
        if not recurring:
            return None
        
        kwargs['updated_at'] = datetime.now(timezone.utc)
        
        for key, value in kwargs.items():
            if hasattr(recurring, key):
                setattr(recurring, key, value)
        
        await self.db.flush()
        return recurring
    
    async def toggle_active(self, recurring_id: str, user_id: str) -> Optional[RecurringInvoice]:
        """Toggle active status of recurring invoice"""
        recurring = await self.get_recurring_invoice_by_id(recurring_id, user_id)
        if not recurring:
            return None
        
        recurring.is_active = not recurring.is_active
        recurring.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        return recurring
    
    async def delete_recurring_invoice(self, recurring_id: str, user_id: str) -> bool:
        """Delete a recurring invoice"""
        recurring = await self.get_recurring_invoice_by_id(recurring_id, user_id)
        if not recurring:
            return False
        
        await self.db.delete(recurring)
        return True
    
    async def get_due_recurring_invoices(self) -> List[RecurringInvoice]:
        """Get all recurring invoices that need generation"""
        now = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            select(RecurringInvoice)
            .where(and_(
                RecurringInvoice.is_active == True,
                RecurringInvoice.next_generation_date <= now,
                (RecurringInvoice.end_date == None) | (RecurringInvoice.end_date > now)
            ))
        )
        return list(result.scalars().all())
    
    def calculate_next_date(self, current_date: datetime, frequency: str) -> datetime:
        """Calculate next generation date based on frequency"""
        if frequency == 'weekly':
            return current_date + timedelta(weeks=1)
        elif frequency == 'monthly':
            # Add one month
            month = current_date.month + 1
            year = current_date.year
            if month > 12:
                month = 1
                year += 1
            day = min(current_date.day, 28)  # Avoid issues with month-end
            return current_date.replace(year=year, month=month, day=day)
        elif frequency == 'quarterly':
            # Add 3 months
            month = current_date.month + 3
            year = current_date.year
            while month > 12:
                month -= 12
                year += 1
            day = min(current_date.day, 28)
            return current_date.replace(year=year, month=month, day=day)
        elif frequency == 'yearly':
            return current_date.replace(year=current_date.year + 1)
        else:
            return current_date + timedelta(days=30)


class InvoiceReminderService:
    """Service for invoice payment reminders"""
    
    REMINDER_TYPES = ['first', 'second', 'final', 'custom']
    
    # Default reminder schedule (days after due date)
    DEFAULT_SCHEDULE = {
        'first': 7,    # 7 days after due date
        'second': 14,  # 14 days after due date
        'final': 30    # 30 days after due date
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_reminder(
        self,
        user_id: str,
        invoice_id: str,
        reminder_type: str,
        scheduled_date: datetime,
        subject: Optional[str] = None,
        message: Optional[str] = None
    ) -> InvoiceReminder:
        """Create a new invoice reminder"""
        
        if reminder_type not in self.REMINDER_TYPES:
            reminder_type = 'custom'
        
        reminder = InvoiceReminder(
            id=generate_uuid(),
            user_id=user_id,
            invoice_id=invoice_id,
            reminder_type=reminder_type,
            scheduled_date=scheduled_date,
            subject=subject,
            message=message,
            is_sent=False,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(reminder)
        await self.db.flush()
        return reminder
    
    async def get_reminder_by_id(
        self, 
        reminder_id: str, 
        user_id: Optional[str] = None
    ) -> Optional[InvoiceReminder]:
        """Get reminder by ID"""
        query = select(InvoiceReminder).where(InvoiceReminder.id == reminder_id)
        
        if user_id:
            query = query.where(InvoiceReminder.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_reminders(
        self,
        user_id: str,
        invoice_id: Optional[str] = None,
        is_sent: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[InvoiceReminder]:
        """List reminders for a user"""
        query = select(InvoiceReminder).where(InvoiceReminder.user_id == user_id)
        
        if invoice_id:
            query = query.where(InvoiceReminder.invoice_id == invoice_id)
        
        if is_sent is not None:
            query = query.where(InvoiceReminder.is_sent == is_sent)
        
        query = query.order_by(InvoiceReminder.scheduled_date).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_pending_reminders(self) -> List[InvoiceReminder]:
        """Get all pending reminders that should be sent"""
        now = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            select(InvoiceReminder)
            .options(selectinload(InvoiceReminder.invoice))
            .where(and_(
                InvoiceReminder.is_sent == False,
                InvoiceReminder.scheduled_date <= now
            ))
        )
        return list(result.scalars().all())
    
    async def mark_as_sent(self, reminder_id: str) -> bool:
        """Mark a reminder as sent"""
        await self.db.execute(
            update(InvoiceReminder)
            .where(InvoiceReminder.id == reminder_id)
            .values(
                is_sent=True,
                sent_date=datetime.now(timezone.utc)
            )
        )
        return True
    
    async def delete_reminder(self, reminder_id: str, user_id: str) -> bool:
        """Delete a reminder"""
        reminder = await self.get_reminder_by_id(reminder_id, user_id)
        if not reminder:
            return False
        
        await self.db.delete(reminder)
        return True
    
    async def schedule_reminders_for_invoice(
        self,
        user_id: str,
        invoice_id: str,
        due_date: datetime,
        schedule: Optional[dict] = None
    ) -> List[InvoiceReminder]:
        """Schedule standard reminders for an invoice"""
        if schedule is None:
            schedule = self.DEFAULT_SCHEDULE
        
        reminders = []
        
        for reminder_type, days_after in schedule.items():
            scheduled_date = due_date + timedelta(days=days_after)
            
            reminder = await self.create_reminder(
                user_id=user_id,
                invoice_id=invoice_id,
                reminder_type=reminder_type,
                scheduled_date=scheduled_date
            )
            reminders.append(reminder)
        
        return reminders
    
    async def cancel_reminders_for_invoice(self, invoice_id: str) -> int:
        """Cancel all pending reminders for an invoice (e.g., when paid)"""
        result = await self.db.execute(
            select(InvoiceReminder)
            .where(and_(
                InvoiceReminder.invoice_id == invoice_id,
                InvoiceReminder.is_sent == False
            ))
        )
        reminders = list(result.scalars().all())
        
        count = 0
        for reminder in reminders:
            await self.db.delete(reminder)
            count += 1
        
        return count


def get_recurring_invoice_service(db: AsyncSession) -> RecurringInvoiceService:
    """Factory function for dependency injection"""
    return RecurringInvoiceService(db)


def get_invoice_reminder_service(db: AsyncSession) -> InvoiceReminderService:
    """Factory function for dependency injection"""
    return InvoiceReminderService(db)
