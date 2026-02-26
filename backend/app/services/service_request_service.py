"""
Services Pro - Service Request Management
Handles professional services requests for BTP businesses
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

logger = logging.getLogger(__name__)


# ============== MODELS ==============

class ServiceRequestCreate(BaseModel):
    """Model for creating a new service request"""
    service_type: str = Field(..., min_length=1, max_length=200)
    service_category: str = Field(..., min_length=1, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=200)
    contact_email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    quantity: Optional[int] = Field(None, ge=1)
    urgency: str = Field(default="standard")  # standard, express
    message: Optional[str] = Field(None, max_length=2000)
    logo_base64: Optional[str] = None  # Base64 encoded logo


class ServiceRequestResponse(BaseModel):
    """Response model for service request"""
    id: str
    user_id: str
    service_type: str
    service_category: str
    company_name: str
    contact_email: str
    phone: str
    quantity: Optional[int] = None
    urgency: str
    message: Optional[str] = None
    has_logo: bool = False
    status: str  # new, contacted, in_progress, completed, cancelled
    created_at: str
    updated_at: Optional[str] = None


class ServiceRequestStatusUpdate(BaseModel):
    """Model for updating service request status"""
    status: str = Field(...)
    admin_notes: Optional[str] = Field(None, max_length=1000)


# ============== SERVICE CATALOG ==============

SERVICE_CATALOG = {
    "website_visibility": {
        "name": "Sites Web et Visibilité",
        "icon": "Globe",
        "services": [
            {
                "id": "website_onepage",
                "name": "Site Web d'une seule page",
                "description": "Site vitrine professionnel d'une page",
                "price": 490,
                "price_label": "À partir de 490€",
            },
            {
                "id": "website_redesign",
                "name": "Refonte de Site Web",
                "description": "Modernisation de votre site existant",
                "price": 390,
                "price_label": "À partir de 390€",
            },
            {
                "id": "google_business",
                "name": "Optimisation Google Business",
                "description": "Visibilité locale optimisée sur Google",
                "price": 150,
                "price_label": "À partir de 150€",
            },
        ]
    },
    "business_cards": {
        "name": "Cartes de visite",
        "icon": "CreditCard",
        "services": [
            {
                "id": "cards_design",
                "name": "Cartes de visite - Design",
                "description": "Création graphique professionnelle",
                "price": 80,
                "price_label": "À partir de 80€",
            },
            {
                "id": "cards_print",
                "name": "Cartes de Visite - Impression",
                "description": "Impression haute qualité (500 ex.)",
                "price": 45,
                "price_label": "À partir de 45€",
            },
            {
                "id": "cards_pack",
                "name": "Cartes de Visite - Pack Complet",
                "description": "Design + Impression (500 ex.)",
                "price": 99,
                "price_label": "À partir de 99€",
                "recommended": True,
            },
        ]
    },
    "flyers_marketing": {
        "name": "Flyers et publicité",
        "icon": "FileText",
        "services": [
            {
                "id": "flyers_design",
                "name": "Flyers - Conception",
                "description": "Création graphique A5 ou A4",
                "price": 120,
                "price_label": "À partir de 120€",
            },
            {
                "id": "flyers_print",
                "name": "Flyers - Impression",
                "description": "Impression haute qualité (1000 ex.)",
                "price": 90,
                "price_label": "À partir de 90€",
            },
            {
                "id": "flyers_pack",
                "name": "Flyers - Pack complet",
                "description": "Design + Impression (1000 ex.)",
                "price": 180,
                "price_label": "À partir de 180€",
                "recommended": True,
            },
        ]
    },
    "it_support": {
        "name": "Support informatique",
        "icon": "Settings",
        "services": [
            {
                "id": "email_pro",
                "name": "Courriel Professionnel",
                "description": "Adresse e-mail de configuration : @votreentreprise.fr",
                "price": 60,
                "price_label": "À partir de 60€",
            },
            {
                "id": "domain_config",
                "name": "Domaine de configuration",
                "description": "Achat et configuration nom de domaine",
                "price": 80,
                "price_label": "À partir de 80€",
            },
            {
                "id": "it_basic",
                "name": "Support informatique de base",
                "description": "Assistance technique ponctuelle",
                "price": 50,
                "price_label": "À partir de 50€",
            },
        ]
    },
}

VALID_STATUSES = ["new", "contacted", "in_progress", "completed", "cancelled"]


# ============== SERVICE CLASS ==============

class ServiceRequestService:
    """Service for managing professional service requests"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.service_requests
    
    async def init_indexes(self) -> None:
        """Create necessary indexes"""
        try:
            await self.collection.create_index("user_id", name="idx_user_id")
            await self.collection.create_index("status", name="idx_status")
            await self.collection.create_index("created_at", name="idx_created_at")
            await self.collection.create_index(
                [("status", 1), ("created_at", -1)],
                name="idx_status_date"
            )
            logger.info("Service request indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def create_request(
        self,
        user_id: str,
        data: ServiceRequestCreate
    ) -> ServiceRequestResponse:
        """Create a new service request"""
        request_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        doc = {
            "id": request_id,
            "user_id": user_id,
            "service_type": data.service_type,
            "service_category": data.service_category,
            "company_name": data.company_name,
            "contact_email": data.contact_email,
            "phone": data.phone,
            "quantity": data.quantity,
            "urgency": data.urgency,
            "message": data.message,
            "logo_base64": data.logo_base64,
            "status": "new",
            "admin_notes": None,
            "created_at": now,
            "updated_at": None,
        }
        
        await self.collection.insert_one(doc)
        logger.info(f"Service request created: {request_id} by user {user_id}")
        
        return ServiceRequestResponse(
            id=request_id,
            user_id=user_id,
            service_type=data.service_type,
            service_category=data.service_category,
            company_name=data.company_name,
            contact_email=data.contact_email,
            phone=data.phone,
            quantity=data.quantity,
            urgency=data.urgency,
            message=data.message,
            has_logo=bool(data.logo_base64),
            status="new",
            created_at=now,
        )
    
    async def get_user_requests(self, user_id: str) -> List[ServiceRequestResponse]:
        """Get all service requests for a user"""
        requests = []
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        
        async for doc in cursor:
            try:
                requests.append(ServiceRequestResponse(
                    id=doc.get("id", ""),
                    user_id=doc.get("user_id", user_id),
                    service_type=doc.get("service_type", "Service inconnu"),
                    service_category=doc.get("service_category", "Non catégorisé"),
                    company_name=doc.get("company_name", ""),
                    contact_email=doc.get("contact_email", doc.get("email", "")),
                    phone=doc.get("phone", ""),
                    quantity=doc.get("quantity"),
                    urgency=doc.get("urgency", "standard"),
                    message=doc.get("message"),
                    has_logo=bool(doc.get("logo_base64")),
                    status=doc.get("status", "new"),
                    created_at=doc.get("created_at", ""),
                    updated_at=doc.get("updated_at"),
                ))
            except Exception as e:
                logger.warning(f"Error parsing service request: {e}")
                continue
        
        return requests
    
    async def get_all_requests(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all service requests (admin only)"""
        query = {}
        if status_filter and status_filter in VALID_STATUSES:
            query["status"] = status_filter
        
        requests = []
        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        
        async for doc in cursor:
            doc.pop("_id", None)
            doc.pop("logo_base64", None)  # Don't send logo in list view
            doc["has_logo"] = bool(doc.get("logo_base64"))
            requests.append(doc)
        
        return requests
    
    async def get_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific service request"""
        doc = await self.collection.find_one({"id": request_id})
        if doc:
            doc.pop("_id", None)
            return doc
        return None
    
    async def update_status(
        self,
        request_id: str,
        status: str,
        admin_notes: Optional[str] = None
    ) -> Optional[ServiceRequestResponse]:
        """Update service request status (admin only)"""
        if status not in VALID_STATUSES:
            return None
        
        now = datetime.now(timezone.utc).isoformat()
        update_data = {
            "status": status,
            "updated_at": now,
        }
        if admin_notes is not None:
            update_data["admin_notes"] = admin_notes
        
        result = await self.collection.find_one_and_update(
            {"id": request_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            result.pop("_id", None)
            logger.info(f"Service request {request_id} status updated to {status}")
            return ServiceRequestResponse(
                id=result["id"],
                user_id=result["user_id"],
                service_type=result["service_type"],
                service_category=result["service_category"],
                company_name=result["company_name"],
                contact_email=result["contact_email"],
                phone=result["phone"],
                quantity=result.get("quantity"),
                urgency=result["urgency"],
                message=result.get("message"),
                has_logo=bool(result.get("logo_base64")),
                status=result["status"],
                created_at=result["created_at"],
                updated_at=result.get("updated_at"),
            )
        return None
    
    async def get_stats(self) -> Dict[str, int]:
        """Get service request statistics"""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        
        stats = {"total": 0, "new": 0, "contacted": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
        
        async for doc in self.collection.aggregate(pipeline):
            status = doc["_id"]
            count = doc["count"]
            if status in stats:
                stats[status] = count
            stats["total"] += count
        
        return stats


def get_service_request_service(db: AsyncIOMotorDatabase) -> ServiceRequestService:
    """Factory function for ServiceRequestService"""
    return ServiceRequestService(db)
