"""
Work Item Library Service (Bibliothèque d'ouvrages)
Manages reusable work items for quotes and invoices
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import WorkItem
from app.core.security import generate_uuid

logger = logging.getLogger(__name__)


class WorkItemLibraryService:
    """Service for work item library (bibliothèque d'ouvrages)"""
    
    # Standard BTP categories
    CATEGORIES = [
        'gros_oeuvre',      # Gros œuvre
        'second_oeuvre',    # Second œuvre
        'electricite',      # Électricité
        'plomberie',        # Plomberie
        'chauffage',        # Chauffage
        'isolation',        # Isolation
        'menuiserie',       # Menuiserie
        'carrelage',        # Carrelage
        'peinture',         # Peinture
        'toiture',          # Toiture
        'maconnerie',       # Maçonnerie
        'terrassement',     # Terrassement
        'autres'            # Autres
    ]
    
    CATEGORY_LABELS = {
        'gros_oeuvre': 'Gros œuvre',
        'second_oeuvre': 'Second œuvre',
        'electricite': 'Électricité',
        'plomberie': 'Plomberie',
        'chauffage': 'Chauffage',
        'isolation': 'Isolation',
        'menuiserie': 'Menuiserie',
        'carrelage': 'Carrelage',
        'peinture': 'Peinture',
        'toiture': 'Toiture',
        'maconnerie': 'Maçonnerie',
        'terrassement': 'Terrassement',
        'autres': 'Autres'
    }
    
    # Standard units
    UNITS = ['u', 'm', 'm²', 'm³', 'h', 'j', 'kg', 'L', 'lot', 'forfait']
    
    UNIT_LABELS = {
        'u': 'Unité',
        'm': 'Mètre linéaire',
        'm²': 'Mètre carré',
        'm³': 'Mètre cube',
        'h': 'Heure',
        'j': 'Jour',
        'kg': 'Kilogramme',
        'L': 'Litre',
        'lot': 'Lot',
        'forfait': 'Forfait'
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_work_item(
        self, 
        user_id: str,
        name: str,
        description: Optional[str] = None,
        category: str = 'autres',
        unit: str = 'u',
        unit_price: float = 0,
        vat_rate: float = 20,
        is_template: bool = False,
        components: Optional[List[dict]] = None,
        labor_cost: Optional[float] = None,
        material_cost: Optional[float] = None
    ) -> WorkItem:
        """Create a new work item"""
        
        if category not in self.CATEGORIES:
            category = 'autres'
        
        if unit not in self.UNITS:
            unit = 'u'
        
        work_item = WorkItem(
            id=generate_uuid(),
            user_id=user_id,
            name=name,
            description=description,
            category=category,
            unit=unit,
            unit_price=unit_price,
            vat_rate=vat_rate,
            is_template=is_template,
            components=components or [],
            labor_cost=labor_cost,
            material_cost=material_cost,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(work_item)
        await self.db.flush()
        return work_item
    
    async def get_work_item_by_id(
        self, 
        item_id: str, 
        user_id: Optional[str] = None
    ) -> Optional[WorkItem]:
        """Get work item by ID"""
        query = select(WorkItem).where(WorkItem.id == item_id)
        
        if user_id:
            query = query.where(WorkItem.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_work_item(
        self, 
        item_id: str, 
        user_id: str,
        **kwargs
    ) -> Optional[WorkItem]:
        """Update a work item"""
        item = await self.get_work_item_by_id(item_id, user_id)
        if not item:
            return None
        
        # Validate category and unit
        if 'category' in kwargs and kwargs['category'] not in self.CATEGORIES:
            kwargs['category'] = 'autres'
        
        if 'unit' in kwargs and kwargs['unit'] not in self.UNITS:
            kwargs['unit'] = 'u'
        
        kwargs['updated_at'] = datetime.now(timezone.utc)
        
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        await self.db.flush()
        return item
    
    async def delete_work_item(self, item_id: str, user_id: str) -> bool:
        """Delete a work item"""
        item = await self.get_work_item_by_id(item_id, user_id)
        if not item:
            return False
        
        await self.db.delete(item)
        return True
    
    async def list_work_items(
        self, 
        user_id: str,
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        search: Optional[str] = None,
        is_template: Optional[bool] = None
    ) -> List[WorkItem]:
        """List work items for a user"""
        query = select(WorkItem).where(WorkItem.user_id == user_id)
        
        if category:
            query = query.where(WorkItem.category == category)
        
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (WorkItem.name.ilike(search_filter)) |
                (WorkItem.description.ilike(search_filter))
            )
        
        if is_template is not None:
            query = query.where(WorkItem.is_template == is_template)
        
        query = query.order_by(WorkItem.category, WorkItem.name).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_work_items(
        self, 
        user_id: str,
        category: Optional[str] = None
    ) -> int:
        """Count work items for a user"""
        query = select(func.count(WorkItem.id)).where(WorkItem.user_id == user_id)
        
        if category:
            query = query.where(WorkItem.category == category)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_items_by_category(self, user_id: str) -> dict:
        """Get work items grouped by category"""
        result = await self.db.execute(
            select(WorkItem.category, func.count(WorkItem.id))
            .where(WorkItem.user_id == user_id)
            .group_by(WorkItem.category)
        )
        
        category_counts = {row[0]: row[1] for row in result.all()}
        
        # Include all categories with 0 count
        return {
            cat: {
                'count': category_counts.get(cat, 0),
                'label': self.CATEGORY_LABELS.get(cat, cat)
            }
            for cat in self.CATEGORIES
        }
    
    async def duplicate_work_item(self, item_id: str, user_id: str) -> Optional[WorkItem]:
        """Duplicate an existing work item"""
        original = await self.get_work_item_by_id(item_id, user_id)
        if not original:
            return None
        
        return await self.create_work_item(
            user_id=user_id,
            name=f"{original.name} (copie)",
            description=original.description,
            category=original.category,
            unit=original.unit,
            unit_price=original.unit_price,
            vat_rate=original.vat_rate,
            is_template=original.is_template,
            components=original.components,
            labor_cost=original.labor_cost,
            material_cost=original.material_cost
        )
    
    async def import_predefined_items(self, user_id: str, items: List[dict]) -> int:
        """Import multiple work items (e.g., from a standard library)"""
        count = 0
        
        for item_data in items:
            await self.create_work_item(
                user_id=user_id,
                name=item_data.get('name', 'Item'),
                description=item_data.get('description'),
                category=item_data.get('category', 'autres'),
                unit=item_data.get('unit', 'u'),
                unit_price=item_data.get('unit_price', 0),
                vat_rate=item_data.get('vat_rate', 20),
                is_template=True,
                labor_cost=item_data.get('labor_cost'),
                material_cost=item_data.get('material_cost')
            )
            count += 1
        
        return count
    
    def get_categories(self) -> List[dict]:
        """Get list of available categories"""
        return [
            {'value': cat, 'label': self.CATEGORY_LABELS[cat]}
            for cat in self.CATEGORIES
        ]
    
    def get_units(self) -> List[dict]:
        """Get list of available units"""
        return [
            {'value': unit, 'label': self.UNIT_LABELS[unit]}
            for unit in self.UNITS
        ]


def get_work_item_library_service(db: AsyncSession) -> WorkItemLibraryService:
    """Factory function for dependency injection"""
    return WorkItemLibraryService(db)
