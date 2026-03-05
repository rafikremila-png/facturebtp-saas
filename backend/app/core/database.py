"""
Database Configuration
Supports both Supabase/PostgreSQL and legacy MongoDB
"""
import os
from pathlib import Path
from typing import Optional, AsyncGenerator
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment
load_dotenv(Path(__file__).parent.parent.parent / '.env')

DATABASE_URL = os.getenv("DATABASE_URL")
MONGO_URL = os.getenv("MONGO_URL")

# ============== SUPABASE/POSTGRESQL ==============

if DATABASE_URL:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import declarative_base
    from sqlalchemy.pool import NullPool
    
    # Convert to async URL
    ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        pool_size=10,
        max_overflow=5,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=False,
        echo=False,
        connect_args={
            "statement_cache_size": 0,  # Required for transaction pooler
            "command_timeout": 30,
        }
    )
    
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    Base = declarative_base()
    
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        """Get database session for dependency injection"""
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    
    async def init_db():
        """Initialize database tables"""
        async with engine.begin() as conn:
            # Import models to register them
            from app.models import models
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL database initialized")
    
    DB_TYPE = "postgresql"
    logger.info("Using Supabase/PostgreSQL database")

else:
    # Fallback to MongoDB
    Base = None
    AsyncSessionLocal = None
    engine = None
    
    async def get_db():
        """Get MongoDB database"""
        return db
    
    async def init_db():
        """Initialize MongoDB"""
        logger.info("MongoDB database ready")
    
    DB_TYPE = "mongodb"
    logger.info("Using MongoDB database")

# ============== MONGODB (Legacy/Fallback) ==============

from motor.motor_asyncio import AsyncIOMotorClient

mongo_client: Optional[AsyncIOMotorClient] = None
db = None

async def init_mongodb():
    """Initialize MongoDB connection"""
    global mongo_client, db
    if MONGO_URL:
        mongo_client = AsyncIOMotorClient(MONGO_URL)
        db_name = os.getenv("DB_NAME", "btp_facture")
        db = mongo_client[db_name]
        logger.info(f"MongoDB connected to database: {db_name}")
        return db
    return None

async def close_mongodb():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")

# ============== DATABASE HELPERS ==============

def get_db_type() -> str:
    """Get current database type"""
    return DB_TYPE

def is_postgresql() -> bool:
    """Check if using PostgreSQL"""
    return DB_TYPE == "postgresql"

def is_mongodb() -> bool:
    """Check if using MongoDB"""
    return DB_TYPE == "mongodb"
