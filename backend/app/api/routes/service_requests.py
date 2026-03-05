"""
Service Request Routes - PostgreSQL Implementation
API endpoints for service categories, services, and requests
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
import logging

from app.core.database import get_db
from app.services.service_request_pg_service import (
    get_service_category_service,
    get_service_request_pg_service
)
from app.api.deps import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Services"])


# ============== SCHEMAS ==============

class ServiceRequestCreate(BaseModel):
    """Schema for creating a service request"""
    category_id: str
    service_id: str
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_email: EmailStr
    phone: str = Field(..., min_length=10, max_length=50)
    message: Optional[str] = Field(None, max_length=2000)
    quantity: Optional[int] = Field(1, ge=1)
    urgency: Optional[str] = Field("standard", pattern="^(standard|express)$")
    logo_base64: Optional[str] = None


class ServiceRequestStatusUpdate(BaseModel):
    """Schema for updating request status"""
    status: str = Field(..., pattern="^(pending|in_progress|completed|cancelled)$")
    admin_notes: Optional[str] = Field(None, max_length=1000)


# ============== CATEGORY ROUTES ==============

@router.get("/service-categories")
async def get_service_categories(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all service categories with their services"""
    service = get_service_category_service(db)
    
    # Seed default data if empty
    await service.seed_default_data()
    await db.commit()
    
    return await service.get_all_categories(include_services=True)


@router.get("/service-categories/{category_id}")
async def get_service_category(
    category_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific category with its services"""
    service = get_service_category_service(db)
    category = await service.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    
    return category


@router.get("/service-categories/{category_id}/services")
async def get_category_services(
    category_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all services for a category"""
    service = get_service_category_service(db)
    return await service.get_services_by_category(category_id)


# ============== SERVICE REQUEST ROUTES ==============

@router.post("/service-requests")
async def create_service_request(
    data: ServiceRequestCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new service request"""
    service = get_service_request_pg_service(db)
    
    request = await service.create_request(
        user_id=current_user["id"],
        category_id=data.category_id,
        service_id=data.service_id,
        company_name=data.company_name,
        contact_email=data.contact_email,
        phone=data.phone,
        message=data.message,
        quantity=data.quantity or 1,
        urgency=data.urgency or "standard",
        logo_base64=data.logo_base64
    )
    
    await db.commit()
    return request


@router.get("/service-requests/me")
async def get_my_service_requests(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's service requests"""
    service = get_service_request_pg_service(db)
    return await service.get_user_requests(current_user["id"])


@router.get("/service-requests")
async def get_all_service_requests(
    status: Optional[str] = Query(None, pattern="^(pending|in_progress|completed|cancelled)$"),
    category_id: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all service requests (admin only)"""
    service = get_service_request_pg_service(db)
    return await service.get_all_requests(
        status_filter=status,
        category_filter=category_id
    )


@router.get("/service-requests/{request_id}")
async def get_service_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific service request"""
    service = get_service_request_pg_service(db)
    request = await service.get_request_by_id(request_id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée"
        )
    
    # Check ownership or admin
    if request["user_id"] != current_user["id"] and current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    return request


@router.put("/service-requests/{request_id}/status")
async def update_service_request_status(
    request_id: str,
    data: ServiceRequestStatusUpdate,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update service request status (admin only)"""
    service = get_service_request_pg_service(db)
    
    result = await service.update_request_status(
        request_id=request_id,
        status=data.status,
        admin_notes=data.admin_notes
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée"
        )
    
    await db.commit()
    return result


@router.get("/service-requests/stats")
async def get_service_stats(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get service request statistics (admin only)"""
    service = get_service_request_pg_service(db)
    return await service.get_stats()
