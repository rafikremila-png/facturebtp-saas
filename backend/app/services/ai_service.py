"""
AI Service for BTP Facture SaaS
Handles AI-powered quote generation, project estimation, and analysis
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ============== LOCAL PRICING DATABASE ==============

# Base prices per service type (in EUR)
BTP_PRICING_DATABASE = {
    "peinture": {
        "mur_interieur": {"price_per_m2": 25, "unit": "m²", "description": "Peinture mur intérieur (2 couches)"},
        "plafond": {"price_per_m2": 30, "unit": "m²", "description": "Peinture plafond"},
        "facade": {"price_per_m2": 45, "unit": "m²", "description": "Peinture façade extérieure"},
        "boiserie": {"price_per_ml": 35, "unit": "ml", "description": "Peinture boiseries"},
    },
    "carrelage": {
        "sol_standard": {"price_per_m2": 55, "unit": "m²", "description": "Pose carrelage sol standard"},
        "sol_grand_format": {"price_per_m2": 75, "unit": "m²", "description": "Pose carrelage grand format"},
        "mural": {"price_per_m2": 65, "unit": "m²", "description": "Pose carrelage mural"},
        "faience": {"price_per_m2": 60, "unit": "m²", "description": "Pose faïence salle de bain"},
    },
    "plomberie": {
        "salle_de_bain_complete": {"price_forfait": 3500, "unit": "forfait", "description": "Installation salle de bain complète"},
        "wc": {"price_forfait": 450, "unit": "unité", "description": "Installation WC"},
        "lavabo": {"price_forfait": 350, "unit": "unité", "description": "Installation lavabo"},
        "douche": {"price_forfait": 1200, "unit": "unité", "description": "Installation douche"},
        "baignoire": {"price_forfait": 1500, "unit": "unité", "description": "Installation baignoire"},
        "chauffe_eau": {"price_forfait": 800, "unit": "unité", "description": "Installation chauffe-eau"},
    },
    "electricite": {
        "prise": {"price_forfait": 85, "unit": "unité", "description": "Installation prise électrique"},
        "interrupteur": {"price_forfait": 65, "unit": "unité", "description": "Installation interrupteur"},
        "point_lumineux": {"price_forfait": 120, "unit": "unité", "description": "Installation point lumineux"},
        "tableau_electrique": {"price_forfait": 1500, "unit": "forfait", "description": "Installation tableau électrique"},
        "renovation_complete": {"price_per_m2": 95, "unit": "m²", "description": "Rénovation électrique complète"},
    },
    "maconnerie": {
        "mur_parpaing": {"price_per_m2": 120, "unit": "m²", "description": "Construction mur parpaing"},
        "dalle_beton": {"price_per_m2": 85, "unit": "m²", "description": "Dalle béton"},
        "demolition": {"price_per_m2": 45, "unit": "m²", "description": "Démolition mur"},
        "ouverture_mur": {"price_forfait": 2500, "unit": "forfait", "description": "Création ouverture dans mur porteur"},
    },
    "menuiserie": {
        "porte_interieure": {"price_forfait": 450, "unit": "unité", "description": "Pose porte intérieure"},
        "porte_exterieure": {"price_forfait": 1200, "unit": "unité", "description": "Pose porte extérieure"},
        "fenetre_pvc": {"price_forfait": 650, "unit": "unité", "description": "Pose fenêtre PVC"},
        "fenetre_alu": {"price_forfait": 950, "unit": "unité", "description": "Pose fenêtre aluminium"},
        "parquet": {"price_per_m2": 55, "unit": "m²", "description": "Pose parquet"},
    },
    "toiture": {
        "reparation": {"price_per_m2": 120, "unit": "m²", "description": "Réparation toiture"},
        "refection_complete": {"price_per_m2": 180, "unit": "m²", "description": "Réfection toiture complète"},
        "gouttiere": {"price_per_ml": 45, "unit": "ml", "description": "Pose gouttière"},
        "isolation": {"price_per_m2": 65, "unit": "m²", "description": "Isolation toiture"},
    },
    "isolation": {
        "murs_interieur": {"price_per_m2": 55, "unit": "m²", "description": "Isolation murs par l'intérieur"},
        "murs_exterieur": {"price_per_m2": 150, "unit": "m²", "description": "Isolation murs par l'extérieur (ITE)"},
        "combles": {"price_per_m2": 35, "unit": "m²", "description": "Isolation combles perdus"},
        "sol": {"price_per_m2": 45, "unit": "m²", "description": "Isolation sol"},
    },
    "chauffage": {
        "radiateur": {"price_forfait": 450, "unit": "unité", "description": "Installation radiateur"},
        "plancher_chauffant": {"price_per_m2": 85, "unit": "m²", "description": "Plancher chauffant"},
        "pompe_chaleur": {"price_forfait": 12000, "unit": "forfait", "description": "Installation pompe à chaleur"},
        "chaudiere_gaz": {"price_forfait": 4500, "unit": "forfait", "description": "Installation chaudière gaz"},
    },
}

# Regional price multipliers
REGIONAL_MULTIPLIERS = {
    "paris": 1.35,
    "ile_de_france": 1.25,
    "lyon": 1.15,
    "marseille": 1.10,
    "bordeaux": 1.10,
    "toulouse": 1.05,
    "nice": 1.20,
    "nantes": 1.05,
    "strasbourg": 1.05,
    "montpellier": 1.05,
    "lille": 1.00,
    "rennes": 1.00,
    "default": 1.00,
    "rural": 0.90,
}

# Project type templates
PROJECT_TEMPLATES = {
    "renovation_salle_de_bain": {
        "description": "Rénovation complète salle de bain",
        "items": [
            {"category": "plomberie", "type": "salle_de_bain_complete", "quantity": 1},
            {"category": "carrelage", "type": "sol_standard", "quantity_multiplier": 1.0},
            {"category": "carrelage", "type": "mural", "quantity_multiplier": 2.5},
            {"category": "peinture", "type": "plafond", "quantity_multiplier": 1.0},
            {"category": "electricite", "type": "point_lumineux", "quantity": 2},
        ],
    },
    "renovation_cuisine": {
        "description": "Rénovation cuisine",
        "items": [
            {"category": "plomberie", "type": "lavabo", "quantity": 1},
            {"category": "carrelage", "type": "sol_standard", "quantity_multiplier": 1.0},
            {"category": "carrelage", "type": "mural", "quantity_multiplier": 0.5},
            {"category": "electricite", "type": "prise", "quantity": 6},
            {"category": "electricite", "type": "point_lumineux", "quantity": 3},
            {"category": "peinture", "type": "mur_interieur", "quantity_multiplier": 2.5},
        ],
    },
    "renovation_appartement": {
        "description": "Rénovation appartement complet",
        "items": [
            {"category": "peinture", "type": "mur_interieur", "quantity_multiplier": 2.8},
            {"category": "peinture", "type": "plafond", "quantity_multiplier": 1.0},
            {"category": "menuiserie", "type": "parquet", "quantity_multiplier": 1.0},
            {"category": "electricite", "type": "renovation_complete", "quantity_multiplier": 1.0},
        ],
    },
    "peinture_interieure": {
        "description": "Peinture intérieure",
        "items": [
            {"category": "peinture", "type": "mur_interieur", "quantity_multiplier": 2.5},
            {"category": "peinture", "type": "plafond", "quantity_multiplier": 1.0},
        ],
    },
    "renovation_electrique": {
        "description": "Rénovation électrique complète",
        "items": [
            {"category": "electricite", "type": "tableau_electrique", "quantity": 1},
            {"category": "electricite", "type": "prise", "quantity_multiplier": 0.3},
            {"category": "electricite", "type": "interrupteur", "quantity_multiplier": 0.15},
            {"category": "electricite", "type": "point_lumineux", "quantity_multiplier": 0.1},
        ],
    },
}


class AIService:
    """AI Service for quote generation and project estimation"""
    
    def __init__(self, use_advanced_ai: bool = False):
        self.use_advanced_ai = use_advanced_ai
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    def get_regional_multiplier(self, location: str) -> float:
        """Get price multiplier based on location"""
        location_lower = location.lower().replace(" ", "_").replace("-", "_")
        
        # Check for exact match
        if location_lower in REGIONAL_MULTIPLIERS:
            return REGIONAL_MULTIPLIERS[location_lower]
        
        # Check for partial match
        for region, multiplier in REGIONAL_MULTIPLIERS.items():
            if region in location_lower or location_lower in region:
                return multiplier
        
        return REGIONAL_MULTIPLIERS["default"]
    
    def generate_quote_items(
        self,
        project_type: str,
        surface: float,
        location: str = "default",
        materials_quality: str = "standard",
        description: str = ""
    ) -> Dict[str, Any]:
        """Generate quote items based on project parameters"""
        
        # Get regional multiplier
        regional_multiplier = self.get_regional_multiplier(location)
        
        # Quality multiplier
        quality_multipliers = {
            "economique": 0.8,
            "standard": 1.0,
            "premium": 1.3,
            "luxe": 1.6,
        }
        quality_multiplier = quality_multipliers.get(materials_quality.lower(), 1.0)
        
        # Normalize project type
        project_type_normalized = project_type.lower().replace(" ", "_").replace("-", "_")
        
        # Find matching template
        template = None
        for template_key, template_data in PROJECT_TEMPLATES.items():
            if template_key in project_type_normalized or project_type_normalized in template_key:
                template = template_data
                break
        
        # Generate items
        items = []
        total_ht = 0
        
        if template:
            for item_config in template["items"]:
                category = item_config["category"]
                item_type = item_config["type"]
                
                if category in BTP_PRICING_DATABASE and item_type in BTP_PRICING_DATABASE[category]:
                    price_data = BTP_PRICING_DATABASE[category][item_type]
                    
                    # Calculate quantity
                    if "quantity" in item_config:
                        quantity = item_config["quantity"]
                    elif "quantity_multiplier" in item_config:
                        quantity = surface * item_config["quantity_multiplier"]
                    else:
                        quantity = 1
                    
                    quantity = round(quantity, 2)
                    
                    # Calculate price
                    if "price_per_m2" in price_data:
                        unit_price = price_data["price_per_m2"] * regional_multiplier * quality_multiplier
                    elif "price_per_ml" in price_data:
                        unit_price = price_data["price_per_ml"] * regional_multiplier * quality_multiplier
                    else:
                        unit_price = price_data["price_forfait"] * regional_multiplier * quality_multiplier
                    
                    unit_price = round(unit_price, 2)
                    line_total = round(quantity * unit_price, 2)
                    total_ht += line_total
                    
                    items.append({
                        "description": price_data["description"],
                        "quantity": quantity,
                        "unit": price_data["unit"],
                        "unit_price": unit_price,
                        "vat_rate": 10.0,  # TVA travaux
                        "total_ht": line_total,
                    })
        else:
            # Generic estimation based on surface
            items = self._generate_generic_items(surface, regional_multiplier, quality_multiplier)
            total_ht = sum(item["total_ht"] for item in items)
        
        return {
            "items": items,
            "total_ht": round(total_ht, 2),
            "total_vat": round(total_ht * 0.10, 2),
            "total_ttc": round(total_ht * 1.10, 2),
            "regional_multiplier": regional_multiplier,
            "quality_multiplier": quality_multiplier,
            "location": location,
            "project_type": project_type,
            "surface": surface,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def _generate_generic_items(
        self,
        surface: float,
        regional_multiplier: float,
        quality_multiplier: float
    ) -> List[Dict]:
        """Generate generic renovation items when no template matches"""
        base_price_per_m2 = 450  # Average renovation cost
        adjusted_price = base_price_per_m2 * regional_multiplier * quality_multiplier
        
        return [
            {
                "description": "Travaux de rénovation",
                "quantity": surface,
                "unit": "m²",
                "unit_price": round(adjusted_price, 2),
                "vat_rate": 10.0,
                "total_ht": round(surface * adjusted_price, 2),
            }
        ]
    
    def estimate_project_cost(
        self,
        project_type: str,
        surface: float,
        location: str = "default",
        complexity: str = "standard"
    ) -> Dict[str, Any]:
        """Estimate total project cost with labor and materials breakdown"""
        
        regional_multiplier = self.get_regional_multiplier(location)
        
        # Complexity multipliers
        complexity_multipliers = {
            "simple": 0.8,
            "standard": 1.0,
            "complexe": 1.3,
            "tres_complexe": 1.6,
        }
        complexity_mult = complexity_multipliers.get(complexity.lower(), 1.0)
        
        # Base costs per m² (labor + materials)
        project_costs = {
            "renovation_salle_de_bain": {"labor": 150, "materials": 200},
            "renovation_cuisine": {"labor": 120, "materials": 180},
            "renovation_appartement": {"labor": 100, "materials": 150},
            "peinture": {"labor": 15, "materials": 10},
            "carrelage": {"labor": 35, "materials": 25},
            "electricite": {"labor": 50, "materials": 40},
            "plomberie": {"labor": 60, "materials": 80},
            "default": {"labor": 80, "materials": 120},
        }
        
        # Find matching costs
        costs = project_costs.get("default")
        for key, value in project_costs.items():
            if key in project_type.lower():
                costs = value
                break
        
        labor_cost = surface * costs["labor"] * regional_multiplier * complexity_mult
        materials_cost = surface * costs["materials"] * regional_multiplier * complexity_mult
        total_ht = labor_cost + materials_cost
        
        # Estimated duration (days)
        duration_per_m2 = 0.15  # Average days per m²
        estimated_days = max(1, round(surface * duration_per_m2 * complexity_mult))
        
        return {
            "project_type": project_type,
            "surface": surface,
            "location": location,
            "complexity": complexity,
            "labor_cost": round(labor_cost, 2),
            "materials_cost": round(materials_cost, 2),
            "total_ht": round(total_ht, 2),
            "total_vat": round(total_ht * 0.10, 2),
            "total_ttc": round(total_ht * 1.10, 2),
            "estimated_duration_days": estimated_days,
            "price_range": {
                "min": round(total_ht * 0.85, 2),
                "max": round(total_ht * 1.15, 2),
            },
            "regional_multiplier": regional_multiplier,
            "estimated_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def analyze_site_description(self, description: str) -> Dict[str, Any]:
        """Analyze site description and suggest quote items"""
        
        # Keywords to detect work types
        keywords = {
            "peinture": ["peinture", "peindre", "mur", "plafond", "couleur"],
            "carrelage": ["carrelage", "carreleur", "faience", "sol", "tomette"],
            "plomberie": ["plomberie", "plombier", "eau", "tuyau", "robinet", "sanitaire", "douche", "baignoire", "wc", "toilette"],
            "electricite": ["electricite", "electricien", "prise", "interrupteur", "tableau", "lumiere"],
            "maconnerie": ["maconnerie", "macon", "mur", "demolition", "ouverture", "beton", "parpaing"],
            "menuiserie": ["menuiserie", "menuisier", "porte", "fenetre", "parquet", "bois"],
            "isolation": ["isolation", "isoler", "thermique", "laine", "combles"],
            "toiture": ["toiture", "toit", "gouttiere", "ardoise", "tuile"],
        }
        
        description_lower = description.lower()
        detected_works = []
        
        for work_type, words in keywords.items():
            for word in words:
                if word in description_lower:
                    detected_works.append(work_type)
                    break
        
        # Remove duplicates
        detected_works = list(set(detected_works))
        
        # Generate suggestions
        suggestions = []
        for work_type in detected_works:
            if work_type in BTP_PRICING_DATABASE:
                for item_key, item_data in BTP_PRICING_DATABASE[work_type].items():
                    suggestions.append({
                        "category": work_type,
                        "type": item_key,
                        "description": item_data["description"],
                        "unit": item_data["unit"],
                        "base_price": item_data.get("price_per_m2") or item_data.get("price_per_ml") or item_data.get("price_forfait"),
                    })
        
        return {
            "detected_work_types": detected_works,
            "suggestions": suggestions,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }


def get_ai_service(use_advanced: bool = False) -> AIService:
    """Factory function"""
    return AIService(use_advanced_ai=use_advanced)
