"""
AI PDF Analysis Service
Uses Gemini 3 Flash to analyze construction plan PDFs
Extracts measurements, materials, quantities for quote generation
"""
import os
import logging
import json
import tempfile
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class PDFAnalysisService:
    """Service for AI-powered PDF analysis using Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv("EMERGENT_LLM_KEY")
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not configured")
    
    async def analyze_construction_pdf(
        self, 
        file_path: str,
        analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Analyze a construction plan PDF and extract structured data
        
        Args:
            file_path: Path to the PDF file
            analysis_type: Type of analysis
                - 'full': Complete analysis with all details
                - 'materials': Extract materials list only
                - 'measurements': Extract measurements only
                - 'summary': Quick summary
        
        Returns:
            Structured data extracted from the PDF
        """
        from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
        
        # Initialize Gemini chat
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"pdf-analysis-{datetime.now(timezone.utc).timestamp()}",
            system_message=self._get_system_prompt(analysis_type)
        ).with_model("gemini", "gemini-2.5-flash")
        
        # Create file attachment
        pdf_file = FileContentWithMimeType(
            file_path=file_path,
            mime_type="application/pdf"
        )
        
        # Build the analysis prompt
        prompt = self._get_analysis_prompt(analysis_type)
        
        # Send for analysis
        user_message = UserMessage(
            text=prompt,
            file_contents=[pdf_file]
        )
        
        try:
            response = await chat.send_message(user_message)
            
            # Parse the response
            result = self._parse_response(response, analysis_type)
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "data": result,
                "raw_response": response,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"PDF analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_type": analysis_type
            }
    
    async def extract_quote_items(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract items suitable for quote/invoice generation from a PDF
        
        Returns a list of items with:
        - description
        - quantity
        - unit
        - estimated_price (if available)
        - category
        """
        from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"quote-extract-{datetime.now(timezone.utc).timestamp()}",
            system_message="""Tu es un expert en BTP (Bâtiment et Travaux Publics) spécialisé dans l'analyse de plans et devis.
            Tu dois extraire les éléments pouvant être utilisés pour créer un devis.
            Réponds UNIQUEMENT en JSON valide, sans texte supplémentaire."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        pdf_file = FileContentWithMimeType(
            file_path=file_path,
            mime_type="application/pdf"
        )
        
        prompt = """Analyse ce document PDF de construction et extrait tous les éléments qui peuvent être facturés.

Pour chaque élément, fournis:
- description: description claire de l'ouvrage
- quantity: quantité (nombre)
- unit: unité (m², m, u, h, forfait, m³, kg, L)
- category: catégorie BTP (gros_oeuvre, electricite, plomberie, chauffage, isolation, menuiserie, carrelage, peinture, toiture, maconnerie, terrassement, second_oeuvre, autres)
- estimated_price: prix unitaire estimé en euros (optionnel)

Réponds UNIQUEMENT avec un tableau JSON valide:
[
  {
    "description": "...",
    "quantity": 10,
    "unit": "m²",
    "category": "...",
    "estimated_price": 25.00
  }
]"""
        
        user_message = UserMessage(
            text=prompt,
            file_contents=[pdf_file]
        )
        
        try:
            response = await chat.send_message(user_message)
            
            # Parse JSON from response
            items = self._extract_json_array(response)
            
            # Validate and clean items
            validated_items = []
            for item in items:
                validated_item = {
                    "description": str(item.get("description", ""))[:500],
                    "quantity": float(item.get("quantity", 1)),
                    "unit": self._validate_unit(item.get("unit", "u")),
                    "category": self._validate_category(item.get("category", "autres")),
                    "estimated_price": float(item.get("estimated_price", 0)) if item.get("estimated_price") else None
                }
                if validated_item["description"]:
                    validated_items.append(validated_item)
            
            return validated_items
            
        except Exception as e:
            logger.error(f"Quote extraction failed: {e}")
            return []
    
    async def summarize_document(self, file_path: str) -> str:
        """Get a quick summary of the document"""
        from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"doc-summary-{datetime.now(timezone.utc).timestamp()}",
            system_message="Tu es un expert en BTP. Fournis des résumés clairs et concis."
        ).with_model("gemini", "gemini-2.5-flash")
        
        pdf_file = FileContentWithMimeType(
            file_path=file_path,
            mime_type="application/pdf"
        )
        
        user_message = UserMessage(
            text="Résume ce document de construction en 3-5 phrases. Indique le type de projet, la surface approximative, et les principaux travaux.",
            file_contents=[pdf_file]
        )
        
        try:
            response = await chat.send_message(user_message)
            return response
        except Exception as e:
            logger.error(f"Document summary failed: {e}")
            return f"Erreur lors de l'analyse: {str(e)}"
    
    def _get_system_prompt(self, analysis_type: str) -> str:
        """Get system prompt based on analysis type"""
        base = "Tu es un expert en BTP (Bâtiment et Travaux Publics) spécialisé dans l'analyse de plans de construction."
        
        if analysis_type == "materials":
            return f"{base} Tu dois identifier tous les matériaux mentionnés dans le document."
        elif analysis_type == "measurements":
            return f"{base} Tu dois extraire toutes les mesures et dimensions du document."
        elif analysis_type == "summary":
            return f"{base} Tu dois fournir un résumé concis du projet."
        else:
            return f"""{base}
Tu analyses des plans et documents de construction pour en extraire:
- Les mesures et dimensions
- Les matériaux nécessaires
- Les quantités estimées
- Les types de travaux

Réponds toujours de manière structurée et précise."""
    
    def _get_analysis_prompt(self, analysis_type: str) -> str:
        """Get analysis prompt based on type"""
        if analysis_type == "materials":
            return """Analyse ce document et liste tous les matériaux de construction mentionnés.
Pour chaque matériau, indique:
- Nom du matériau
- Quantité si spécifiée
- Unité de mesure
- Utilisation prévue

Réponds en JSON structuré."""
        
        elif analysis_type == "measurements":
            return """Analyse ce document et extrait toutes les mesures et dimensions.
Pour chaque mesure, indique:
- Type (surface, longueur, volume, etc.)
- Valeur
- Unité
- Emplacement/pièce concernée

Réponds en JSON structuré."""
        
        elif analysis_type == "summary":
            return """Fournis un résumé du projet de construction:
- Type de projet
- Surface totale
- Nombre de pièces
- Principaux travaux prévus
- Budget estimé si mentionné

Réponds en texte clair et concis."""
        
        else:  # full
            return """Analyse complète de ce document de construction.

Extrait les informations suivantes en JSON:
{
  "project_type": "type de projet",
  "total_surface": "surface en m²",
  "rooms": [{"name": "nom", "surface": "m²"}],
  "materials": [{"name": "nom", "quantity": "qté", "unit": "unité"}],
  "works": [{"type": "type", "description": "desc", "estimated_cost": "€"}],
  "measurements": [{"type": "type", "value": "valeur", "unit": "unité"}],
  "notes": "remarques importantes"
}"""
    
    def _parse_response(self, response: str, analysis_type: str) -> Any:
        """Parse the AI response based on analysis type"""
        if analysis_type == "summary":
            return response
        
        # Try to extract JSON
        try:
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            # Try array
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            return {"raw_text": response}
            
        except json.JSONDecodeError:
            return {"raw_text": response}
    
    def _extract_json_array(self, response: str) -> List[Dict]:
        """Extract JSON array from response"""
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            return []
        except json.JSONDecodeError:
            return []
    
    def _validate_unit(self, unit: str) -> str:
        """Validate and normalize unit"""
        valid_units = ['u', 'm', 'm²', 'm³', 'h', 'j', 'kg', 'L', 'lot', 'forfait']
        unit = str(unit).strip().lower()
        
        # Common mappings
        mappings = {
            'unité': 'u',
            'unite': 'u',
            'mètre': 'm',
            'metre': 'm',
            'mètre carré': 'm²',
            'metre carre': 'm²',
            'm2': 'm²',
            'mètre cube': 'm³',
            'metre cube': 'm³',
            'm3': 'm³',
            'heure': 'h',
            'jour': 'j',
            'kilogramme': 'kg',
            'litre': 'L',
            'ens': 'lot',
            'ensemble': 'lot'
        }
        
        return mappings.get(unit, unit if unit in valid_units else 'u')
    
    def _validate_category(self, category: str) -> str:
        """Validate and normalize category"""
        valid_categories = [
            'gros_oeuvre', 'second_oeuvre', 'electricite', 'plomberie',
            'chauffage', 'isolation', 'menuiserie', 'carrelage',
            'peinture', 'toiture', 'maconnerie', 'terrassement', 'autres'
        ]
        
        category = str(category).strip().lower().replace(' ', '_').replace('é', 'e').replace('ç', 'c')
        
        return category if category in valid_categories else 'autres'


def get_pdf_analysis_service() -> PDFAnalysisService:
    """Factory function"""
    return PDFAnalysisService()
