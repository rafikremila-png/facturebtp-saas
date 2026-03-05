"""
Application Configuration
Central configuration management for BTP Facture SaaS
"""
import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

class Settings:
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "BTP Facture"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database - Supabase PostgreSQL
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Legacy MongoDB (for migration)
    MONGO_URL: Optional[str] = os.getenv("MONGO_URL")
    DB_NAME: str = os.getenv("DB_NAME", "btp_facture")
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-this-secret-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    
    # Email (SMTP)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@btpfacture.com")
    
    # Stripe
    STRIPE_API_KEY: Optional[str] = os.getenv("STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ESSENTIEL_MONTHLY: Optional[str] = os.getenv("STRIPE_PRICE_ESSENTIEL_MONTHLY")
    STRIPE_PRICE_ESSENTIEL_YEARLY: Optional[str] = os.getenv("STRIPE_PRICE_ESSENTIEL_YEARLY")
    STRIPE_PRICE_PRO_MONTHLY: Optional[str] = os.getenv("STRIPE_PRICE_PRO_MONTHLY")
    STRIPE_PRICE_PRO_YEARLY: Optional[str] = os.getenv("STRIPE_PRICE_PRO_YEARLY")
    STRIPE_PRICE_BUSINESS_MONTHLY: Optional[str] = os.getenv("STRIPE_PRICE_BUSINESS_MONTHLY")
    STRIPE_PRICE_BUSINESS_YEARLY: Optional[str] = os.getenv("STRIPE_PRICE_BUSINESS_YEARLY")
    
    # AI Integration
    EMERGENT_LLM_KEY: Optional[str] = os.getenv("EMERGENT_LLM_KEY")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.5-flash")
    
    # Admin
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@btpfacture.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin123!")
    ADMIN_NAME: str = os.getenv("ADMIN_NAME", "Super Admin")
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Storage paths
    STORAGE_PATH: Path = Path(__file__).parent.parent.parent / "storage"
    LOGOS_PATH: Path = STORAGE_PATH / "logos"
    PDFS_PATH: Path = STORAGE_PATH / "pdfs"
    SIGNATURES_PATH: Path = STORAGE_PATH / "signatures"
    
    # BTP Specific
    DEFAULT_VAT_RATES: List[float] = [20.0, 10.0, 5.5, 2.1]
    DEFAULT_PAYMENT_DAYS: int = 30
    DEFAULT_RETENTION_RATE: float = 5.0
    
    def __init__(self):
        # Ensure storage directories exist
        self.LOGOS_PATH.mkdir(parents=True, exist_ok=True)
        self.PDFS_PATH.mkdir(parents=True, exist_ok=True)
        self.SIGNATURES_PATH.mkdir(parents=True, exist_ok=True)

# Create global settings instance
settings = Settings()
