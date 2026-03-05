"""
API Routes Module
All API route handlers for BTP Facture
"""
# New modular routes - these are the active ones
from app.api.routes import (
    auth,
    clients,
    projects,
    quotes,
    invoices,
    admin,
    work_items,
    financial
)

__all__ = [
    "auth",
    "clients",
    "projects", 
    "quotes",
    "invoices",
    "admin",
    "work_items",
    "financial"
]
