"""
Supabase Database Service
Centralized database operations using Supabase client
"""
import os
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Singleton client
_client: Optional[Client] = None

def get_supabase() -> Client:
    """Get or create Supabase client"""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase credentials not configured")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client

class SupabaseService:
    """Base service for Supabase operations"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.client = get_supabase()
    
    async def get_all(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all records for a user"""
        result = self.client.from_(self.table_name)\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        return result.data or []
    
    async def get_by_id(self, id: str, user_id: str) -> Optional[Dict]:
        """Get a record by ID"""
        result = self.client.from_(self.table_name)\
            .select("*")\
            .eq("id", id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        return result.data
    
    async def create(self, data: Dict, user_id: str) -> Dict:
        """Create a new record"""
        data["user_id"] = user_id
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = self.client.from_(self.table_name)\
            .insert(data)\
            .execute()
        return result.data[0] if result.data else data
    
    async def update(self, id: str, data: Dict, user_id: str) -> Optional[Dict]:
        """Update a record"""
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = self.client.from_(self.table_name)\
            .update(data)\
            .eq("id", id)\
            .eq("user_id", user_id)\
            .execute()
        return result.data[0] if result.data else None
    
    async def delete(self, id: str, user_id: str) -> bool:
        """Delete a record"""
        result = self.client.from_(self.table_name)\
            .delete()\
            .eq("id", id)\
            .eq("user_id", user_id)\
            .execute()
        return len(result.data) > 0 if result.data else False
    
    async def count(self, user_id: str, filters: Dict = None) -> int:
        """Count records"""
        query = self.client.from_(self.table_name)\
            .select("*", count="exact")\
            .eq("user_id", user_id)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        result = query.execute()
        return result.count or 0

# Specific services for each table
class ClientsService(SupabaseService):
    def __init__(self):
        super().__init__("clients")
    
    async def search(self, user_id: str, query: str) -> List[Dict]:
        """Search clients by name or email"""
        result = self.client.from_(self.table_name)\
            .select("*")\
            .eq("user_id", user_id)\
            .or_(f"name.ilike.%{query}%,email.ilike.%{query}%,company_name.ilike.%{query}%")\
            .execute()
        return result.data or []

class QuotesService(SupabaseService):
    def __init__(self):
        super().__init__("quotes")
    
    async def get_by_status(self, user_id: str, status: str) -> List[Dict]:
        """Get quotes by status"""
        result = self.client.from_(self.table_name)\
            .select("*, clients(*)")\
            .eq("user_id", user_id)\
            .eq("status", status)\
            .order("created_at", desc=True)\
            .execute()
        return result.data or []
    
    async def get_with_client(self, id: str, user_id: str) -> Optional[Dict]:
        """Get quote with client details"""
        result = self.client.from_(self.table_name)\
            .select("*, clients(*)")\
            .eq("id", id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        return result.data

class InvoicesService(SupabaseService):
    def __init__(self):
        super().__init__("invoices")
    
    async def get_by_status(self, user_id: str, status: str) -> List[Dict]:
        """Get invoices by status"""
        result = self.client.from_(self.table_name)\
            .select("*, clients(*)")\
            .eq("user_id", user_id)\
            .eq("status", status)\
            .order("created_at", desc=True)\
            .execute()
        return result.data or []
    
    async def get_overdue(self, user_id: str) -> List[Dict]:
        """Get overdue invoices"""
        today = datetime.now(timezone.utc).date().isoformat()
        result = self.client.from_(self.table_name)\
            .select("*, clients(*)")\
            .eq("user_id", user_id)\
            .neq("status", "paid")\
            .lt("due_date", today)\
            .execute()
        return result.data or []

class ProjectsService(SupabaseService):
    def __init__(self):
        super().__init__("projects")
    
    async def get_active(self, user_id: str) -> List[Dict]:
        """Get active projects"""
        result = self.client.from_(self.table_name)\
            .select("*, clients(*)")\
            .eq("user_id", user_id)\
            .neq("status", "completed")\
            .neq("status", "cancelled")\
            .order("created_at", desc=True)\
            .execute()
        return result.data or []

class WorkItemsService(SupabaseService):
    def __init__(self):
        super().__init__("work_items")

class ServiceRequestsService(SupabaseService):
    def __init__(self):
        super().__init__("service_requests")

# Factory functions
def get_clients_service() -> ClientsService:
    return ClientsService()

def get_quotes_service() -> QuotesService:
    return QuotesService()

def get_invoices_service() -> InvoicesService:
    return InvoicesService()

def get_projects_service() -> ProjectsService:
    return ProjectsService()

def get_work_items_service() -> WorkItemsService:
    return WorkItemsService()

def get_service_requests_service() -> ServiceRequestsService:
    return ServiceRequestsService()
