"""
API Routes Module
All API route handlers
"""
from app.api.routes import (
    project_routes,
    work_item_routes,
    financial_routes,
    signature_routes,
    portal_routes,
    ai_routes,
    accounting_routes,
    recurring_routes,
    reminder_routes,
    notification_routes
)

__all__ = [
    "project_routes",
    "work_item_routes",
    "financial_routes",
    "signature_routes",
    "portal_routes",
    "ai_routes",
    "accounting_routes",
    "recurring_routes",
    "reminder_routes",
    "notification_routes"
]
