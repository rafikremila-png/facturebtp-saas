"""
Work Item Routes (Bibliothèque d'ouvrages)
API endpoints for construction work items library
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
import csv
import io

from app.api.deps import get_current_user
from app.services.work_item_service import work_item_service

router = APIRouter(prefix="/work-items", tags=["Work Items"])


class WorkItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = "u"
    unit_price: float
    vat_rate: Optional[float] = 20.0
    labor_cost: Optional[float] = 0
    material_cost: Optional[float] = 0
    reference: Optional[str] = None


@router.post("")
async def create_work_item(data: WorkItemCreate, user: dict = Depends(get_current_user)):
    """Create a new work item"""
    item = await work_item_service.create(user["id"], data.model_dump())
    return item


@router.get("")
async def list_work_items(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(get_current_user)
):
    """List all work items for the current user"""
    return await work_item_service.get_all(
        user["id"],
        category=category,
        search=search,
        skip=skip,
        limit=limit
    )


@router.get("/categories")
async def list_categories(user: dict = Depends(get_current_user)):
    """Get all work item categories"""
    categories = await work_item_service.get_categories(user["id"])
    return {"categories": categories}


@router.get("/units")
async def list_units():
    """Get all available units"""
    return {"units": work_item_service.get_units()}


@router.get("/{item_id}")
async def get_work_item(item_id: str, user: dict = Depends(get_current_user)):
    """Get a work item by ID"""
    item = await work_item_service.get_by_id(item_id, user["id"])
    if not item:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return item


@router.put("/{item_id}")
async def update_work_item(
    item_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    unit: Optional[str] = None,
    unit_price: Optional[float] = None,
    vat_rate: Optional[float] = None,
    user: dict = Depends(get_current_user)
):
    """Update a work item"""
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if category is not None:
        data["category"] = category
    if unit is not None:
        data["unit"] = unit
    if unit_price is not None:
        data["unit_price"] = unit_price
    if vat_rate is not None:
        data["vat_rate"] = vat_rate
    
    item = await work_item_service.update(item_id, user["id"], data)
    if not item:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return item


@router.delete("/{item_id}")
async def delete_work_item(item_id: str, user: dict = Depends(get_current_user)):
    """Delete a work item"""
    success = await work_item_service.delete(item_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return {"message": "Article supprimé"}


@router.post("/import")
async def import_work_items(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Import work items from CSV"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers CSV sont acceptés")
    
    content = await file.read()
    decoded = content.decode('utf-8-sig')
    
    reader = csv.DictReader(io.StringIO(decoded), delimiter=';')
    rows = list(reader)
    
    if not rows:
        raise HTTPException(status_code=400, detail="Le fichier est vide")
    
    result = await work_item_service.import_from_csv(user["id"], rows)
    return result


@router.post("/bulk")
async def bulk_create_work_items(items: List[WorkItemCreate], user: dict = Depends(get_current_user)):
    """Create multiple work items at once"""
    created = await work_item_service.bulk_create(
        user["id"],
        [item.model_dump() for item in items]
    )
    return {"created_count": len(created), "items": created}
