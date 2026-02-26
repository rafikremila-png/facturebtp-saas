"""
Service Categories Management for BTP Facture
Handles business-type filtering for predefined categories and items
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
import uuid

logger = logging.getLogger(__name__)

# ============== CONSTANTS ==============

VALID_BUSINESS_TYPES = [
    "general",
    "electrician", 
    "plumber",
    "mason",
    "painter",
    "carpenter",
    "it_installer"
]

BUSINESS_TYPE_LABELS = {
    "general": "Général / Multi-corps",
    "electrician": "Électricien",
    "plumber": "Plombier",
    "mason": "Maçon",
    "painter": "Peintre",
    "carpenter": "Menuisier",
    "it_installer": "Installateur réseaux / IT"
}

# ============== MODELS ==============

class ServiceCategory(BaseModel):
    id: str
    name: str
    business_types: List[str]
    icon: Optional[str] = None
    created_at: str


class ServiceItem(BaseModel):
    id: str
    category_id: str
    name: str
    description: Optional[str] = None
    default_price: Optional[float] = None
    unit: Optional[str] = None
    created_at: str


# ============== SEED DATA ==============

SEED_CATEGORIES = [
    {
        "name": "Maçonnerie",
        "business_types": ["mason", "general"],
        "icon": "Blocks"
    },
    {
        "name": "Électricité",
        "business_types": ["electrician", "general"],
        "icon": "Zap"
    },
    {
        "name": "Plomberie",
        "business_types": ["plumber", "general"],
        "icon": "Droplets"
    },
    {
        "name": "Peinture",
        "business_types": ["painter", "general"],
        "icon": "Paintbrush"
    },
    {
        "name": "Menuiserie",
        "business_types": ["carpenter", "general"],
        "icon": "Hammer"
    },
    {
        "name": "Carrelage",
        "business_types": ["mason", "general"],
        "icon": "Grid3x3"
    },
    {
        "name": "Plâtrerie / Isolation",
        "business_types": ["mason", "general"],
        "icon": "Layers"
    },
    {
        "name": "Rénovation générale",
        "business_types": ["general"],
        "icon": "Home"
    },
    {
        "name": "Réseaux & Courants Faibles",
        "business_types": ["electrician", "general", "it_installer"],
        "icon": "Network"
    },
]

SEED_ITEMS = {
    "Maçonnerie": [
        {"name": "Coulage dalle béton", "description": "Coulage dalle béton armé", "default_price": 80, "unit": "m²"},
        {"name": "Montage mur parpaings", "description": "Construction mur en parpaings", "default_price": 65, "unit": "m²"},
        {"name": "Ouverture mur porteur", "description": "Création ouverture avec renfort IPN", "default_price": 1500, "unit": "forfait"},
        {"name": "Enduit façade", "description": "Application enduit extérieur", "default_price": 45, "unit": "m²"},
    ],
    "Électricité": [
        {"name": "Installation prise électrique", "description": "Pose prise 16A avec encastrement", "default_price": 65, "unit": "unité"},
        {"name": "Installation interrupteur", "description": "Pose interrupteur simple/double", "default_price": 55, "unit": "unité"},
        {"name": "Tableau électrique", "description": "Installation tableau électrique complet", "default_price": 850, "unit": "forfait"},
        {"name": "Mise aux normes NF C 15-100", "description": "Mise en conformité installation", "default_price": 1200, "unit": "forfait"},
        {"name": "Pose luminaire", "description": "Installation point lumineux", "default_price": 75, "unit": "unité"},
        {"name": "Tirage de câble", "description": "Passage câble électrique", "default_price": 15, "unit": "ml"},
    ],
    "Plomberie": [
        {"name": "Installation WC", "description": "Pose WC complet avec raccordement", "default_price": 350, "unit": "forfait"},
        {"name": "Pose chauffe-eau", "description": "Installation chauffe-eau électrique", "default_price": 450, "unit": "forfait"},
        {"name": "Réparation fuite", "description": "Recherche et réparation fuite", "default_price": 120, "unit": "forfait"},
        {"name": "Installation lavabo", "description": "Pose lavabo avec robinetterie", "default_price": 280, "unit": "forfait"},
        {"name": "Pose baignoire", "description": "Installation baignoire complète", "default_price": 550, "unit": "forfait"},
        {"name": "Débouchage canalisation", "description": "Débouchage manuel ou haute pression", "default_price": 150, "unit": "forfait"},
    ],
    "Peinture": [
        {"name": "Peinture mur", "description": "Application peinture 2 couches", "default_price": 25, "unit": "m²"},
        {"name": "Peinture plafond", "description": "Application peinture plafond", "default_price": 30, "unit": "m²"},
        {"name": "Préparation support", "description": "Enduit + ponçage + sous-couche", "default_price": 18, "unit": "m²"},
        {"name": "Peinture boiserie", "description": "Peinture portes/plinthes/fenêtres", "default_price": 35, "unit": "ml"},
        {"name": "Papier peint", "description": "Pose papier peint intissé", "default_price": 28, "unit": "m²"},
    ],
    "Menuiserie": [
        {"name": "Pose porte intérieure", "description": "Fourniture et pose porte + huisserie", "default_price": 450, "unit": "unité"},
        {"name": "Pose fenêtre PVC", "description": "Dépose + pose fenêtre PVC", "default_price": 650, "unit": "unité"},
        {"name": "Installation cuisine", "description": "Montage meubles cuisine", "default_price": 150, "unit": "ml"},
        {"name": "Pose parquet", "description": "Pose parquet flottant", "default_price": 35, "unit": "m²"},
        {"name": "Création placard", "description": "Aménagement placard sur mesure", "default_price": 800, "unit": "forfait"},
    ],
    "Carrelage": [
        {"name": "Pose carrelage sol", "description": "Pose carrelage format standard", "default_price": 45, "unit": "m²"},
        {"name": "Pose carrelage mural", "description": "Pose faïence murale", "default_price": 55, "unit": "m²"},
        {"name": "Pose mosaïque", "description": "Pose mosaïque décorative", "default_price": 75, "unit": "m²"},
        {"name": "Ragréage sol", "description": "Préparation sol avant pose", "default_price": 20, "unit": "m²"},
    ],
    "Plâtrerie / Isolation": [
        {"name": "Pose placo BA13", "description": "Pose plaques de plâtre", "default_price": 35, "unit": "m²"},
        {"name": "Isolation laine de verre", "description": "Pose isolant thermique", "default_price": 25, "unit": "m²"},
        {"name": "Faux plafond", "description": "Installation faux plafond suspendu", "default_price": 55, "unit": "m²"},
        {"name": "Cloison placo", "description": "Création cloison avec isolation", "default_price": 65, "unit": "m²"},
        {"name": "Bandes et joints", "description": "Finition joints placo", "default_price": 12, "unit": "ml"},
    ],
    "Rénovation générale": [
        {"name": "Démolition cloison", "description": "Démolition et évacuation", "default_price": 45, "unit": "m²"},
        {"name": "Évacuation gravats", "description": "Enlèvement et mise en décharge", "default_price": 250, "unit": "m³"},
        {"name": "Main d'œuvre", "description": "Heure de main d'œuvre", "default_price": 45, "unit": "heure"},
        {"name": "Déplacement", "description": "Frais de déplacement", "default_price": 50, "unit": "forfait"},
        {"name": "Étude / Conseil", "description": "Étude technique et conseil", "default_price": 80, "unit": "heure"},
    ],
    "Réseaux & Courants Faibles": [
        {"name": "Installation prise RJ45", "description": "Pose prise réseau cat.6", "default_price": 85, "unit": "unité"},
        {"name": "Câblage réseau complet", "description": "Tirage câble réseau + raccordement", "default_price": 25, "unit": "ml"},
        {"name": "Baie de brassage", "description": "Installation baie 19 pouces équipée", "default_price": 650, "unit": "forfait"},
        {"name": "Installation caméra IP", "description": "Pose caméra + configuration", "default_price": 250, "unit": "unité"},
        {"name": "Installation alarme", "description": "Système alarme sans fil", "default_price": 450, "unit": "forfait"},
        {"name": "Configuration routeur/switch", "description": "Paramétrage équipement réseau", "default_price": 120, "unit": "forfait"},
        {"name": "Pose fibre optique interne", "description": "Tirage fibre + soudure", "default_price": 35, "unit": "ml"},
        {"name": "Installation interphone/visiophone", "description": "Pose système interphone", "default_price": 350, "unit": "forfait"},
        {"name": "Câblage téléphonique", "description": "Installation ligne téléphonique", "default_price": 65, "unit": "unité"},
        {"name": "Installation TV/SAT", "description": "Pose antenne + câblage coaxial", "default_price": 180, "unit": "forfait"},
    ],
}


# ============== SERVICE CLASS ==============

class CategoryService:
    """Service for managing service categories and items"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.categories = db.service_categories
        self.items = db.service_items
    
    async def init_indexes(self) -> None:
        """Create necessary indexes"""
        try:
            await self.categories.create_index("name", unique=True)
            await self.categories.create_index("business_types")
            await self.items.create_index("category_id")
            await self.items.create_index([("category_id", 1), ("name", 1)])
            logger.info("Category service indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def seed_categories(self, force: bool = False) -> Dict[str, int]:
        """
        Seed default categories and items.
        
        Args:
            force: If True, delete existing and reseed
            
        Returns:
            Dict with counts of seeded categories and items
        """
        stats = {"categories": 0, "items": 0, "skipped": 0}
        
        # Check if already seeded
        existing_count = await self.categories.count_documents({})
        if existing_count > 0 and not force:
            logger.info(f"Categories already seeded ({existing_count} found). Skipping.")
            stats["skipped"] = existing_count
            return stats
        
        if force:
            await self.categories.delete_many({})
            await self.items.delete_many({})
            logger.info("Force reseed: cleared existing categories and items")
        
        now = datetime.now(timezone.utc).isoformat()
        category_id_map = {}
        
        # Seed categories
        for cat_data in SEED_CATEGORIES:
            cat_id = str(uuid.uuid4())
            category_doc = {
                "id": cat_id,
                "name": cat_data["name"],
                "business_types": cat_data["business_types"],
                "icon": cat_data.get("icon"),
                "created_at": now
            }
            await self.categories.insert_one(category_doc)
            category_id_map[cat_data["name"]] = cat_id
            stats["categories"] += 1
        
        # Seed items
        for cat_name, items_list in SEED_ITEMS.items():
            cat_id = category_id_map.get(cat_name)
            if not cat_id:
                logger.warning(f"Category not found for items: {cat_name}")
                continue
            
            for item_data in items_list:
                item_doc = {
                    "id": str(uuid.uuid4()),
                    "category_id": cat_id,
                    "name": item_data["name"],
                    "description": item_data.get("description"),
                    "default_price": item_data.get("default_price"),
                    "unit": item_data.get("unit"),
                    "created_at": now
                }
                await self.items.insert_one(item_doc)
                stats["items"] += 1
        
        logger.info(f"Seeded {stats['categories']} categories and {stats['items']} items")
        return stats
    
    async def get_categories_for_user(
        self, 
        business_type: str = "general"
    ) -> List[Dict[str, Any]]:
        """
        Get categories filtered by user's business type.
        
        Args:
            business_type: User's business type
            
        Returns:
            List of categories matching user's business type
        """
        if business_type not in VALID_BUSINESS_TYPES:
            business_type = "general"
        
        # Find categories where business_type is in business_types array
        # OR "general" is in business_types (available to all)
        query = {
            "$or": [
                {"business_types": business_type},
                {"business_types": "general"}
            ]
        }
        
        # If user is "general", show all categories
        if business_type == "general":
            query = {}
        
        categories = []
        cursor = self.categories.find(query).sort("name", 1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            categories.append(doc)
        
        return categories
    
    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories (admin view)"""
        categories = []
        cursor = self.categories.find({}).sort("name", 1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            categories.append(doc)
        
        return categories
    
    async def get_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get a single category by ID"""
        doc = await self.categories.find_one({"id": category_id})
        if doc:
            doc.pop("_id", None)
            return doc
        return None
    
    async def get_items_by_category(self, category_id: str) -> List[Dict[str, Any]]:
        """Get all items for a category"""
        items = []
        cursor = self.items.find({"category_id": category_id}).sort("name", 1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            items.append(doc)
        
        return items
    
    async def get_categories_with_items(
        self, 
        business_type: str = "general"
    ) -> List[Dict[str, Any]]:
        """
        Get categories with their items (for dropdown/picker UI).
        Filtered by business type.
        """
        categories = await self.get_categories_for_user(business_type)
        
        result = []
        for cat in categories:
            items = await self.get_items_by_category(cat["id"])
            result.append({
                **cat,
                "items": items
            })
        
        return result
    
    async def search_items(
        self, 
        query: str, 
        business_type: str = "general",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search items by name across allowed categories"""
        # First get allowed category IDs
        categories = await self.get_categories_for_user(business_type)
        category_ids = [c["id"] for c in categories]
        
        # Search items in those categories
        search_query = {
            "category_id": {"$in": category_ids},
            "name": {"$regex": query, "$options": "i"}
        }
        
        items = []
        cursor = self.items.find(search_query).limit(limit)
        
        async for doc in cursor:
            doc.pop("_id", None)
            items.append(doc)
        
        return items


def get_category_service(db: AsyncIOMotorDatabase) -> CategoryService:
    """Factory function for CategoryService"""
    return CategoryService(db)
