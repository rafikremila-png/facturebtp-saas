"""
Work Item Library Routes (Bibliothèque d'ouvrages)
API for managing reusable work items
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.services.work_item_library_service import get_work_item_library_service
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/work-items", tags=["Work Item Library (Bibliothèque)"])


# ============== SCHEMAS ==============

class WorkItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = "autres"
    unit: str = "u"
    unit_price: float = Field(0, ge=0)
    vat_rate: float = Field(20, ge=0, le=100)
    is_template: bool = False
    components: Optional[List[dict]] = None
    labor_cost: Optional[float] = Field(None, ge=0)
    material_cost: Optional[float] = Field(None, ge=0)


class WorkItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = Field(None, ge=0)
    vat_rate: Optional[float] = Field(None, ge=0, le=100)
    is_template: Optional[bool] = None
    components: Optional[List[dict]] = None
    labor_cost: Optional[float] = Field(None, ge=0)
    material_cost: Optional[float] = Field(None, ge=0)


class WorkItemResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    category: str
    unit: str
    unit_price: float
    vat_rate: float
    is_template: bool
    components: Optional[List[dict]]
    labor_cost: Optional[float]
    material_cost: Optional[float]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ============== ROUTES ==============

@router.post("", response_model=WorkItemResponse)
async def create_work_item(
    item_data: WorkItemCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new work item in the library."""
    service = get_work_item_library_service(db)
    item = await service.create_work_item(
        user_id=current_user["id"],
        **item_data.model_dump()
    )
    return _format_response(item)


@router.get("", response_model=List[WorkItemResponse])
async def list_work_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_template: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all work items in the library."""
    service = get_work_item_library_service(db)
    items = await service.list_work_items(
        user_id=current_user["id"],
        skip=skip,
        limit=limit,
        category=category,
        search=search,
        is_template=is_template
    )
    return [_format_response(item) for item in items]


@router.get("/categories")
async def get_categories(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available categories with item counts."""
    service = get_work_item_library_service(db)
    
    return {
        'categories': service.get_categories(),
        'by_category': await service.get_items_by_category(current_user["id"])
    }


@router.get("/units")
async def get_units(
    current_user: dict = Depends(get_current_user)
):
    """Get available units of measurement."""
    service = get_work_item_library_service(None)  # Doesn't need DB
    return service.get_units()


@router.get("/{item_id}", response_model=WorkItemResponse)
async def get_work_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific work item."""
    service = get_work_item_library_service(db)
    item = await service.get_work_item_by_id(item_id, current_user["id"])
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ouvrage non trouvé"
        )
    
    return _format_response(item)


@router.put("/{item_id}", response_model=WorkItemResponse)
async def update_work_item(
    item_id: str,
    item_data: WorkItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a work item."""
    service = get_work_item_library_service(db)
    item = await service.update_work_item(
        item_id,
        current_user["id"],
        **item_data.model_dump(exclude_unset=True)
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ouvrage non trouvé"
        )
    
    return _format_response(item)


@router.delete("/{item_id}")
async def delete_work_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a work item."""
    service = get_work_item_library_service(db)
    success = await service.delete_work_item(item_id, current_user["id"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ouvrage non trouvé"
        )
    
    return {"message": "Ouvrage supprimé"}


@router.post("/{item_id}/duplicate", response_model=WorkItemResponse)
async def duplicate_work_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Duplicate a work item."""
    service = get_work_item_library_service(db)
    item = await service.duplicate_work_item(item_id, current_user["id"])
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ouvrage non trouvé"
        )
    
    return _format_response(item)


@router.post("/import")
async def import_work_items(
    items: List[WorkItemCreate],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import multiple work items."""
    service = get_work_item_library_service(db)
    count = await service.import_predefined_items(
        current_user["id"],
        [item.model_dump() for item in items]
    )
    
    return {
        "message": f"{count} ouvrages importés",
        "count": count
    }


def _format_response(item) -> dict:
    """Format work item for response"""
    return {
        'id': item.id,
        'user_id': item.user_id,
        'name': item.name,
        'description': item.description,
        'category': item.category,
        'unit': item.unit,
        'unit_price': float(item.unit_price or 0),
        'vat_rate': float(item.vat_rate or 20),
        'is_template': item.is_template or False,
        'components': item.components,
        'labor_cost': float(item.labor_cost) if item.labor_cost else None,
        'material_cost': float(item.material_cost) if item.material_cost else None,
        'created_at': item.created_at.isoformat() if item.created_at else None,
        'updated_at': item.updated_at.isoformat() if item.updated_at else None
    }
