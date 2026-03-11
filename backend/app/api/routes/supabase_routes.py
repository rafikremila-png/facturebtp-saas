"""
Supabase API Routes
Clean API endpoints using Supabase for authentication and database
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.services.supabase_auth_service import (
    get_current_user,
    get_current_user_optional,
    require_admin,
    get_supabase_client,
)
from app.services.supabase_db_service import (
    get_clients_service,
    get_quotes_service,
    get_invoices_service,
    get_projects_service,
    get_work_items_service,
)

router = APIRouter()

# ============== PYDANTIC MODELS ==============

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    siret: Optional[str] = None
    notes: Optional[str] = None

class ClientResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    siret: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

class QuoteCreate(BaseModel):
    client_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    items: List[Dict[str, Any]] = []
    validity_days: int = 30
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    discount_percent: float = 0
    status: str = "draft"

class InvoiceCreate(BaseModel):
    client_id: str
    quote_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    items: List[Dict[str, Any]] = []
    due_days: int = 30
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    discount_percent: float = 0
    status: str = "draft"

class ProjectCreate(BaseModel):
    client_id: str
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: float = 0
    status: str = "pending"

# ============== AUTH ROUTES ==============

@router.get("/auth/me")
async def get_current_user_info(user: Dict = Depends(get_current_user)):
    """Get current user information"""
    return user

@router.put("/auth/profile")
async def update_profile(
    data: Dict[str, Any],
    user: Dict = Depends(get_current_user)
):
    """Update user profile"""
    supabase = get_supabase_client()
    
    allowed_fields = ["name", "phone", "company_name", "address", "siret", "business_type"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    result = supabase.from_("users")\
        .update(update_data)\
        .eq("id", user["id"])\
        .execute()
    
    return {"message": "Profil mis à jour", "data": result.data[0] if result.data else None}

# ============== DASHBOARD ==============

@router.get("/dashboard")
async def get_dashboard(user: Dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    supabase = get_supabase_client()
    user_id = user["id"]
    
    # Get counts
    clients = supabase.from_("clients").select("*", count="exact").eq("user_id", user_id).execute()
    quotes = supabase.from_("quotes").select("*", count="exact").eq("user_id", user_id).execute()
    invoices = supabase.from_("invoices").select("*", count="exact").eq("user_id", user_id).execute()
    projects = supabase.from_("projects").select("*", count="exact").eq("user_id", user_id).execute()
    
    # Get pending quotes
    pending_quotes = supabase.from_("quotes")\
        .select("*")\
        .eq("user_id", user_id)\
        .in_("status", ["draft", "sent"])\
        .execute()
    
    # Get unpaid invoices
    unpaid_invoices = supabase.from_("invoices")\
        .select("*")\
        .eq("user_id", user_id)\
        .neq("status", "paid")\
        .execute()
    
    # Calculate totals
    total_pending = sum(q.get("total_ttc", 0) for q in (pending_quotes.data or []))
    total_unpaid = sum(i.get("total_ttc", 0) for i in (unpaid_invoices.data or []))
    
    return {
        "clients_count": clients.count or 0,
        "quotes_count": quotes.count or 0,
        "invoices_count": invoices.count or 0,
        "projects_count": projects.count or 0,
        "pending_quotes_count": len(pending_quotes.data or []),
        "unpaid_invoices_count": len(unpaid_invoices.data or []),
        "total_pending": total_pending,
        "total_unpaid": total_unpaid,
        "recent_quotes": (pending_quotes.data or [])[:5],
        "recent_invoices": (unpaid_invoices.data or [])[:5],
    }

# ============== CLIENTS ==============

@router.get("/clients", response_model=List[ClientResponse])
async def list_clients(user: Dict = Depends(get_current_user)):
    """List all clients"""
    service = get_clients_service()
    clients = await service.get_all(user["id"])
    return clients

@router.get("/clients/{client_id}")
async def get_client(client_id: str, user: Dict = Depends(get_current_user)):
    """Get a client by ID"""
    service = get_clients_service()
    client = await service.get_by_id(client_id, user["id"])
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return client

@router.post("/clients", response_model=ClientResponse)
async def create_client(data: ClientCreate, user: Dict = Depends(get_current_user)):
    """Create a new client"""
    service = get_clients_service()
    client_data = data.dict()
    client_data["id"] = str(uuid.uuid4())
    result = await service.create(client_data, user["id"])
    return result

@router.put("/clients/{client_id}")
async def update_client(client_id: str, data: ClientCreate, user: Dict = Depends(get_current_user)):
    """Update a client"""
    service = get_clients_service()
    result = await service.update(client_id, data.dict(exclude_unset=True), user["id"])
    if not result:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return result

@router.delete("/clients/{client_id}")
async def delete_client(client_id: str, user: Dict = Depends(get_current_user)):
    """Delete a client"""
    service = get_clients_service()
    success = await service.delete(client_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return {"message": "Client supprimé"}

# ============== QUOTES ==============

@router.get("/quotes")
async def list_quotes(
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    """List quotes with optional filters"""
    supabase = get_supabase_client()
    
    query = supabase.from_("quotes")\
        .select("*, clients(*)")\
        .eq("user_id", user["id"])\
        .order("created_at", desc=True)
    
    if status:
        query = query.eq("status", status)
    if client_id:
        query = query.eq("client_id", client_id)
    
    result = query.execute()
    return result.data or []

@router.get("/quotes/{quote_id}")
async def get_quote(quote_id: str, user: Dict = Depends(get_current_user)):
    """Get a quote by ID"""
    service = get_quotes_service()
    quote = await service.get_with_client(quote_id, user["id"])
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    return quote

@router.post("/quotes")
async def create_quote(data: QuoteCreate, user: Dict = Depends(get_current_user)):
    """Create a new quote"""
    supabase = get_supabase_client()
    
    # Generate quote number
    count_result = supabase.from_("quotes")\
        .select("*", count="exact")\
        .eq("user_id", user["id"])\
        .execute()
    quote_number = f"DEV-{(count_result.count or 0) + 1:04d}"
    
    # Calculate totals
    items = data.items or []
    total_ht = sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in items)
    total_vat = total_ht * 0.20  # 20% VAT
    discount = total_ht * (data.discount_percent / 100)
    total_ttc = (total_ht - discount) + total_vat
    
    quote_data = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "client_id": data.client_id,
        "quote_number": quote_number,
        "title": data.title,
        "description": data.description,
        "items": items,
        "validity_days": data.validity_days,
        "notes": data.notes,
        "payment_terms": data.payment_terms,
        "discount_percent": data.discount_percent,
        "status": data.status,
        "total_ht": total_ht,
        "total_vat": total_vat,
        "total_ttc": total_ttc,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    result = supabase.from_("quotes").insert(quote_data).execute()
    return result.data[0] if result.data else quote_data

@router.put("/quotes/{quote_id}")
async def update_quote(quote_id: str, data: QuoteCreate, user: Dict = Depends(get_current_user)):
    """Update a quote"""
    supabase = get_supabase_client()
    
    # Recalculate totals
    items = data.items or []
    total_ht = sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in items)
    total_vat = total_ht * 0.20
    discount = total_ht * (data.discount_percent / 100)
    total_ttc = (total_ht - discount) + total_vat
    
    update_data = data.dict(exclude_unset=True)
    update_data["total_ht"] = total_ht
    update_data["total_vat"] = total_vat
    update_data["total_ttc"] = total_ttc
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    result = supabase.from_("quotes")\
        .update(update_data)\
        .eq("id", quote_id)\
        .eq("user_id", user["id"])\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    return result.data[0]

@router.delete("/quotes/{quote_id}")
async def delete_quote(quote_id: str, user: Dict = Depends(get_current_user)):
    """Delete a quote"""
    supabase = get_supabase_client()
    result = supabase.from_("quotes")\
        .delete()\
        .eq("id", quote_id)\
        .eq("user_id", user["id"])\
        .execute()
    return {"message": "Devis supprimé"}

@router.post("/quotes/{quote_id}/convert")
async def convert_quote_to_invoice(quote_id: str, user: Dict = Depends(get_current_user)):
    """Convert a quote to an invoice"""
    supabase = get_supabase_client()
    
    # Get quote
    quote_result = supabase.from_("quotes")\
        .select("*")\
        .eq("id", quote_id)\
        .eq("user_id", user["id"])\
        .single()\
        .execute()
    
    if not quote_result.data:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    quote = quote_result.data
    
    # Generate invoice number
    count_result = supabase.from_("invoices")\
        .select("*", count="exact")\
        .eq("user_id", user["id"])\
        .execute()
    invoice_number = f"FAC-{(count_result.count or 0) + 1:04d}"
    
    # Create invoice from quote
    invoice_data = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "client_id": quote["client_id"],
        "quote_id": quote_id,
        "invoice_number": invoice_number,
        "title": quote.get("title"),
        "description": quote.get("description"),
        "items": quote.get("items", []),
        "notes": quote.get("notes"),
        "payment_terms": quote.get("payment_terms"),
        "discount_percent": quote.get("discount_percent", 0),
        "status": "draft",
        "total_ht": quote.get("total_ht", 0),
        "total_vat": quote.get("total_vat", 0),
        "total_ttc": quote.get("total_ttc", 0),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    result = supabase.from_("invoices").insert(invoice_data).execute()
    
    # Update quote status
    supabase.from_("quotes")\
        .update({"status": "converted", "updated_at": datetime.utcnow().isoformat()})\
        .eq("id", quote_id)\
        .execute()
    
    return result.data[0] if result.data else invoice_data

# ============== INVOICES ==============

@router.get("/invoices")
async def list_invoices(
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    """List invoices with optional filters"""
    supabase = get_supabase_client()
    
    query = supabase.from_("invoices")\
        .select("*, clients(*)")\
        .eq("user_id", user["id"])\
        .order("created_at", desc=True)
    
    if status:
        query = query.eq("status", status)
    if client_id:
        query = query.eq("client_id", client_id)
    
    result = query.execute()
    return result.data or []

@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, user: Dict = Depends(get_current_user)):
    """Get an invoice by ID"""
    supabase = get_supabase_client()
    result = supabase.from_("invoices")\
        .select("*, clients(*)")\
        .eq("id", invoice_id)\
        .eq("user_id", user["id"])\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return result.data

@router.post("/invoices")
async def create_invoice(data: InvoiceCreate, user: Dict = Depends(get_current_user)):
    """Create a new invoice"""
    supabase = get_supabase_client()
    
    # Generate invoice number
    count_result = supabase.from_("invoices")\
        .select("*", count="exact")\
        .eq("user_id", user["id"])\
        .execute()
    invoice_number = f"FAC-{(count_result.count or 0) + 1:04d}"
    
    # Calculate totals
    items = data.items or []
    total_ht = sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in items)
    total_vat = total_ht * 0.20
    discount = total_ht * (data.discount_percent / 100)
    total_ttc = (total_ht - discount) + total_vat
    
    invoice_data = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "client_id": data.client_id,
        "quote_id": data.quote_id,
        "invoice_number": invoice_number,
        "title": data.title,
        "description": data.description,
        "items": items,
        "notes": data.notes,
        "payment_terms": data.payment_terms,
        "discount_percent": data.discount_percent,
        "status": data.status,
        "total_ht": total_ht,
        "total_vat": total_vat,
        "total_ttc": total_ttc,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    result = supabase.from_("invoices").insert(invoice_data).execute()
    return result.data[0] if result.data else invoice_data

@router.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, data: InvoiceCreate, user: Dict = Depends(get_current_user)):
    """Update an invoice"""
    supabase = get_supabase_client()
    
    # Recalculate totals
    items = data.items or []
    total_ht = sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in items)
    total_vat = total_ht * 0.20
    discount = total_ht * (data.discount_percent / 100)
    total_ttc = (total_ht - discount) + total_vat
    
    update_data = data.dict(exclude_unset=True)
    update_data["total_ht"] = total_ht
    update_data["total_vat"] = total_vat
    update_data["total_ttc"] = total_ttc
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    result = supabase.from_("invoices")\
        .update(update_data)\
        .eq("id", invoice_id)\
        .eq("user_id", user["id"])\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return result.data[0]

@router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str, user: Dict = Depends(get_current_user)):
    """Delete an invoice"""
    supabase = get_supabase_client()
    result = supabase.from_("invoices")\
        .delete()\
        .eq("id", invoice_id)\
        .eq("user_id", user["id"])\
        .execute()
    return {"message": "Facture supprimée"}

# ============== PROJECTS ==============

@router.get("/projects")
async def list_projects(user: Dict = Depends(get_current_user)):
    """List all projects"""
    supabase = get_supabase_client()
    result = supabase.from_("projects")\
        .select("*, clients(*)")\
        .eq("user_id", user["id"])\
        .order("created_at", desc=True)\
        .execute()
    return result.data or []

@router.get("/projects/{project_id}")
async def get_project(project_id: str, user: Dict = Depends(get_current_user)):
    """Get a project by ID"""
    supabase = get_supabase_client()
    result = supabase.from_("projects")\
        .select("*, clients(*)")\
        .eq("id", project_id)\
        .eq("user_id", user["id"])\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return result.data

@router.post("/projects")
async def create_project(data: ProjectCreate, user: Dict = Depends(get_current_user)):
    """Create a new project"""
    supabase = get_supabase_client()
    
    project_data = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        **data.dict(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    result = supabase.from_("projects").insert(project_data).execute()
    return result.data[0] if result.data else project_data

@router.put("/projects/{project_id}")
async def update_project(project_id: str, data: ProjectCreate, user: Dict = Depends(get_current_user)):
    """Update a project"""
    supabase = get_supabase_client()
    
    update_data = data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    result = supabase.from_("projects")\
        .update(update_data)\
        .eq("id", project_id)\
        .eq("user_id", user["id"])\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return result.data[0]

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, user: Dict = Depends(get_current_user)):
    """Delete a project"""
    supabase = get_supabase_client()
    result = supabase.from_("projects")\
        .delete()\
        .eq("id", project_id)\
        .eq("user_id", user["id"])\
        .execute()
    return {"message": "Projet supprimé"}
