"""
Service Request Service - PostgreSQL Implementation
Handles service categories, services, and service requests
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import ServiceCategory, Service, ServiceRequest
from app.core.security import generate_uuid

logger = logging.getLogger(__name__)


# ============== SERVICE CATEGORIES ==============

# Pre-filled categories and services
DEFAULT_CATEGORIES = [
    {
        "name": "Site Web",
        "icon": "Globe",
        "description": "Création et gestion de sites web professionnels",
        "services": [
            {"name": "Création de site web", "description": "Site vitrine professionnel responsive", "price": 490, "price_label": "À partir de 490€", "is_recommended": True},
            {"name": "Refonte de site web", "description": "Modernisation de votre site existant", "price": 390, "price_label": "À partir de 390€"},
            {"name": "Site e-commerce", "description": "Boutique en ligne complète", "price": 990, "price_label": "À partir de 990€"},
        ]
    },
    {
        "name": "SEO",
        "icon": "Search",
        "description": "Optimisation pour les moteurs de recherche",
        "services": [
            {"name": "Optimisation SEO", "description": "Amélioration du référencement naturel", "price": 300, "price_label": "À partir de 300€/mois", "is_recommended": True},
            {"name": "Audit SEO", "description": "Analyse complète de votre site", "price": 150, "price_label": "À partir de 150€"},
            {"name": "Google Business", "description": "Optimisation Google My Business", "price": 100, "price_label": "À partir de 100€"},
        ]
    },
    {
        "name": "Marketing Digital",
        "icon": "TrendingUp",
        "description": "Publicité et marketing en ligne",
        "services": [
            {"name": "Gestion Google Ads", "description": "Campagnes publicitaires Google", "price": 250, "price_label": "À partir de 250€/mois", "is_recommended": True},
            {"name": "Gestion Facebook Ads", "description": "Publicité sur Facebook et Instagram", "price": 200, "price_label": "À partir de 200€/mois"},
            {"name": "Email Marketing", "description": "Campagnes email professionnelles", "price": 150, "price_label": "À partir de 150€/mois"},
        ]
    },
    {
        "name": "Automatisation / IA",
        "icon": "Zap",
        "description": "Automatisation et intelligence artificielle",
        "services": [
            {"name": "Workflow automatisé", "description": "Automatisation de vos processus métier", "price": 500, "price_label": "À partir de 500€", "is_recommended": True},
            {"name": "Chatbot IA", "description": "Assistant virtuel intelligent", "price": 800, "price_label": "À partir de 800€"},
            {"name": "Analyse de données", "description": "Tableaux de bord et rapports automatiques", "price": 400, "price_label": "À partir de 400€"},
        ]
    },
    {
        "name": "CRM",
        "icon": "Users",
        "description": "Gestion de la relation client",
        "services": [
            {"name": "Configuration CRM", "description": "Mise en place et paramétrage", "price": 300, "price_label": "À partir de 300€", "is_recommended": True},
            {"name": "Formation CRM", "description": "Formation de vos équipes", "price": 200, "price_label": "À partir de 200€"},
            {"name": "Migration données", "description": "Import de vos données existantes", "price": 150, "price_label": "À partir de 150€"},
        ]
    },
    {
        "name": "Design",
        "icon": "Palette",
        "description": "Design graphique et identité visuelle",
        "services": [
            {"name": "Design landing page", "description": "Page d'atterrissage optimisée", "price": 250, "price_label": "À partir de 250€", "is_recommended": True},
            {"name": "Charte graphique", "description": "Identité visuelle complète", "price": 500, "price_label": "À partir de 500€"},
            {"name": "Cartes de visite", "description": "Design + impression 500 exemplaires", "price": 99, "price_label": "À partir de 99€"},
        ]
    },
]


class ServiceCategoryService:
    """Service for managing service categories and services"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def seed_default_data(self) -> bool:
        """Seed default categories and services if empty"""
        # Check if categories exist
        result = await self.db.execute(select(func.count(ServiceCategory.id)))
        count = result.scalar()
        
        if count > 0:
            logger.info(f"Categories already exist ({count}), skipping seed")
            return False
        
        logger.info("Seeding default service categories and services...")
        
        for i, cat_data in enumerate(DEFAULT_CATEGORIES):
            # Create category
            category = ServiceCategory(
                id=generate_uuid(),
                name=cat_data["name"],
                icon=cat_data.get("icon"),
                description=cat_data.get("description"),
                sort_order=i,
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(category)
            await self.db.flush()
            
            # Create services
            for j, svc_data in enumerate(cat_data.get("services", [])):
                service = Service(
                    id=generate_uuid(),
                    category_id=category.id,
                    name=svc_data["name"],
                    description=svc_data.get("description"),
                    price=svc_data.get("price"),
                    price_label=svc_data.get("price_label"),
                    is_recommended=svc_data.get("is_recommended", False),
                    sort_order=j,
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(service)
        
        await self.db.flush()
        logger.info(f"Seeded {len(DEFAULT_CATEGORIES)} categories with services")
        return True
    
    async def get_all_categories(self, include_services: bool = True) -> List[Dict]:
        """Get all active categories with their services"""
        query = select(ServiceCategory).where(
            ServiceCategory.is_active == True
        ).order_by(ServiceCategory.sort_order)
        
        if include_services:
            query = query.options(selectinload(ServiceCategory.services))
        
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        return [self._category_to_dict(cat, include_services) for cat in categories]
    
    async def get_category_by_id(self, category_id: str) -> Optional[Dict]:
        """Get a specific category with services"""
        query = select(ServiceCategory).where(
            ServiceCategory.id == category_id
        ).options(selectinload(ServiceCategory.services))
        
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()
        
        if category:
            return self._category_to_dict(category, True)
        return None
    
    async def get_services_by_category(self, category_id: str) -> List[Dict]:
        """Get all services for a category"""
        query = select(Service).where(
            and_(Service.category_id == category_id, Service.is_active == True)
        ).order_by(Service.sort_order)
        
        result = await self.db.execute(query)
        services = result.scalars().all()
        
        return [self._service_to_dict(svc) for svc in services]
    
    async def get_service_by_id(self, service_id: str) -> Optional[Dict]:
        """Get a specific service"""
        query = select(Service).where(Service.id == service_id)
        result = await self.db.execute(query)
        service = result.scalar_one_or_none()
        
        if service:
            return self._service_to_dict(service)
        return None
    
    def _category_to_dict(self, category: ServiceCategory, include_services: bool = False) -> Dict:
        """Convert category to dict"""
        data = {
            "id": category.id,
            "name": category.name,
            "icon": category.icon,
            "description": category.description,
            "sort_order": category.sort_order,
            "is_active": category.is_active,
            "created_at": category.created_at.isoformat() if category.created_at else None,
        }
        
        if include_services and category.services:
            data["services"] = [
                self._service_to_dict(svc) 
                for svc in sorted(category.services, key=lambda x: x.sort_order)
                if svc.is_active
            ]
        
        return data
    
    def _service_to_dict(self, service: Service) -> Dict:
        """Convert service to dict"""
        return {
            "id": service.id,
            "category_id": service.category_id,
            "name": service.name,
            "description": service.description,
            "price": service.price,
            "price_label": service.price_label,
            "is_recommended": service.is_recommended,
            "sort_order": service.sort_order,
            "is_active": service.is_active,
            "created_at": service.created_at.isoformat() if service.created_at else None,
        }


class ServiceRequestService:
    """Service for managing service requests"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_request(
        self,
        user_id: str,
        category_id: str,
        service_id: str,
        company_name: str,
        contact_email: str,
        phone: str,
        message: Optional[str] = None,
        quantity: int = 1,
        urgency: str = "standard",
        logo_base64: Optional[str] = None
    ) -> Dict:
        """Create a new service request"""
        request = ServiceRequest(
            id=generate_uuid(),
            user_id=user_id,
            category_id=category_id,
            service_id=service_id,
            company_name=company_name,
            contact_email=contact_email,
            phone=phone,
            message=message,
            quantity=quantity,
            urgency=urgency,
            logo_base64=logo_base64,
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(request)
        await self.db.flush()
        
        logger.info(f"Service request created: {request.id}")
        return await self.get_request_by_id(request.id)
    
    async def get_request_by_id(self, request_id: str) -> Optional[Dict]:
        """Get a service request by ID"""
        query = select(ServiceRequest).where(
            ServiceRequest.id == request_id
        ).options(selectinload(ServiceRequest.service))
        
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()
        
        if request:
            return self._request_to_dict(request)
        return None
    
    async def get_user_requests(self, user_id: str) -> List[Dict]:
        """Get all requests for a user"""
        query = select(ServiceRequest).where(
            ServiceRequest.user_id == user_id
        ).options(
            selectinload(ServiceRequest.service)
        ).order_by(ServiceRequest.created_at.desc())
        
        result = await self.db.execute(query)
        requests = result.scalars().all()
        
        return [self._request_to_dict(req) for req in requests]
    
    async def get_all_requests(
        self,
        status_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get all service requests (admin)"""
        query = select(ServiceRequest).options(
            selectinload(ServiceRequest.service)
        )
        
        filters = []
        if status_filter:
            filters.append(ServiceRequest.status == status_filter)
        if category_filter:
            filters.append(ServiceRequest.category_id == category_filter)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(ServiceRequest.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        requests = result.scalars().all()
        
        return [self._request_to_dict(req) for req in requests]
    
    async def update_request_status(
        self,
        request_id: str,
        status: str,
        admin_notes: Optional[str] = None
    ) -> Optional[Dict]:
        """Update request status"""
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            return None
        
        query = select(ServiceRequest).where(ServiceRequest.id == request_id)
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()
        
        if not request:
            return None
        
        request.status = status
        request.updated_at = datetime.now(timezone.utc)
        if admin_notes is not None:
            request.admin_notes = admin_notes
        
        await self.db.flush()
        logger.info(f"Service request {request_id} status updated to {status}")
        
        return await self.get_request_by_id(request_id)
    
    async def get_stats(self) -> Dict[str, int]:
        """Get request statistics"""
        stats = {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
        
        for status in ["pending", "in_progress", "completed", "cancelled"]:
            query = select(func.count(ServiceRequest.id)).where(
                ServiceRequest.status == status
            )
            result = await self.db.execute(query)
            count = result.scalar() or 0
            stats[status] = count
            stats["total"] += count
        
        return stats
    
    def _request_to_dict(self, request: ServiceRequest) -> Dict:
        """Convert request to dict"""
        data = {
            "id": request.id,
            "user_id": request.user_id,
            "category_id": request.category_id,
            "service_id": request.service_id,
            "company_name": request.company_name,
            "contact_email": request.contact_email,
            "phone": request.phone,
            "message": request.message,
            "quantity": request.quantity,
            "urgency": request.urgency,
            "status": request.status,
            "admin_notes": request.admin_notes,
            "has_logo": bool(request.logo_base64),
            "created_at": request.created_at.isoformat() if request.created_at else None,
            "updated_at": request.updated_at.isoformat() if request.updated_at else None,
        }
        
        # Include service info
        if request.service:
            data["service_name"] = request.service.name
            data["service_price"] = request.service.price
        
        return data


def get_service_category_service(db: AsyncSession) -> ServiceCategoryService:
    """Factory function"""
    return ServiceCategoryService(db)


def get_service_request_pg_service(db: AsyncSession) -> ServiceRequestService:
    """Factory function"""
    return ServiceRequestService(db)
