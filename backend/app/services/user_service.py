"""
User Service - CRUD operations for users
PostgreSQL/Supabase implementation
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import User, UserSettings
from app.schemas.schemas import UserCreate, UserUpdate, UserResponse, UserSettingsUpdate
from app.core.security import hash_password, verify_password, generate_uuid, ROLE_USER, ROLE_SUPER_ADMIN

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user_data: UserCreate, role: str = ROLE_USER) -> User:
        """Create a new user with settings"""
        user_id = generate_uuid()
        
        user = User(
            id=user_id,
            email=user_data.email.lower(),
            password=hash_password(user_data.password),
            name=user_data.name,
            phone=user_data.phone,
            role=role,
            is_active=False,  # Activated after email verification
            email_verified=False,
            subscription_plan="trial_pending",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(user)
        
        # Create default settings
        settings = UserSettings(
            id=generate_uuid(),
            user_id=user_id,
            default_payment_days=30,
            vat_rates=[20.0, 10.0, 5.5, 2.1],
            retention_enabled=False,
            default_retention_rate=5.0,
            quote_validity_days=30,
            quote_prefix="DEV",
            invoice_prefix="FAC",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(settings)
        await self.db.flush()
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def get_user_with_settings(self, user_id: str) -> Optional[User]:
        """Get user with settings loaded"""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.settings))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        for key, value in update_data.items():
            setattr(user, key, value)
        
        await self.db.flush()
        return user
    
    async def update_user_settings(self, user_id: str, settings_data: UserSettingsUpdate) -> Optional[UserSettings]:
        """Update user settings"""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            # Create settings if not exists
            settings = UserSettings(
                id=generate_uuid(),
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            self.db.add(settings)
        
        update_data = settings_data.model_dump(exclude_unset=True)
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        for key, value in update_data.items():
            setattr(settings, key, value)
        
        await self.db.flush()
        return settings
    
    async def get_user_settings(self, user_id: str) -> Optional[UserSettings]:
        """Get user settings"""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def verify_user_email(self, user_id: str) -> bool:
        """Mark user email as verified and activate trial"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=14)
        
        user.email_verified = True
        user.is_active = True
        user.subscription_plan = "trial_active"
        user.updated_at = now
        
        await self.db.flush()
        return True
    
    async def update_last_login(self, user_id: str):
        """Update last login timestamp"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                last_login=datetime.now(timezone.utc),
                login_attempts=0,
                locked_until=None
            )
        )
    
    async def increment_login_attempts(self, user_id: str) -> int:
        """Increment failed login attempts and lock if needed"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return 0
        
        attempts = (user.login_attempts or 0) + 1
        update_values = {'login_attempts': attempts}
        
        if attempts >= 5:
            lock_time = datetime.now(timezone.utc) + timedelta(minutes=30)
            update_values['locked_until'] = lock_time
        
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_values)
        )
        
        return attempts
    
    async def is_account_locked(self, user_id: str) -> bool:
        """Check if account is locked"""
        user = await self.get_user_by_id(user_id)
        if not user or not user.locked_until:
            return False
        
        return user.locked_until > datetime.now(timezone.utc)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user and all related data"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        await self.db.delete(user)
        return True
    
    async def list_users(
        self, 
        skip: int = 0, 
        limit: int = 50,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """List users with optional filtering"""
        query = select(User)
        
        conditions = []
        if role:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count_users(self, role: Optional[str] = None, is_active: Optional[bool] = None) -> int:
        """Count users with optional filtering"""
        query = select(func.count(User.id))
        
        conditions = []
        if role:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        user = await self.get_user_by_email(email)
        
        if not user:
            return None
        
        if not verify_password(password, user.password):
            await self.increment_login_attempts(user.id)
            return None
        
        return user
    
    async def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user password"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                password=hash_password(new_password),
                updated_at=datetime.now(timezone.utc)
            )
        )
        return True
    
    async def create_super_admin(self, email: str, password: str, name: str) -> Optional[User]:
        """Create super admin if not exists"""
        existing = await self.get_user_by_email(email)
        if existing:
            # Update to super admin if exists
            existing.role = ROLE_SUPER_ADMIN
            existing.is_active = True
            existing.email_verified = True
            await self.db.flush()
            return existing
        
        user_id = generate_uuid()
        user = User(
            id=user_id,
            email=email.lower(),
            password=hash_password(password),
            name=name,
            role=ROLE_SUPER_ADMIN,
            is_active=True,
            email_verified=True,
            subscription_plan="enterprise",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(user)
        
        # Create settings for admin
        settings = UserSettings(
            id=generate_uuid(),
            user_id=user_id,
            company_name="BTP Facture Admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.db.add(settings)
        
        await self.db.flush()
        return user


def get_user_service(db: AsyncSession) -> UserService:
    """Factory function for dependency injection"""
    return UserService(db)
