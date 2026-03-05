"""
User Settings Service
Handles user company settings and logo management
"""
import os
import base64
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import logging

from app.core.config import settings
from app.core.database import db, is_mongodb, is_postgresql

logger = logging.getLogger(__name__)

class UserSettingsService:
    """Service for managing user settings"""
    
    @staticmethod
    async def get_settings(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user settings by user_id"""
        if is_mongodb():
            return await db.user_settings.find_one(
                {"user_id": user_id},
                {"_id": 0}
            )
        return None
    
    @staticmethod
    async def create_default_settings(user_id: str) -> Dict[str, Any]:
        """Create default settings for a new user"""
        default_settings = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "company_name": "",
            "company_address": "",
            "company_email": "",
            "company_phone": "",
            "company_website": "",
            "siret": "",
            "vat_number": "",
            "rcs": "",
            "capital": "",
            "legal_form": "",
            "iban": "",
            "bic": "",
            "bank_name": "",
            "logo_url": None,
            "logo_base64": None,
            "default_payment_days": 30,
            "vat_rates": [20.0, 10.0, 5.5, 2.1],
            "retention_enabled": False,
            "default_retention_rate": 5.0,
            "quote_validity_days": 30,
            "quote_prefix": "DEV",
            "invoice_prefix": "FAC",
            "invoice_notes": "",
            "invoice_footer": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if is_mongodb():
            await db.user_settings.insert_one(default_settings.copy())
        
        return default_settings
    
    @staticmethod
    async def update_settings(user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user settings"""
        # Get existing settings or create new
        existing = await UserSettingsService.get_settings(user_id)
        if not existing:
            existing = await UserSettingsService.create_default_settings(user_id)
        
        # Update fields
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        if is_mongodb():
            await db.user_settings.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            return await UserSettingsService.get_settings(user_id)
        
        return None
    
    @staticmethod
    async def upload_logo(user_id: str, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Upload and save company logo"""
        # Validate file type
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        ext = Path(filename).suffix.lower()
        if ext not in allowed_extensions:
            raise ValueError(f"Type de fichier non autorisé: {ext}")
        
        # Generate unique filename
        logo_filename = f"{user_id}{ext}"
        logo_path = settings.LOGOS_PATH / logo_filename
        
        # Save file
        with open(logo_path, 'wb') as f:
            f.write(file_data)
        
        # Convert to base64 for database storage
        logo_base64 = base64.b64encode(file_data).decode('utf-8')
        
        # Determine MIME type
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/png')
        
        # Store with data URI prefix
        logo_data_uri = f"data:{mime_type};base64,{logo_base64}"
        
        # Update settings
        logo_url = f"/storage/logos/{logo_filename}"
        
        if is_mongodb():
            await db.user_settings.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "logo_url": logo_url,
                        "logo_base64": logo_data_uri,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )
        
        return {
            "logo_url": logo_url,
            "logo_base64": logo_data_uri,
            "message": "Logo téléchargé avec succès"
        }
    
    @staticmethod
    async def delete_logo(user_id: str) -> bool:
        """Delete user's company logo"""
        # Get current settings
        settings_data = await UserSettingsService.get_settings(user_id)
        if not settings_data or not settings_data.get("logo_url"):
            return False
        
        # Delete file if exists
        logo_url = settings_data.get("logo_url")
        if logo_url:
            logo_path = settings.STORAGE_PATH / logo_url.lstrip('/')
            if logo_path.exists():
                logo_path.unlink()
        
        # Update settings
        if is_mongodb():
            await db.user_settings.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "logo_url": None,
                        "logo_base64": None,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        
        return True
    
    @staticmethod
    async def get_profile_completion(user_id: str) -> Dict[str, Any]:
        """Calculate profile completion percentage"""
        user = None
        user_settings = None
        
        if is_mongodb():
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            user_settings = await db.user_settings.find_one({"user_id": user_id}, {"_id": 0})
        
        if not user:
            return {"completion_percentage": 0, "items": []}
        
        completion_items = []
        
        # Profile checks
        completion_items.append({
            "key": "name",
            "label": "Nom complet",
            "completed": bool(user.get("name") and len(user.get("name", "")) > 2),
            "category": "profil"
        })
        completion_items.append({
            "key": "phone",
            "label": "Téléphone",
            "completed": bool(user.get("phone")),
            "category": "profil"
        })
        completion_items.append({
            "key": "email_verified",
            "label": "Email vérifié",
            "completed": user.get("email_verified", False),
            "category": "profil"
        })
        
        # Company checks
        if user_settings:
            completion_items.extend([
                {"key": "company_name", "label": "Nom entreprise", 
                 "completed": bool(user_settings.get("company_name")), "category": "entreprise"},
                {"key": "address", "label": "Adresse", 
                 "completed": bool(user_settings.get("company_address")), "category": "entreprise"},
                {"key": "siret", "label": "SIRET", 
                 "completed": bool(user_settings.get("siret") and len(user_settings.get("siret", "")) == 14), "category": "legal"},
                {"key": "vat_number", "label": "N° TVA", 
                 "completed": bool(user_settings.get("vat_number")), "category": "legal"},
                {"key": "iban", "label": "IBAN", 
                 "completed": bool(user_settings.get("iban") and len(user_settings.get("iban", "")) >= 15), "category": "bancaire"},
                {"key": "bic", "label": "BIC", 
                 "completed": bool(user_settings.get("bic")), "category": "bancaire"},
                {"key": "logo", "label": "Logo", 
                 "completed": bool(user_settings.get("logo_base64")), "category": "entreprise"},
                {"key": "website", "label": "Site web", 
                 "completed": bool(user_settings.get("company_website")), "category": "entreprise"},
            ])
        else:
            # No settings yet
            for item in ["company_name", "address", "siret", "vat_number", "iban", "bic", "logo", "website"]:
                completion_items.append({
                    "key": item,
                    "label": item.replace("_", " ").title(),
                    "completed": False,
                    "category": "entreprise" if item in ["company_name", "address", "logo", "website"] 
                               else "legal" if item in ["siret", "vat_number"]
                               else "bancaire"
                })
        
        # Calculate
        completed_count = sum(1 for item in completion_items if item["completed"])
        total_count = len(completion_items)
        completion_percentage = int((completed_count / total_count) * 100) if total_count > 0 else 0
        
        # Summary by category
        summary = {}
        for category in ["profil", "entreprise", "legal", "bancaire"]:
            cat_items = [i for i in completion_items if i["category"] == category]
            summary[category] = sum(1 for i in cat_items if i["completed"])
            summary[f"{category}_total"] = len(cat_items)
        
        return {
            "user_id": user_id,
            "user_name": user.get("name"),
            "user_email": user.get("email"),
            "completion_percentage": completion_percentage,
            "completed_count": completed_count,
            "total_count": total_count,
            "items": completion_items,
            "summary": summary
        }


# Create singleton instance
user_settings_service = UserSettingsService()
