"""
AI Document Analysis Service
PDF and document analysis using Gemini AI
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger(__name__)

class AIDocumentService:
    """Service for AI-powered document analysis"""
    
    def __init__(self):
        self.api_key = settings.EMERGENT_LLM_KEY or os.getenv("EMERGENT_LLM_KEY")
        self.provider = "gemini"
        self.model = "gemini-2.5-flash"
    
    async def analyze_pdf(self, file_path: str, analysis_type: str = "invoice") -> Dict[str, Any]:
        """Analyze a PDF document using AI"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
            
            if not self.api_key:
                return {
                    "success": False,
                    "error": "AI API key not configured"
                }
            
            # Determine the extraction prompt based on type
            prompts = {
                "invoice": self._get_invoice_prompt(),
                "quote": self._get_quote_prompt(),
                "contract": self._get_contract_prompt(),
                "plan": self._get_plan_prompt()
            }
            
            prompt = prompts.get(analysis_type, prompts["invoice"])
            
            # Initialize chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"doc_analysis_{datetime.now().timestamp()}",
                system_message="Tu es un assistant expert en analyse de documents BTP (Bâtiment et Travaux Publics). Tu extrais les informations des documents de manière précise et structurée."
            ).with_model(self.provider, self.model)
            
            # Create file attachment
            file_content = FileContentWithMimeType(
                file_path=file_path,
                mime_type="application/pdf"
            )
            
            # Create message
            user_message = UserMessage(
                text=prompt,
                file_contents=[file_content]
            )
            
            # Send message and get response
            response = await chat.send_message(user_message)
            
            # Parse the response
            extracted_data = self._parse_ai_response(response, analysis_type)
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "data": extracted_data,
                "raw_response": response,
                "confidence": extracted_data.get("confidence", 0.8)
            }
            
        except ImportError:
            logger.error("emergentintegrations library not installed")
            return {
                "success": False,
                "error": "AI library not available. Please install emergentintegrations."
            }
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_construction_plan(self, file_path: str) -> Dict[str, Any]:
        """Analyze a construction plan PDF"""
        return await self.analyze_pdf(file_path, "plan")
    
    async def generate_quote_items(self, project_description: str, 
                                    project_type: Optional[str] = None,
                                    surface_area: Optional[float] = None,
                                    location: Optional[str] = None) -> Dict[str, Any]:
        """Generate quote items based on project description"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            if not self.api_key:
                return {
                    "success": False,
                    "error": "AI API key not configured"
                }
            
            # Build prompt
            prompt = f"""En tant qu'expert BTP, génère une liste détaillée de postes pour un devis basé sur la description suivante:

Description du projet: {project_description}
"""
            if project_type:
                prompt += f"\nType de projet: {project_type}"
            if surface_area:
                prompt += f"\nSurface: {surface_area} m²"
            if location:
                prompt += f"\nLocalisation: {location}"
            
            prompt += """

Retourne les postes au format JSON avec la structure suivante:
{
    "items": [
        {
            "description": "Description du poste",
            "category": "Catégorie (ex: Maçonnerie, Plomberie)",
            "quantity": 1,
            "unit": "u|m²|m³|ml|h|forfait",
            "unit_price": 0.00,
            "vat_rate": 20.0,
            "notes": "Notes éventuelles"
        }
    ],
    "estimated_total_ht": 0.00,
    "notes": "Notes générales sur le devis",
    "recommendations": ["Recommandation 1", "Recommandation 2"]
}

