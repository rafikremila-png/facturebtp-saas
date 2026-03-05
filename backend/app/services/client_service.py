"""
Client Service - CRUD operations for clients
PostgreSQL/Supabase implementation
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import secrets

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Client
from app.schemas.schemas import ClientCreate, ClientUpdate, ClientResponse
from app.core.security import generate_uuid

logger = logging.getLogger(__name__)


class ClientService:
    """Service for client-related database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_client(self, user_id: str, client_data: ClientCreate) -> Client:
        """Create a new client"""
        client = Client(
            id=generate_uuid(),
            user_id=user_id,
            name=client_data.name,
            email=client_data.email,
            phone=client_data.phone,
            address=client_data.address,
            city=client_data.city,
            postal_code=client_data.postal_code,
            country=client_data.country or "France",
            company_name=client_data.company_name,
            siret=client_data.siret,
            vat_number=client_data.vat_number,
            client_type=client_data.client_type or "individual",
            notes=client_data.notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(client)
        await self.db.flush()
        return client
    
    async def get_client_by_id(self, client_id: str, user_id: Optional[str] = None) -> Optional[Client]:
        """Get client by ID, optionally verify ownership"""
        query = select(Client).where(Client.id == client_id)
        
        if user_id:
            query = query.where(Client.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_client(
        self, 
        client_id: str, 
        user_id: str, 
        client_data: ClientUpdate
    ) -> Optional[Client]:
        """Update client information"""
        client = await self.get_client_by_id(client_id, user_id)
        if not client:
            return None
        
        update_data = client_data.model_dump(exclude_unset=True)
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        for key, value in update_data.items():
            setattr(client, key, value)
        
        await self.db.flush()
        return client
    
    async def delete_client(self, client_id: str, user_id: str) -> bool:
        """Delete a client"""
        client = await self.get_client_by_id(client_id, user_id)
        if not client:
            return False
        
        await self.db.delete(client)
        return True
    
    async def list_clients(
        self, 
        user_id: str,
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        client_type: Optional[str] = None
    ) -> List[Client]:
        """List clients for a user with optional filtering"""
        query = select(Client).where(Client.user_id == user_id)
        
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (Client.name.ilike(search_filter)) |
                (Client.email.ilike(search_filter)) |
                (Client.company_name.ilike(search_filter))
            )
        
        if client_type:
            query = query.where(Client.client_type == client_type)
        
        query = query.order_by(Client.name).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_clients(
        self, 
        user_id: str,
        client_type: Optional[str] = None
    ) -> int:
        """Count clients for a user"""
        query = select(func.count(Client.id)).where(Client.user_id == user_id)
        
        if client_type:
            query = query.where(Client.client_type == client_type)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def generate_portal_token(self, client_id: str, user_id: str) -> Optional[str]:
        """Generate a secure access token for client portal"""
        client = await self.get_client_by_id(client_id, user_id)
        if not client:
            return None
        
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        client.access_token = token
        client.token_expires_at = expires_at
        client.updated_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        return token
    
    async def get_client_by_token(self, token: str) -> Optional[Client]:
        """Get client by portal access token"""
        result = await self.db.execute(
            select(Client).where(
                and_(
                    Client.access_token == token,
                    Client.token_expires_at > datetime.now(timezone.utc)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_clients_with_stats(self, user_id: str) -> List[dict]:
        """Get clients with invoice/quote statistics"""
        from app.models.models import Invoice, Quote
        
        # Get all clients
        clients = await self.list_clients(user_id)
        
        result = []
        for client in clients:
            # Get invoice stats
            invoice_result = await self.db.execute(
                select(
                    func.count(Invoice.id).label('total_invoices'),
                    func.coalesce(func.sum(Invoice.total_ttc), 0).label('total_invoiced'),
                    func.coalesce(func.sum(Invoice.amount_paid), 0).label('total_paid')
                ).where(Invoice.client_id == client.id)
            )
            invoice_stats = invoice_result.one()
            
            # Get quote stats
            quote_result = await self.db.execute(
                select(func.count(Quote.id)).where(Quote.client_id == client.id)
            )
            total_quotes = quote_result.scalar() or 0
            
            result.append({
                **ClientResponse.model_validate(client).model_dump(),
                'total_invoices': invoice_stats.total_invoices,
                'total_invoiced': float(invoice_stats.total_invoiced),
                'total_paid': float(invoice_stats.total_paid),
                'total_quotes': total_quotes
            })
        
        return result


def get_client_service(db: AsyncSession) -> ClientService:
    """Factory function for dependency injection"""
    return ClientService(db)
