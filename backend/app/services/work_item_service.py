"""
Work Item Service (Bibliothèque d'ouvrages)
Handles construction work items/materials library
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from app.core.database import db, is_mongodb

logger = logging.getLogger(__name__)

# Default BTP work categories
DEFAULT_CATEGORIES = [
    "Gros œuvre",
    "Second œuvre",
    "Maçonnerie",
    "Plomberie",
    "Électricité",
    "Chauffage/Climatisation",
    "Menuiserie",
    "Peinture",
    "Revêtements",
    "Toiture",
    "Isolation",
    "Démolition",
    "Terrassement",
    "Aménagement extérieur"
]

# Common units in BTP
BTP_UNITS = {
    "u": "Unité",
    "m²": "Mètre carré",
    "m³": "Mètre cube",
    "ml": "Mètre linéaire",
    "h": "Heure",
    "j": "Jour",
    "forfait": "Forfait",
    "kg": "Kilogramme",
    "t": "Tonne",
    "l": "Litre"
}

class WorkItemService:
    """Service for managing work items library"""
    
    @staticmethod
    async def create(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new work item"""
        work_item = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": data["name"],
            "description": data.get("description", ""),
            "category": data.get("category", ""),
            "unit": data.get("unit", "u"),
            "unit_price": data["unit_price"],
            "vat_rate": data.get("vat_rate", 20.0),
            "labor_cost": data.get("labor_cost", 0),
            "material_cost": data.get("material_cost", 0),
            "reference": data.get("reference", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if is_mongodb():
            await db.work_items.insert_one(work_item.copy())
        
        return work_item
    
    @staticmethod
    async def get_by_id(work_item_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get work item by ID"""
        if is_mongodb():
            return await db.work_items.find_one(
                {"id": work_item_id, "user_id": user_id},
                {"_id": 0}
            )
        return None
    
    @staticmethod
    async def get_all(user_id: str, category: Optional[str] = None,
                      search: Optional[str] = None,
                      skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all work items for a user"""
        query = {"user_id": user_id}
        
        if category:
            query["category"] = category
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"reference": {"$regex": search, "$options": "i"}}
            ]
        
        if is_mongodb():
            cursor = db.work_items.find(query, {"_id": 0}).sort("name", 1).skip(skip).limit(limit)
            return await cursor.to_list(length=limit)
        return []
    
    @staticmethod
    async def get_by_category(user_id: str, category: str) -> List[Dict[str, Any]]:
        """Get work items by category"""
        if is_mongodb():
            cursor = db.work_items.find(
                {"user_id": user_id, "category": category},
                {"_id": 0}
            ).sort("name", 1)
            return await cursor.to_list(length=500)
        return []
    
    @staticmethod
    async def get_categories(user_id: str) -> List[str]:
        """Get all categories used by a user"""
        if is_mongodb():
            categories = await db.work_items.distinct("category", {"user_id": user_id})
            # Merge with default categories
            all_categories = set(categories) | set(DEFAULT_CATEGORIES)
            return sorted(list(all_categories))
        return DEFAULT_CATEGORIES
    
    @staticmethod
    async def update(work_item_id: str, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a work item"""
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        if is_mongodb():
            result = await db.work_items.update_one(
                {"id": work_item_id, "user_id": user_id},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                return await WorkItemService.get_by_id(work_item_id, user_id)
        return None
    
    @staticmethod
    async def delete(work_item_id: str, user_id: str) -> bool:
        """Delete a work item"""
        if is_mongodb():
            result = await db.work_items.delete_one(
                {"id": work_item_id, "user_id": user_id}
            )
            return result.deleted_count > 0
        return False
    
    @staticmethod
    async def bulk_create(user_id: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk create work items"""
        work_items = []
        now = datetime.now(timezone.utc).isoformat()
        
        for item_data in items:
            work_item = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": item_data["name"],
                "description": item_data.get("description", ""),
                "category": item_data.get("category", ""),
                "unit": item_data.get("unit", "u"),
                "unit_price": item_data["unit_price"],
                "vat_rate": item_data.get("vat_rate", 20.0),
                "labor_cost": item_data.get("labor_cost", 0),
                "material_cost": item_data.get("material_cost", 0),
                "reference": item_data.get("reference", ""),
                "created_at": now,
                "updated_at": now
            }
            work_items.append(work_item)
        
        if is_mongodb() and work_items:
            await db.work_items.insert_many(work_items)
        
        return work_items
    
    @staticmethod
    async def import_from_csv(user_id: str, csv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import work items from CSV data"""
        success = 0
        errors = []
        
        for idx, row in enumerate(csv_data):
            try:
                # Validate required fields
                if not row.get("name"):
                    errors.append(f"Ligne {idx + 1}: Nom requis")
                    continue
                if not row.get("unit_price"):
                    errors.append(f"Ligne {idx + 1}: Prix unitaire requis")
                    continue
                
                await WorkItemService.create(user_id, {
                    "name": row["name"],
                    "description": row.get("description", ""),
                    "category": row.get("category", ""),
                    "unit": row.get("unit", "u"),
                    "unit_price": float(row["unit_price"]),
                    "vat_rate": float(row.get("vat_rate", 20.0)),
                    "labor_cost": float(row.get("labor_cost", 0)),
                    "material_cost": float(row.get("material_cost", 0)),
                    "reference": row.get("reference", "")
                })
                success += 1
            except Exception as e:
                errors.append(f"Ligne {idx + 1}: {str(e)}")
        
        return {
            "success_count": success,
            "error_count": len(errors),
            "errors": errors
        }
    
    @staticmethod
    def get_units() -> Dict[str, str]:
        """Get available units"""
        return BTP_UNITS
    
    @staticmethod
    def get_default_categories() -> List[str]:
        """Get default BTP categories"""
        return DEFAULT_CATEGORIES


# Create singleton instance
work_item_service = WorkItemService()