Utilise des prix réalistes du marché français pour le BTP. Inclus tous les postes nécessaires."""
            
            # Initialize chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"quote_gen_{datetime.now().timestamp()}",
                system_message="Tu es un métreur expert en BTP. Tu génères des devis précis et complets avec des prix de marché réalistes."
            ).with_model(self.provider, self.model)
            
            # Send message
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Parse response
            result = self._extract_json_from_response(response)
            
            if result:
                return {
                    "success": True,
                    "suggested_items": result.get("items", []),
                    "estimated_total": result.get("estimated_total_ht", 0),
                    "notes": result.get("notes", ""),
                    "recommendations": result.get("recommendations", [])
                }
            else:
                return {
                    "success": True,
                    "suggested_items": [],
                    "raw_response": response,
                    "notes": "Impossible de parser la réponse automatiquement"
                }
            
        except Exception as e:
            logger.error(f"Quote generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def estimate_project_cost(self, project_description: str,
                                     surface_area: Optional[float] = None,
                                     project_type: Optional[str] = None) -> Dict[str, Any]:
        """Estimate project cost using AI"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            if not self.api_key:
                return {
                    "success": False,
                    "error": "AI API key not configured"
                }
            
            prompt = f"""En tant qu'expert en estimation BTP, estime les coûts pour le projet suivant:

Description: {project_description}
"""
            if surface_area:
                prompt += f"Surface: {surface_area} m²\n"
            if project_type:
                prompt += f"Type: {project_type}\n"
            
            prompt += """
Retourne l'estimation au format JSON:
{
    "estimated_labor_cost": 0.00,
    "estimated_material_cost": 0.00,
    "estimated_total_ht": 0.00,
    "estimated_total_ttc": 0.00,
    "estimated_duration_days": 0,
    "cost_breakdown": [
        {"category": "Catégorie", "amount": 0.00, "percentage": 0}
    ],
    "confidence_level": "high|medium|low",
    "assumptions": ["Hypothèse 1", "Hypothèse 2"],
    "risks": ["Risque potentiel 1", "Risque potentiel 2"]
}

Base ton estimation sur les prix moyens du marché français."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"cost_estimate_{datetime.now().timestamp()}",
                system_message="Tu es un économiste de la construction expert en estimation de coûts BTP."
            ).with_model(self.provider, self.model)
            
            response = await chat.send_message(UserMessage(text=prompt))
            result = self._extract_json_from_response(response)
            
            if result:
                return {
                    "success": True,
                    **result
                }
            else:
                return {
                    "success": True,
                    "raw_response": response,
                    "notes": "Estimation générée mais format non structuré"
                }
            
        except Exception as e:
            logger.error(f"Cost estimation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_invoice_prompt(self) -> str:
        return """Analyse cette facture et extrait les informations suivantes au format JSON:
{
    "invoice_number": "Numéro de facture",
    "invoice_date": "Date de facture (YYYY-MM-DD)",
    "due_date": "Date d'échéance (YYYY-MM-DD)",
    "company": {
        "name": "Nom de l'entreprise émettrice",
        "address": "Adresse",
        "siret": "SIRET",
        "vat_number": "Numéro TVA"
    },
    "client": {
        "name": "Nom du client",
        "address": "Adresse du client"
    },
    "items": [
        {
            "description": "Description",
            "quantity": 1,
            "unit_price": 0.00,
            "vat_rate": 20.0,
            "total": 0.00
        }
    ],
    "subtotal_ht": 0.00,
    "total_vat": 0.00,
    "total_ttc": 0.00,
    "payment_terms": "Conditions de paiement",
    "confidence": 0.95
}

Si une information n'est pas trouvée, utilise null."""
    
    def _get_quote_prompt(self) -> str:
        return """Analyse ce devis et extrait les informations au format JSON:
{
    "quote_number": "Numéro de devis",
    "quote_date": "Date du devis (YYYY-MM-DD)",
    "validity_date": "Date de validité (YYYY-MM-DD)",
    "company": {
        "name": "Entreprise émettrice",
        "address": "Adresse"
    },
    "client": {
        "name": "Client",
        "address": "Adresse"
    },
    "project": {
        "title": "Titre du projet",
        "address": "Adresse du chantier",
        "description": "Description"
    },
    "items": [
        {
            "description": "Description",
            "quantity": 1,
            "unit": "u",
            "unit_price": 0.00,
            "vat_rate": 20.0
        }
    ],
    "subtotal_ht": 0.00,
    "total_vat": 0.00,
    "total_ttc": 0.00,
    "conditions": "Conditions générales",
    "confidence": 0.95
}"""
    
    def _get_contract_prompt(self) -> str:
        return """Analyse ce contrat BTP et extrait les informations clés au format JSON:
{
    "contract_type": "Type de contrat",
    "parties": [
        {"role": "Maître d'ouvrage", "name": "Nom", "address": "Adresse"},
        {"role": "Entreprise", "name": "Nom", "address": "Adresse"}
    ],
    "project": {
        "title": "Titre",
        "address": "Adresse du chantier",
        "description": "Description des travaux"
    },
    "amounts": {
        "total_ht": 0.00,
        "total_ttc": 0.00
    },
    "dates": {
        "signature": "Date signature",
        "start": "Date début",
        "end": "Date fin prévue"
    },
    "terms": {
        "payment": "Conditions de paiement",
        "retention": "Retenue de garantie",
        "penalties": "Pénalités de retard"
    },
    "confidence": 0.90
}"""
    
    def _get_plan_prompt(self) -> str:
        return """Analyse ce plan de construction et extrait les informations au format JSON:
{
    "plan_type": "Type de plan (plan masse, plan de niveau, coupe, etc.)",
    "project_name": "Nom du projet",
    "scale": "Échelle",
    "measurements": [
        {
            "zone": "Zone/Pièce",
            "dimensions": {"length": 0.00, "width": 0.00},
            "surface": 0.00,
            "unit": "m²"
        }
    ],
    "total_surface": 0.00,
    "rooms": [
        {"name": "Nom de la pièce", "surface": 0.00}
    ],
    "suggested_work_items": [
        {
            "category": "Catégorie de travaux",
            "description": "Description",
            "estimated_quantity": 0.00,
            "unit": "m²"
        }
    ],
    "notes": "Observations importantes",
    "confidence": 0.85
}

Identifie les surfaces et suggère les postes de travaux nécessaires."""
    
    def _parse_ai_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data"""
        result = self._extract_json_from_response(response)
        if result:
            return result
        
        # If JSON extraction failed, return raw response
        return {
            "raw_text": response,
            "confidence": 0.5,
            "parsing_failed": True
        }
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from AI response"""
        try:
            # Try direct parsing
            return json.loads(response)
        except:
            pass
        
        # Try to find JSON in the response
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Try to find JSON array
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return {"items": json.loads(json_str)}
        except:
            pass
        
        return None


# Create singleton instance
ai_document_service = AIDocumentService()
