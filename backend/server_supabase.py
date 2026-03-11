"""
FactureBTP - Clean Supabase Backend
Production-ready FastAPI server using Supabase for auth and database
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FactureBTP API",
    description="API de gestion de devis et factures pour le BTP",
    version="2.0.0",
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include Supabase routes
from app.api.routes.supabase_routes import router as supabase_router
app.include_router(supabase_router, prefix="/api")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "database": "supabase"}

@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "version": "2.0.0", "database": "supabase"}

# Root redirect
@app.get("/")
async def root():
    return {"message": "FactureBTP API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
