"""
User Sync Utility
Ensures MongoDB users exist in PostgreSQL for hybrid operation
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient
import os

from app.models.models import User
from app.core.security import generate_uuid

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'btp_invoice')


async def ensure_user_in_postgres(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Ensure a MongoDB user exists in PostgreSQL.
    If not, copy basic info from MongoDB to PostgreSQL.
    """
    # First check if user exists in PostgreSQL
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    pg_user = result.scalar_one_or_none()
    
    if pg_user:
        return pg_user
    
    # User not in PostgreSQL, fetch from MongoDB
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        mongo_db = client[DB_NAME]
        
        mongo_user = await mongo_db.users.find_one({"id": user_id})
        
        if not mongo_user:
            logger.warning(f"User {user_id} not found in MongoDB")
            client.close()
            return None
        
        # Create user in PostgreSQL
        pg_user = User(
            id=mongo_user.get("id"),
            email=mongo_user.get("email"),
            password=mongo_user.get("password", ""),  # Keep hash from MongoDB
            name=mongo_user.get("name", ""),
            phone=mongo_user.get("phone"),
            role=mongo_user.get("role", "user"),
            is_active=mongo_user.get("is_active", True),
            email_verified=mongo_user.get("email_verified", False),
            subscription_plan=mongo_user.get("subscription_plan", "free"),
            subscription_status=mongo_user.get("subscription_status", "active"),
            stripe_customer_id=mongo_user.get("stripe_customer_id"),
            stripe_subscription_id=mongo_user.get("stripe_subscription_id"),
            created_at=mongo_user.get("created_at", datetime.now(timezone.utc)) if isinstance(mongo_user.get("created_at"), datetime) else datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(pg_user)
        await db.flush()
        
        logger.info(f"Synced user {user_id} from MongoDB to PostgreSQL")
        
        client.close()
        return pg_user
        
    except Exception as e:
        logger.error(f"Error syncing user {user_id}: {e}")
        return None


async def sync_all_users(db: AsyncSession) -> int:
    """
    Sync all MongoDB users to PostgreSQL.
    Returns count of users synced.
    """
    synced_count = 0
    
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        mongo_db = client[DB_NAME]
        
        async for mongo_user in mongo_db.users.find({}):
            user_id = mongo_user.get("id")
            
            # Check if already exists
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                pg_user = User(
                    id=user_id,
                    email=mongo_user.get("email"),
                    password=mongo_user.get("password", ""),
                    name=mongo_user.get("name", ""),
                    phone=mongo_user.get("phone"),
                    role=mongo_user.get("role", "user"),
                    is_active=mongo_user.get("is_active", True),
                    email_verified=mongo_user.get("email_verified", False),
                    subscription_plan=mongo_user.get("subscription_plan", "free"),
                    subscription_status=mongo_user.get("subscription_status", "active"),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                db.add(pg_user)
                synced_count += 1
        
        await db.commit()
        client.close()
        
        logger.info(f"Synced {synced_count} users from MongoDB to PostgreSQL")
        
    except Exception as e:
        logger.error(f"Error syncing users: {e}")
        await db.rollback()
    
    return synced_count
