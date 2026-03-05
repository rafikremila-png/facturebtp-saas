"""
Database Configuration for PostgreSQL/Supabase
Async SQLAlchemy with connection pooling optimized for Supabase Transaction Pooler
"""
import os
import logging
from pathlib import Path
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# Load environment
load_dotenv(Path(__file__).parent.parent.parent / '.env')

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in environment")

# Convert to async URL for asyncpg
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# Create async engine optimized for Supabase Transaction Pooler
# NullPool is required for transaction pooler (no persistent connections)
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    poolclass=NullPool,  # Required for Supabase Transaction Pooler
    echo=False,
    connect_args={
        "statement_cache_size": 0,  # Required for transaction pooler
        "prepared_statement_cache_size": 0,
    }
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions.
    Use with FastAPI's Depends():
    
    @app.get("/items")
    async def get_items(db: AsyncSession = Depends(get_db)):
        ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """
    Context manager for database sessions.
    Use in non-FastAPI contexts:
    
    async with get_db_context() as db:
        ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - create tables if needed"""
    from app.models.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")


async def check_db_connection() -> bool:
    """Check if database connection is working"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


# Export for convenience
__all__ = [
    "engine",
    "AsyncSessionLocal", 
    "get_db",
    "get_db_context",
    "init_db",
    "check_db_connection"
]
