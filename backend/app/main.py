"""
BTP Facture API - Main Application
FastAPI application with PostgreSQL/Supabase backend

This is the new modular entry point replacing the monolithic server.py
"""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=True)

from app.core.database import get_db_context, check_db_connection
from app.core.config import settings
from app.services.user_service import get_user_service

# Import API routes
from app.api.routes import auth, clients, projects, quotes, invoices

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    logger.info("Starting BTP Facture API...")
    
    # Check database connection
    db_ok = await check_db_connection()
    if db_ok:
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed")
    
    # Initialize super admin
    try:
        async with get_db_context() as db:
            user_service = get_user_service(db)
            await user_service.create_super_admin(
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                name=settings.ADMIN_NAME
            )
            logger.info(f"✅ Super admin ready: {settings.ADMIN_EMAIL}")
    except Exception as e:
        logger.error(f"Failed to initialize super admin: {e}")
    
    yield
    
    logger.info("Shutting down BTP Facture API...")


# Create FastAPI application
app = FastAPI(
    title="BTP Facture API",
    description="API pour la gestion de devis et factures BTP",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne s'est produite"}
    )


# Root endpoint
@app.get("/")
def root():
    return {
        "service": "BTP Facture API",
        "status": "running",
        "version": "2.0.0",
        "documentation": "/docs",
        "health": "/api/health",
        "database": "postgresql"
    }


# Health check
@app.get("/api/health")
async def health_check():
    db_ok = await check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "version": "2.0.0"
    }


# Include API routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(quotes.router, prefix="/api")
app.include_router(invoices.router, prefix="/api")


# Legacy compatibility routes - redirect to new endpoints
# These can be removed once frontend is updated

@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Placeholder for dashboard stats - to be implemented"""
    return {
        "total_turnover": 0,
        "unpaid_invoices_count": 0,
        "unpaid_invoices_amount": 0,
        "pending_quotes_count": 0,
        "total_clients": 0,
        "total_quotes": 0,
        "total_invoices": 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
