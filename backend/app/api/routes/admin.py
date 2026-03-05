"""
Admin Dashboard Routes
Analytics and metrics for admin users
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.core.database import get_db
from app.services.admin_dashboard_service import get_admin_dashboard_service
from app.api.deps import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete admin dashboard with all metrics.
    Requires admin or super_admin role.
    """
    service = get_admin_dashboard_service(db)
    return await service.get_admin_dashboard_summary()


@router.get("/users/statistics")
async def get_user_statistics(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user statistics.
    - Total users
    - Active/inactive users
    - Users by subscription plan
    - Users by role
    """
    service = get_admin_dashboard_service(db)
    return await service.get_user_statistics()


@router.get("/profile-completion")
async def get_profile_completion_stats(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get profile completion statistics.
    - Average completion rate
    - Completion distribution
    - Category averages
    - Missing fields summary
    """
    service = get_admin_dashboard_service(db)
    return await service.get_profile_completion_stats()


@router.get("/users/missing-info/{info_type}")
async def get_users_missing_info(
    info_type: str = "all",
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of users missing specific information.
    
    Args:
        info_type: Type of missing info to check
            - 'company': Missing company info
            - 'legal': Missing legal info (SIRET, VAT)
            - 'banking': Missing banking info (IBAN, BIC)
            - 'all': All missing info
    """
    valid_types = ['all', 'company', 'legal', 'banking']
    if info_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type invalide. Valeurs autorisées: {valid_types}"
        )
    
    service = get_admin_dashboard_service(db)
    return await service.get_users_missing_info(info_type)


@router.get("/business-metrics")
async def get_business_metrics(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get business metrics.
    - Total invoices and amounts
    - Total quotes
    - Total clients
    - Total projects
    """
    service = get_admin_dashboard_service(db)
    return await service.get_business_metrics()
