"""
Quote Service - CRUD operations for quotes (devis)
PostgreSQL/Supabase implementation with BTP-specific features
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Quote, QuoteSignature, Client, Project, QuoteStatus
from app.schemas.schemas import (
    QuoteCreate, QuoteUpdate, QuoteResponse, QuoteItem,
    QuoteSignatureCreate, QuoteSignatureResponse
)
from app.core.security import generate_uuid, generate_token

logger = logging.getLogger(__name__)


class QuoteService:
    """Service for quote (devis) database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_quote(self, user_id: str, quote_data: QuoteCreate) -> Quote:
        """Create a new quote"""
        # Generate quote number
        count = await self.count_quotes(user_id)
        quote_number = f"DEV-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
        
        # Calculate totals
        items = [item.model_dump() for item in quote_data.items]
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
        if quote_data.discount_type == 'percentage' and quote_data.discount_value:
            discount_amount = subtotal_ht * (quote_data.discount_value / 100)
        elif quote_data.discount_type == 'fixed' and quote_data.discount_value:
            discount_amount = quote_data.discount_value
        
        subtotal_after_discount = subtotal_ht - discount_amount
        total_vat_adjusted = (subtotal_after_discount / subtotal_ht * total_vat) if subtotal_ht > 0 else 0
        
        # Calculate retention
        retention_amount = 0
        if quote_data.retention_rate and quote_data.retention_rate > 0:
            total_before_retention = subtotal_after_discount + total_vat_adjusted
            retention_amount = total_before_retention * (quote_data.retention_rate / 100)
        
        total_ttc = subtotal_after_discount + total_vat_adjusted - retention_amount
        
        # Default validity date
        validity_date = quote_data.validity_date
        if not validity_date:
            validity_date = datetime.now(timezone.utc) + timedelta(days=30)
        
        quote = Quote(
            id=generate_uuid(),
            user_id=user_id,
            client_id=quote_data.client_id,
            project_id=quote_data.project_id,
            quote_number=quote_number,
            title=quote_data.title,
            description=quote_data.description,
            status=QuoteStatus.DRAFT,
            quote_date=datetime.now(timezone.utc),
            validity_date=validity_date,
            items=items,
            subtotal_ht=round(subtotal_ht, 2),
            total_vat=round(total_vat_adjusted, 2),
            total_ttc=round(total_ttc, 2),
            discount_type=quote_data.discount_type,
            discount_value=quote_data.discount_value or 0,
            discount_amount=round(discount_amount, 2),
            retention_rate=quote_data.retention_rate or 0,
            retention_amount=round(retention_amount, 2),
            notes=quote_data.notes,
            terms=quote_data.terms,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(quote)
        await self.db.flush()
        return quote
    
    async def get_quote_by_id(
        self, 
        quote_id: str, 
        user_id: Optional[str] = None,
        include_client: bool = False,
        include_project: bool = False,
        include_signature: bool = False
    ) -> Optional[Quote]:
        """Get quote by ID"""
        query = select(Quote).where(Quote.id == quote_id)
        
        if user_id:
            query = query.where(Quote.user_id == user_id)
        
        if include_client:
            query = query.options(selectinload(Quote.client))
        
        if include_project:
            query = query.options(selectinload(Quote.project))
        
        if include_signature:
            query = query.options(selectinload(Quote.signature))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_quote(
        self, 
        quote_id: str, 
        user_id: str, 
        quote_data: QuoteUpdate
    ) -> Optional[Quote]:
        """Update quote information"""
        quote = await self.get_quote_by_id(quote_id, user_id)
        if not quote:
            return None
        
        # Cannot update signed/accepted quotes
        if quote.status in [QuoteStatus.SIGNED, QuoteStatus.ACCEPTED]:
            raise ValueError("Cannot modify signed or accepted quote")
        
        update_data = quote_data.model_dump(exclude_unset=True)
        
        # Recalculate totals if items changed
        if 'items' in update_data and update_data['items']:
            items = update_data['items']
            subtotal_ht = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in items)
            
            total_vat = 0
            for item in items:
                item_total = item.get('quantity', 0) * item.get('unit_price', 0)
                item['total_ht'] = item_total
                vat_rate = item.get('vat_rate', 20.0)
                item_vat = item_total * (vat_rate / 100)
                item['vat_amount'] = item_vat
                total_vat += item_vat
            
            discount_type = update_data.get('discount_type', quote.discount_type)
            discount_value = update_data.get('discount_value', quote.discount_value)
            
            discount_amount = 0
            if discount_type == 'percentage' and discount_value:
                discount_amount = subtotal_ht * (discount_value / 100)
            elif discount_type == 'fixed' and discount_value:
                discount_amount = discount_value
            
            subtotal_after_discount = subtotal_ht - discount_amount
            total_vat_adjusted = (subtotal_after_discount / subtotal_ht * total_vat) if subtotal_ht > 0 else 0
            
            retention_rate = update_data.get('retention_rate', quote.retention_rate) or 0
            retention_amount = 0
            if retention_rate > 0:
                total_before_retention = subtotal_after_discount + total_vat_adjusted
                retention_amount = total_before_retention * (retention_rate / 100)
            
            update_data['subtotal_ht'] = round(subtotal_ht, 2)
            update_data['total_vat'] = round(total_vat_adjusted, 2)
            update_data['total_ttc'] = round(subtotal_after_discount + total_vat_adjusted - retention_amount, 2)
            update_data['discount_amount'] = round(discount_amount, 2)
            update_data['retention_amount'] = round(retention_amount, 2)
        
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        for key, value in update_data.items():
            setattr(quote, key, value)
        
        await self.db.flush()
        return quote
    
    async def delete_quote(self, quote_id: str, user_id: str) -> bool:
        """Delete a quote"""
        quote = await self.get_quote_by_id(quote_id, user_id)
        if not quote:
            return False
        
        await self.db.delete(quote)
        return True
    
    async def list_quotes(
        self, 
        user_id: str,
        skip: int = 0, 
        limit: int = 50,
        status: Optional[str] = None,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        include_client: bool = False
    ) -> List[Quote]:
        """List quotes for a user"""
        query = select(Quote).where(Quote.user_id == user_id)
        
        if status:
            query = query.where(Quote.status == status)
        
        if client_id:
            query = query.where(Quote.client_id == client_id)
        
        if project_id:
            query = query.where(Quote.project_id == project_id)
        
        if include_client:
            query = query.options(selectinload(Quote.client))
        
        query = query.order_by(Quote.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_quotes(
        self, 
        user_id: str,
        status: Optional[str] = None
    ) -> int:
        """Count quotes for a user"""
        query = select(func.count(Quote.id)).where(Quote.user_id == user_id)
        
        if status:
            query = query.where(Quote.status == status)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def update_status(self, quote_id: str, user_id: str, new_status: str) -> Optional[Quote]:
        """Update quote status"""
        quote = await self.get_quote_by_id(quote_id, user_id)
        if not quote:
            return None
        
        quote.status = new_status
        quote.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        return quote
    
    async def duplicate_quote(self, quote_id: str, user_id: str) -> Optional[Quote]:
        """Duplicate an existing quote"""
        original = await self.get_quote_by_id(quote_id, user_id)
        if not original:
            return None
        
        # Create new quote with same data
        quote_data = QuoteCreate(
            client_id=original.client_id,
            project_id=original.project_id,
            title=f"{original.title} (copie)" if original.title else "Copie",
            description=original.description,
            items=[QuoteItem(**item) for item in original.items],
            validity_date=datetime.now(timezone.utc) + timedelta(days=30),
            discount_type=original.discount_type,
            discount_value=original.discount_value,
            retention_rate=original.retention_rate,
            notes=original.notes,
            terms=original.terms
        )
        
        return await self.create_quote(user_id, quote_data)
    
    # ============== SIGNATURE ==============
    
    async def sign_quote(
        self, 
        quote_id: str, 
        signature_data: QuoteSignatureCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[QuoteSignature]:
        """Add electronic signature to quote"""
        quote = await self.get_quote_by_id(quote_id)
        if not quote:
            return None
        
        if quote.status not in [QuoteStatus.DRAFT, QuoteStatus.SENT]:
            raise ValueError("Quote cannot be signed in current status")
        
        # Create signature record
        signature = QuoteSignature(
            id=generate_uuid(),
            quote_id=quote_id,
            signer_name=signature_data.signer_name,
            signer_email=signature_data.signer_email,
            signer_title=signature_data.signer_title,
            signature_data=signature_data.signature_data,
            ip_address=ip_address,
            user_agent=user_agent,
            signed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(signature)
        
        # Update quote status
        quote.status = QuoteStatus.SIGNED
        quote.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        return signature
    
    async def get_signature(self, quote_id: str) -> Optional[QuoteSignature]:
        """Get signature for a quote"""
        result = await self.db.execute(
            select(QuoteSignature).where(QuoteSignature.quote_id == quote_id)
        )
        return result.scalar_one_or_none()
    
    async def get_quote_stats(self, user_id: str) -> dict:
        """Get quote statistics"""
        # Total quotes by status
        status_result = await self.db.execute(
            select(Quote.status, func.count(Quote.id))
            .where(Quote.user_id == user_id)
            .group_by(Quote.status)
        )
        status_breakdown = {row[0]: row[1] for row in status_result.all()}
        
        # Total amounts
        amount_result = await self.db.execute(
            select(
                func.coalesce(func.sum(Quote.total_ttc), 0).label('total'),
                func.count(Quote.id).label('count')
            ).where(Quote.user_id == user_id)
        )
        amounts = amount_result.one()
        
        # Conversion rate
        total = amounts.count
        signed = status_breakdown.get(QuoteStatus.SIGNED, 0)
        accepted = status_breakdown.get(QuoteStatus.ACCEPTED, 0)
        conversion_rate = ((signed + accepted) / total * 100) if total > 0 else 0
        
        return {
            'total_quotes': total,
            'total_amount': float(amounts.total),
            'status_breakdown': status_breakdown,
            'conversion_rate': round(conversion_rate, 2)
        }


def get_quote_service(db: AsyncSession) -> QuoteService:
    """Factory function for dependency injection"""
    return QuoteService(db)
