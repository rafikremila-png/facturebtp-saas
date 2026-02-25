"""
Application Initialization for BTP Facture
Integrates new modular services with existing server.py
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

from .services.otp_service import get_otp_service
from .routes.auth_routes import set_database as set_auth_db

logger = logging.getLogger(__name__)


async def init_app_services(db: AsyncIOMotorDatabase) -> None:
    """
    Initialize all application services with database.
    Call this on application startup.
    
    Args:
        db: MongoDB database instance
    """
    # Set database for auth routes
    set_auth_db(db)
    
    # Initialize OTP service indexes
    otp_service = get_otp_service(db)
    await otp_service.init_indexes()
    
    logger.info("Application services initialized successfully")


async def create_user_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Create necessary indexes for users collection.
    
    Args:
        db: MongoDB database instance
    """
    try:
        # Unique email index
        await db.users.create_index("email", unique=True, name="idx_email_unique")
        
        # Index for role-based queries
        await db.users.create_index("role", name="idx_role")
        
        # Index for active users
        await db.users.create_index("is_active", name="idx_active")
        
        # Index for verification status
        await db.users.create_index("is_verified", name="idx_verified")
        
        # Compound index for trial management
        await db.users.create_index(
            [("plan", 1), ("trial_end", 1)],
            name="idx_plan_trial"
        )
        
        logger.info("User indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")
