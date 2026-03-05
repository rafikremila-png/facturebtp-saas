"""
Advanced Features Service for BTP Facture SaaS
Handles electronic signatures, PDF analysis, image analysis, and marketing automation
"""

import os
import re
import io
import base64
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pdfplumber
from PIL import Image

logger = logging.getLogger(__name__)


class ElectronicSignatureService:
    """Handle electronic signatures for quotes"""
    
    def __init__(self, db):
        self.db = db
        self.signatures = db.signatures
    
    async def create_signature_request(
        self,
        quote_id: str,
        client_email: str,
        client_name: str,
        owner_id: str
    ) -> Dict[str, Any]:
        """Create a signature request for a quote"""
        import uuid
        
        signature_token = str(uuid.uuid4())
        
        signature_doc = {
            "id": str(uuid.uuid4()),
            "quote_id": quote_id,
            "client_email": client_email,
            "client_name": client_name,
            "owner_id": owner_id,
            "signature_token": signature_token,
            "status": "pending",  # pending, signed, expired
            "signature_data": None,
            "signed_at": None,
            "ip_address": None,
            "user_agent": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc).replace(day=datetime.now().day + 30)).isoformat(),
        }
        
        await self.signatures.insert_one(signature_doc)
        
        return {
            "signature_id": signature_doc["id"],
            "signature_token": signature_token,
            "signature_url": f"/signer/{signature_token}",
            "expires_at": signature_doc["expires_at"],
        }
    
    async def sign_quote(
        self,
        signature_token: str,
        signature_data: str,  # Base64 image data
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Sign a quote with electronic signature"""
        
        # Find signature request
        signature = await self.signatures.find_one({"signature_token": signature_token})
        
        if not signature:
            raise ValueError("Lien de signature invalide ou expiré")
        
        if signature["status"] == "signed":
            raise ValueError("Ce document a déjà été signé")
        
        # Update signature
        now = datetime.now(timezone.utc).isoformat()
        
        await self.signatures.update_one(
            {"signature_token": signature_token},
            {
                "$set": {
                    "status": "signed",
                    "signature_data": signature_data,
                    "signed_at": now,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                }
            }
        )
        
        # Update quote status to accepted
        await self.db.quotes.update_one(
            {"id": signature["quote_id"]},
            {
                "$set": {
                    "status": "accepted",
                    "signature_id": signature["id"],
                    "signed_at": now,
                    "updated_at": now,
                }
            }
        )
        
        logger.info(f"Quote {signature['quote_id']} signed electronically")
        
        return {
            "success": True,
            "signed_at": now,
            "quote_id": signature["quote_id"],
        }
    
    async def get_signature_status(self, signature_token: str) -> Dict[str, Any]:
        """Get signature status"""
        signature = await self.signatures.find_one(
            {"signature_token": signature_token},
            {"_id": 0, "signature_data": 0}
        )
        
        if not signature:
            return {"valid": False, "error": "Signature non trouvée"}
        
        return {
            "valid": True,
            "status": signature["status"],
            "client_name": signature["client_name"],
            "signed_at": signature.get("signed_at"),
        }


class PDFAnalysisService:
    """Analyze construction plan PDFs"""
    
    def __init__(self):
        self.room_patterns = {
            "cuisine": ["cuisine", "kitchen", "cuis."],
            "salon": ["salon", "séjour", "living", "salle de séjour"],
            "chambre": ["chambre", "bedroom", "ch.", "chb"],
            "salle_de_bain": ["salle de bain", "sdb", "bathroom", "douche"],
            "wc": ["wc", "toilette", "toilet", "w.c."],
            "bureau": ["bureau", "office", "bur."],
            "entree": ["entrée", "hall", "entry"],
            "garage": ["garage", "gar."],
            "terrasse": ["terrasse", "balcon", "terrace"],
            "cave": ["cave", "cellier", "basement"],
        }
        
        # Regex patterns for surface detection
        self.surface_patterns = [
            r"(\d+[,.]?\d*)\s*m[²2]",
            r"(\d+[,.]?\d*)\s*m\s*2",
            r"surface\s*[:=]\s*(\d+[,.]?\d*)",
            r"(\d+[,.]?\d*)\s*mètres?\s*carrés?",
        ]
    
    def analyze_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Analyze a PDF file and extract room/surface information"""
        
        try:
            pdf_file = io.BytesIO(pdf_content)
            
            with pdfplumber.open(pdf_file) as pdf:
                all_text = ""
                tables = []
                
                for page in pdf.pages:
                    # Extract text
                    text = page.extract_text() or ""
                    all_text += text + "\n"
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                
                # Analyze text
                rooms = self._detect_rooms(all_text)
                surfaces = self._extract_surfaces(all_text)
                total_surface = self._calculate_total_surface(surfaces)
                
                return {
                    "success": True,
                    "pages": len(pdf.pages),
                    "rooms_detected": rooms,
                    "surfaces_detected": surfaces,
                    "total_surface_estimated": total_surface,
                    "tables_found": len(tables),
                    "raw_text_length": len(all_text),
                    "suggested_works": self._suggest_works(rooms),
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                }
                
        except Exception as e:
            logger.error(f"PDF analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def _detect_rooms(self, text: str) -> List[Dict[str, Any]]:
        """Detect rooms mentioned in the text"""
        text_lower = text.lower()
        detected = []
        
        for room_type, patterns in self.room_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    # Try to find associated surface
                    surface = self._find_room_surface(text_lower, pattern)
                    detected.append({
                        "type": room_type,
                        "name": room_type.replace("_", " ").title(),
                        "surface": surface,
                    })
                    break
        
        return detected
    
    def _find_room_surface(self, text: str, room_pattern: str) -> Optional[float]:
        """Find surface associated with a room"""
        # Look for surface near the room name
        idx = text.find(room_pattern)
        if idx == -1:
            return None
        
        # Search in a window around the room name
        window = text[max(0, idx-50):idx+100]
        
        for pattern in self.surface_patterns:
            match = re.search(pattern, window)
            if match:
                surface_str = match.group(1).replace(",", ".")
                try:
                    return float(surface_str)
                except ValueError:
                    pass
        
        return None
    
    def _extract_surfaces(self, text: str) -> List[Dict[str, Any]]:
        """Extract all surface mentions from text"""
        surfaces = []
        
        for pattern in self.surface_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                surface_str = match.group(1).replace(",", ".")
                try:
                    surface = float(surface_str)
                    if 1 < surface < 1000:  # Reasonable surface range
                        surfaces.append({
                            "value": surface,
                            "unit": "m²",
                            "context": text[max(0, match.start()-20):match.end()+20].strip(),
                        })
                except ValueError:
                    pass
        
        # Remove duplicates
        seen = set()
        unique_surfaces = []
        for s in surfaces:
            if s["value"] not in seen:
                seen.add(s["value"])
                unique_surfaces.append(s)
        
        return unique_surfaces
    
    def _calculate_total_surface(self, surfaces: List[Dict]) -> float:
        """Estimate total surface from detected surfaces"""
        if not surfaces:
            return 0
        
        # Take the largest value as potential total, or sum of reasonable values
        values = [s["value"] for s in surfaces]
        max_val = max(values) if values else 0
        
        # If we have multiple small values, sum them
        small_values = [v for v in values if v < 50]
        if len(small_values) > 3:
            return sum(small_values)
        
        return max_val
    
    def _suggest_works(self, rooms: List[Dict]) -> List[Dict[str, Any]]:
        """Suggest works based on detected rooms"""
        suggestions = []
        
        room_works = {
            "cuisine": [
                {"type": "plomberie", "description": "Installation cuisine", "price_range": "2000-5000€"},
                {"type": "electricite", "description": "Points électriques cuisine", "price_range": "500-1500€"},
                {"type": "carrelage", "description": "Carrelage sol/mur", "price_range": "60-80€/m²"},
            ],
            "salle_de_bain": [
                {"type": "plomberie", "description": "Installation salle de bain", "price_range": "3000-7000€"},
                {"type": "carrelage", "description": "Faïence et carrelage", "price_range": "60-90€/m²"},
                {"type": "electricite", "description": "Points lumineux", "price_range": "200-500€"},
            ],
            "chambre": [
                {"type": "peinture", "description": "Peinture murs/plafond", "price_range": "25-35€/m²"},
                {"type": "menuiserie", "description": "Parquet/revêtement sol", "price_range": "40-80€/m²"},
            ],
            "salon": [
                {"type": "peinture", "description": "Peinture murs/plafond", "price_range": "25-35€/m²"},
                {"type": "menuiserie", "description": "Parquet/revêtement sol", "price_range": "40-80€/m²"},
                {"type": "electricite", "description": "Points lumineux et prises", "price_range": "300-800€"},
            ],
        }
        
        for room in rooms:
            room_type = room["type"]
            if room_type in room_works:
                for work in room_works[room_type]:
                    work_copy = work.copy()
                    work_copy["room"] = room["name"]
                    work_copy["surface"] = room.get("surface")
                    suggestions.append(work_copy)
        
        return suggestions


class ImageAnalysisService:
    """Analyze construction site photos"""
    
    def __init__(self):
        self.openai_key = os.environ.get("OPENAI_API_KEY")
    
    def analyze_basic(self, image_content: bytes) -> Dict[str, Any]:
        """Basic image analysis without AI"""
        try:
            img = Image.open(io.BytesIO(image_content))
            
            # Get basic info
            width, height = img.size
            format_type = img.format
            mode = img.mode
            
            # Detect dominant colors
            if mode != "RGB":
                img = img.convert("RGB")
            
            # Simple color analysis
            colors = img.getcolors(maxcolors=1000000)
            if colors:
                # Sort by frequency
                colors.sort(key=lambda x: x[0], reverse=True)
                dominant_colors = colors[:5]
            else:
                dominant_colors = []
            
            return {
                "success": True,
                "dimensions": {"width": width, "height": height},
                "format": format_type,
                "mode": mode,
                "color_analysis": "basic",
                "dominant_colors": len(dominant_colors),
                "suggestions": [
                    "Pour une analyse détaillée du chantier, décrivez les travaux souhaités dans l'Assistant IA.",
                    "Vous pouvez utiliser la fonction 'Analyser un chantier' avec une description textuelle.",
                ],
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Image analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }


class MarketingAutomationService:
    """Marketing automation for website detection and upselling"""
    
    def __init__(self, db):
        self.db = db
        self.notifications = db.marketing_notifications
    
    async def check_website_status(self, user_id: str) -> Dict[str, Any]:
        """Check if user has a website configured"""
        settings = await self.db.settings.find_one({"type": "company"})
        
        has_website = bool(settings and settings.get("website") and settings["website"].strip())
        
        return {
            "has_website": has_website,
            "website": settings.get("website") if settings else None,
            "show_upsell": not has_website,
            "message": None if has_website else "Votre entreprise n'a pas encore de site web. Un site professionnel peut vous aider à obtenir plus de clients.",
        }
    
    async def create_website_request(
        self,
        user_id: str,
        company_name: str,
        email: str,
        phone: str = None,
        message: str = None
    ) -> Dict[str, Any]:
        """Create a website creation request"""
        import uuid
        
        request_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "company_name": company_name,
            "email": email,
            "phone": phone,
            "message": message,
            "service_type": "website_creation",
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await self.db.service_requests.insert_one(request_doc)
        
        logger.info(f"Website request created for user {user_id}")
        
        return {
            "success": True,
            "request_id": request_doc["id"],
            "message": "Votre demande de création de site web a été enregistrée. Nous vous contacterons sous 24h.",
        }
    
    async def get_marketing_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get marketing notifications for a user"""
        notifications = []
        
        # Check website status
        website_status = await self.check_website_status(user_id)
        
        if not website_status["has_website"]:
            notifications.append({
                "type": "website_upsell",
                "priority": "medium",
                "title": "Site web professionnel",
                "message": website_status["message"],
                "action": {
                    "label": "Demander un devis",
                    "url": "/services?type=website",
                },
            })
        
        # Check subscription status
        user = await self.db.users.find_one({"id": user_id})
        if user:
            plan = user.get("subscription_plan", "trial")
            if plan == "trial":
                notifications.append({
                    "type": "subscription_upsell",
                    "priority": "high",
                    "title": "Passez au plan payant",
                    "message": "Débloquez toutes les fonctionnalités et continuez à développer votre activité.",
                    "action": {
                        "label": "Voir les plans",
                        "url": "/facturation",
                    },
                })
        
        return notifications


def get_signature_service(db) -> ElectronicSignatureService:
    return ElectronicSignatureService(db)

def get_pdf_analysis_service() -> PDFAnalysisService:
    return PDFAnalysisService()

def get_image_analysis_service() -> ImageAnalysisService:
    return ImageAnalysisService()

def get_marketing_service(db) -> MarketingAutomationService:
    return MarketingAutomationService(db)
