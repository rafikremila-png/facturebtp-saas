"""
Simplified Article Service for BTP Facture
Category -> Article (NO subcategories)
With massive library and smart filtering by business_type
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

logger = logging.getLogger(__name__)

# ============== BUSINESS TYPES ==============

BUSINESS_TYPES = ["general", "electrician", "plumber", "painter", "network_installer"]

BUSINESS_TYPE_LABELS = {
    "general": "Entrepreneur général",
    "electrician": "Électricien",
    "plumber": "Plombier / Chauffagiste",
    "painter": "Peintre en bâtiment",
    "network_installer": "Installateur réseaux"
}

# ============== CATEGORIES ==============

CATEGORIES = [
    "Électricité",
    "Plomberie",
    "Chauffage",
    "Peinture",
    "Maçonnerie",
    "Menuiserie",
    "Carrelage",
    "Plâtrerie / Isolation",
    "Réseaux & Courants Faibles",
    "Rénovation générale",
    "Main d'œuvre"
]

# ============== MASSIVE ARTICLE LIBRARY ==============

ARTICLES_LIBRARY = [
    # ========== ÉLECTRICITÉ (30+ articles) ==========
    {"name": "Installation tableau électrique", "category": "Électricité", "unit": "forfait", "price": 950, "for": ["electrician", "general"]},
    {"name": "Remplacement tableau électrique", "category": "Électricité", "unit": "forfait", "price": 850, "for": ["electrician", "general"]},
    {"name": "Mise aux normes NF C 15-100", "category": "Électricité", "unit": "forfait", "price": 1200, "for": ["electrician", "general"]},
    {"name": "Installation prise électrique", "category": "Électricité", "unit": "unité", "price": 65, "for": ["electrician", "general"]},
    {"name": "Installation prise spécialisée 32A", "category": "Électricité", "unit": "unité", "price": 120, "for": ["electrician", "general"]},
    {"name": "Installation interrupteur simple", "category": "Électricité", "unit": "unité", "price": 55, "for": ["electrician", "general"]},
    {"name": "Installation interrupteur va-et-vient", "category": "Électricité", "unit": "unité", "price": 85, "for": ["electrician", "general"]},
    {"name": "Installation variateur", "category": "Électricité", "unit": "unité", "price": 95, "for": ["electrician", "general"]},
    {"name": "Pose luminaire plafonnier", "category": "Électricité", "unit": "unité", "price": 75, "for": ["electrician", "general"]},
    {"name": "Pose spot encastré LED", "category": "Électricité", "unit": "unité", "price": 45, "for": ["electrician", "general"]},
    {"name": "Pose applique murale", "category": "Électricité", "unit": "unité", "price": 65, "for": ["electrician", "general"]},
    {"name": "Tirage de câble électrique", "category": "Électricité", "unit": "ml", "price": 15, "for": ["electrician", "general"]},
    {"name": "Pose goulotte électrique", "category": "Électricité", "unit": "ml", "price": 22, "for": ["electrician", "general"]},
    {"name": "Installation disjoncteur différentiel", "category": "Électricité", "unit": "unité", "price": 180, "for": ["electrician", "general"]},
    {"name": "Installation disjoncteur modulaire", "category": "Électricité", "unit": "unité", "price": 85, "for": ["electrician", "general"]},
    {"name": "Recherche de panne électrique", "category": "Électricité", "unit": "forfait", "price": 120, "for": ["electrician", "general"]},
    {"name": "Réparation court-circuit", "category": "Électricité", "unit": "forfait", "price": 180, "for": ["electrician", "general"]},
    {"name": "Installation parafoudre", "category": "Électricité", "unit": "unité", "price": 250, "for": ["electrician", "general"]},
    {"name": "Mise à la terre", "category": "Électricité", "unit": "forfait", "price": 350, "for": ["electrician", "general"]},
    {"name": "Diagnostic électrique", "category": "Électricité", "unit": "forfait", "price": 150, "for": ["electrician", "general"]},
    {"name": "Installation VMC simple flux", "category": "Électricité", "unit": "forfait", "price": 450, "for": ["electrician", "general"]},
    {"name": "Installation VMC double flux", "category": "Électricité", "unit": "forfait", "price": 1200, "for": ["electrician", "general"]},
    {"name": "Installation sonnette/carillon", "category": "Électricité", "unit": "forfait", "price": 120, "for": ["electrician", "general"]},
    {"name": "Installation détecteur de fumée", "category": "Électricité", "unit": "unité", "price": 45, "for": ["electrician", "general"]},
    {"name": "Installation détecteur de mouvement", "category": "Électricité", "unit": "unité", "price": 85, "for": ["electrician", "general"]},
    {"name": "Câblage tableau divisionnaire", "category": "Électricité", "unit": "forfait", "price": 450, "for": ["electrician", "general"]},
    {"name": "Installation borne recharge VE", "category": "Électricité", "unit": "forfait", "price": 1500, "for": ["electrician", "general"]},
    {"name": "Remplacement prise défectueuse", "category": "Électricité", "unit": "unité", "price": 75, "for": ["electrician", "general"]},
    {"name": "Installation éclairage extérieur", "category": "Électricité", "unit": "unité", "price": 150, "for": ["electrician", "general"]},
    {"name": "Intervention urgente électricité", "category": "Électricité", "unit": "forfait", "price": 180, "for": ["electrician", "general"]},

    # ========== PLOMBERIE (30+ articles) ==========
    {"name": "Installation WC suspendu", "category": "Plomberie", "unit": "forfait", "price": 650, "for": ["plumber", "general"]},
    {"name": "Installation WC à poser", "category": "Plomberie", "unit": "forfait", "price": 280, "for": ["plumber", "general"]},
    {"name": "Installation lavabo", "category": "Plomberie", "unit": "forfait", "price": 320, "for": ["plumber", "general"]},
    {"name": "Installation meuble vasque", "category": "Plomberie", "unit": "forfait", "price": 450, "for": ["plumber", "general"]},
    {"name": "Installation évier cuisine", "category": "Plomberie", "unit": "forfait", "price": 280, "for": ["plumber", "general"]},
    {"name": "Installation douche italienne", "category": "Plomberie", "unit": "forfait", "price": 1800, "for": ["plumber", "general"]},
    {"name": "Installation receveur douche", "category": "Plomberie", "unit": "forfait", "price": 850, "for": ["plumber", "general"]},
    {"name": "Installation baignoire", "category": "Plomberie", "unit": "forfait", "price": 650, "for": ["plumber", "general"]},
    {"name": "Installation colonne de douche", "category": "Plomberie", "unit": "forfait", "price": 380, "for": ["plumber", "general"]},
    {"name": "Remplacement mitigeur", "category": "Plomberie", "unit": "unité", "price": 150, "for": ["plumber", "general"]},
    {"name": "Remplacement robinet", "category": "Plomberie", "unit": "unité", "price": 120, "for": ["plumber", "general"]},
    {"name": "Débouchage canalisation", "category": "Plomberie", "unit": "forfait", "price": 120, "for": ["plumber", "general"]},
    {"name": "Débouchage haute pression", "category": "Plomberie", "unit": "forfait", "price": 250, "for": ["plumber", "general"]},
    {"name": "Recherche de fuite", "category": "Plomberie", "unit": "forfait", "price": 150, "for": ["plumber", "general"]},
    {"name": "Réparation fuite apparente", "category": "Plomberie", "unit": "forfait", "price": 95, "for": ["plumber", "general"]},
    {"name": "Réparation fuite encastrée", "category": "Plomberie", "unit": "forfait", "price": 280, "for": ["plumber", "general"]},
    {"name": "Installation siphon", "category": "Plomberie", "unit": "unité", "price": 45, "for": ["plumber", "general"]},
    {"name": "Tirage tuyauterie cuivre", "category": "Plomberie", "unit": "ml", "price": 35, "for": ["plumber", "general"]},
    {"name": "Tirage tuyauterie PER", "category": "Plomberie", "unit": "ml", "price": 25, "for": ["plumber", "general"]},
    {"name": "Installation machine à laver", "category": "Plomberie", "unit": "forfait", "price": 120, "for": ["plumber", "general"]},
    {"name": "Installation lave-vaisselle", "category": "Plomberie", "unit": "forfait", "price": 120, "for": ["plumber", "general"]},
    {"name": "Remplacement joint", "category": "Plomberie", "unit": "unité", "price": 45, "for": ["plumber", "general"]},
    {"name": "Installation sèche-serviettes", "category": "Plomberie", "unit": "forfait", "price": 280, "for": ["plumber", "general"]},
    {"name": "Remplacement flotteur WC", "category": "Plomberie", "unit": "forfait", "price": 85, "for": ["plumber", "general"]},
    {"name": "Intervention urgente plomberie", "category": "Plomberie", "unit": "forfait", "price": 180, "for": ["plumber", "general"]},
    {"name": "Installation adoucisseur d'eau", "category": "Plomberie", "unit": "forfait", "price": 650, "for": ["plumber", "general"]},
    {"name": "Détartrage canalisation", "category": "Plomberie", "unit": "forfait", "price": 180, "for": ["plumber", "general"]},
    {"name": "Installation vanne d'arrêt", "category": "Plomberie", "unit": "unité", "price": 95, "for": ["plumber", "general"]},
    {"name": "Installation réducteur pression", "category": "Plomberie", "unit": "unité", "price": 150, "for": ["plumber", "general"]},
    {"name": "Création point d'eau", "category": "Plomberie", "unit": "forfait", "price": 350, "for": ["plumber", "general"]},

    # ========== CHAUFFAGE (15 articles) ==========
    {"name": "Installation chauffe-eau électrique", "category": "Chauffage", "unit": "forfait", "price": 450, "for": ["plumber", "general"]},
    {"name": "Installation chauffe-eau thermodynamique", "category": "Chauffage", "unit": "forfait", "price": 850, "for": ["plumber", "general"]},
    {"name": "Installation chauffe-eau gaz", "category": "Chauffage", "unit": "forfait", "price": 650, "for": ["plumber", "general"]},
    {"name": "Remplacement radiateur", "category": "Chauffage", "unit": "unité", "price": 250, "for": ["plumber", "general"]},
    {"name": "Installation radiateur", "category": "Chauffage", "unit": "unité", "price": 320, "for": ["plumber", "general"]},
    {"name": "Purge circuit chauffage", "category": "Chauffage", "unit": "forfait", "price": 120, "for": ["plumber", "general"]},
    {"name": "Désembouage radiateurs", "category": "Chauffage", "unit": "forfait", "price": 450, "for": ["plumber", "general"]},
    {"name": "Installation thermostat", "category": "Chauffage", "unit": "forfait", "price": 180, "for": ["plumber", "general"]},
    {"name": "Installation plancher chauffant", "category": "Chauffage", "unit": "m²", "price": 85, "for": ["plumber", "general"]},
    {"name": "Entretien chaudière gaz", "category": "Chauffage", "unit": "forfait", "price": 120, "for": ["plumber", "general"]},
    {"name": "Installation pompe à chaleur", "category": "Chauffage", "unit": "forfait", "price": 5500, "for": ["plumber", "general"]},
    {"name": "Installation climatisation", "category": "Chauffage", "unit": "forfait", "price": 1800, "for": ["plumber", "general"]},
    {"name": "Entretien climatisation", "category": "Chauffage", "unit": "forfait", "price": 150, "for": ["plumber", "general"]},
    {"name": "Installation robinet thermostatique", "category": "Chauffage", "unit": "unité", "price": 85, "for": ["plumber", "general"]},
    {"name": "Remplacement circulateur", "category": "Chauffage", "unit": "forfait", "price": 380, "for": ["plumber", "general"]},

    # ========== PEINTURE (30+ articles) ==========
    {"name": "Peinture mur", "category": "Peinture", "unit": "m²", "price": 28, "for": ["painter", "general"]},
    {"name": "Peinture plafond", "category": "Peinture", "unit": "m²", "price": 32, "for": ["painter", "general"]},
    {"name": "Peinture boiseries", "category": "Peinture", "unit": "ml", "price": 18, "for": ["painter", "general"]},
    {"name": "Peinture porte", "category": "Peinture", "unit": "unité", "price": 95, "for": ["painter", "general"]},
    {"name": "Peinture fenêtre", "category": "Peinture", "unit": "unité", "price": 85, "for": ["painter", "general"]},
    {"name": "Peinture radiateur", "category": "Peinture", "unit": "unité", "price": 65, "for": ["painter", "general"]},
    {"name": "Peinture façade", "category": "Peinture", "unit": "m²", "price": 25, "for": ["painter", "general"]},
    {"name": "Peinture volets bois", "category": "Peinture", "unit": "m²", "price": 55, "for": ["painter", "general"]},
    {"name": "Peinture portail métal", "category": "Peinture", "unit": "m²", "price": 48, "for": ["painter", "general"]},
    {"name": "Enduit rebouchage", "category": "Peinture", "unit": "m²", "price": 12, "for": ["painter", "general"]},
    {"name": "Enduit lissage", "category": "Peinture", "unit": "m²", "price": 18, "for": ["painter", "general"]},
    {"name": "Ponçage murs", "category": "Peinture", "unit": "m²", "price": 8, "for": ["painter", "general"]},
    {"name": "Sous-couche impression", "category": "Peinture", "unit": "m²", "price": 10, "for": ["painter", "general"]},
    {"name": "Décapage peinture", "category": "Peinture", "unit": "m²", "price": 25, "for": ["painter", "general"]},
    {"name": "Pose papier peint", "category": "Peinture", "unit": "m²", "price": 28, "for": ["painter", "general"]},
    {"name": "Dépose papier peint", "category": "Peinture", "unit": "m²", "price": 12, "for": ["painter", "general"]},
    {"name": "Pose toile de verre", "category": "Peinture", "unit": "m²", "price": 18, "for": ["painter", "general"]},
    {"name": "Effet béton ciré", "category": "Peinture", "unit": "m²", "price": 75, "for": ["painter", "general"]},
    {"name": "Effet stucco", "category": "Peinture", "unit": "m²", "price": 85, "for": ["painter", "general"]},
    {"name": "Lasure bois extérieur", "category": "Peinture", "unit": "m²", "price": 22, "for": ["painter", "general"]},
    {"name": "Traitement anti-mousse", "category": "Peinture", "unit": "m²", "price": 8, "for": ["painter", "general"]},
    {"name": "Application hydrofuge", "category": "Peinture", "unit": "m²", "price": 15, "for": ["painter", "general"]},
    {"name": "Ravalement façade complet", "category": "Peinture", "unit": "m²", "price": 75, "for": ["painter", "general"]},
    {"name": "Nettoyage façade", "category": "Peinture", "unit": "m²", "price": 18, "for": ["painter", "general"]},
    {"name": "Réparation fissures façade", "category": "Peinture", "unit": "ml", "price": 45, "for": ["painter", "general"]},
    {"name": "Patine meuble", "category": "Peinture", "unit": "unité", "price": 150, "for": ["painter", "general"]},
    {"name": "Laquage meuble", "category": "Peinture", "unit": "unité", "price": 180, "for": ["painter", "general"]},
    {"name": "Peinture cage d'escalier", "category": "Peinture", "unit": "m²", "price": 35, "for": ["painter", "general"]},
    {"name": "Peinture sol", "category": "Peinture", "unit": "m²", "price": 35, "for": ["painter", "general"]},
    {"name": "Protection chantier", "category": "Peinture", "unit": "forfait", "price": 150, "for": ["painter", "general"]},

    # ========== RÉSEAUX & COURANTS FAIBLES (25 articles) ==========
    {"name": "Installation prise RJ45", "category": "Réseaux & Courants Faibles", "unit": "unité", "price": 85, "for": ["network_installer", "electrician", "general"]},
    {"name": "Tirage câble réseau cat.6", "category": "Réseaux & Courants Faibles", "unit": "ml", "price": 25, "for": ["network_installer", "electrician", "general"]},
    {"name": "Tirage fibre optique", "category": "Réseaux & Courants Faibles", "unit": "ml", "price": 35, "for": ["network_installer", "general"]},
    {"name": "Installation baie de brassage", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 650, "for": ["network_installer", "general"]},
    {"name": "Installation switch réseau", "category": "Réseaux & Courants Faibles", "unit": "unité", "price": 180, "for": ["network_installer", "general"]},
    {"name": "Installation routeur/box", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 120, "for": ["network_installer", "general"]},
    {"name": "Configuration WiFi professionnel", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 180, "for": ["network_installer", "general"]},
    {"name": "Installation borne WiFi", "category": "Réseaux & Courants Faibles", "unit": "unité", "price": 250, "for": ["network_installer", "general"]},
    {"name": "Installation caméra IP", "category": "Réseaux & Courants Faibles", "unit": "unité", "price": 280, "for": ["network_installer", "electrician", "general"]},
    {"name": "Installation système alarme", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 650, "for": ["network_installer", "electrician", "general"]},
    {"name": "Installation interphone", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 350, "for": ["network_installer", "electrician", "general"]},
    {"name": "Installation visiophone", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 550, "for": ["network_installer", "electrician", "general"]},
    {"name": "Installation contrôle d'accès", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 850, "for": ["network_installer", "general"]},
    {"name": "Installation NAS/Serveur", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 450, "for": ["network_installer", "general"]},
    {"name": "Installation onduleur", "category": "Réseaux & Courants Faibles", "unit": "unité", "price": 250, "for": ["network_installer", "electrician", "general"]},
    {"name": "Test certification câblage", "category": "Réseaux & Courants Faibles", "unit": "prise", "price": 25, "for": ["network_installer", "general"]},
    {"name": "Configuration VPN", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 250, "for": ["network_installer", "general"]},
    {"name": "Installation antenne TV/SAT", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 280, "for": ["network_installer", "electrician", "general"]},
    {"name": "Câblage téléphonique", "category": "Réseaux & Courants Faibles", "unit": "unité", "price": 65, "for": ["network_installer", "electrician", "general"]},
    {"name": "Installation écran/projecteur", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 350, "for": ["network_installer", "general"]},
    {"name": "Passage câble coaxial", "category": "Réseaux & Courants Faibles", "unit": "ml", "price": 18, "for": ["network_installer", "electrician", "general"]},
    {"name": "Installation domotique", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 850, "for": ["network_installer", "electrician", "general"]},
    {"name": "Maintenance réseau", "category": "Réseaux & Courants Faibles", "unit": "heure", "price": 65, "for": ["network_installer", "general"]},
    {"name": "Dépannage informatique", "category": "Réseaux & Courants Faibles", "unit": "heure", "price": 55, "for": ["network_installer", "general"]},
    {"name": "Audit réseau", "category": "Réseaux & Courants Faibles", "unit": "forfait", "price": 350, "for": ["network_installer", "general"]},

    # ========== MAÇONNERIE (20 articles) ==========
    {"name": "Coulage dalle béton", "category": "Maçonnerie", "unit": "m²", "price": 85, "for": ["general"]},
    {"name": "Montage mur parpaings", "category": "Maçonnerie", "unit": "m²", "price": 75, "for": ["general"]},
    {"name": "Montage mur briques", "category": "Maçonnerie", "unit": "m²", "price": 95, "for": ["general"]},
    {"name": "Chape ciment", "category": "Maçonnerie", "unit": "m²", "price": 32, "for": ["general"]},
    {"name": "Ragréage sol", "category": "Maçonnerie", "unit": "m²", "price": 22, "for": ["general"]},
    {"name": "Enduit façade monocouche", "category": "Maçonnerie", "unit": "m²", "price": 48, "for": ["general"]},
    {"name": "Ouverture mur porteur", "category": "Maçonnerie", "unit": "forfait", "price": 2500, "for": ["general"]},
    {"name": "Démolition cloison", "category": "Maçonnerie", "unit": "m²", "price": 35, "for": ["general"]},
    {"name": "Linteau béton", "category": "Maçonnerie", "unit": "ml", "price": 85, "for": ["general"]},
    {"name": "Chaînage béton", "category": "Maçonnerie", "unit": "ml", "price": 65, "for": ["general"]},
    {"name": "Pose appui fenêtre", "category": "Maçonnerie", "unit": "ml", "price": 65, "for": ["general"]},
    {"name": "Seuil de porte", "category": "Maçonnerie", "unit": "unité", "price": 120, "for": ["general"]},
    {"name": "Rebouchage saignées", "category": "Maçonnerie", "unit": "ml", "price": 18, "for": ["general"]},
    {"name": "Reprise maçonnerie", "category": "Maçonnerie", "unit": "m²", "price": 95, "for": ["general"]},
    {"name": "Scellement chimique", "category": "Maçonnerie", "unit": "unité", "price": 45, "for": ["general"]},
    {"name": "Évacuation gravats", "category": "Maçonnerie", "unit": "m³", "price": 85, "for": ["general"]},
    {"name": "Location benne", "category": "Maçonnerie", "unit": "jour", "price": 150, "for": ["general"]},
    {"name": "Création terrasse", "category": "Maçonnerie", "unit": "m²", "price": 120, "for": ["general"]},
    {"name": "Pose bordures", "category": "Maçonnerie", "unit": "ml", "price": 35, "for": ["general"]},
    {"name": "Création escalier béton", "category": "Maçonnerie", "unit": "forfait", "price": 2800, "for": ["general"]},

    # ========== MENUISERIE (15 articles) ==========
    {"name": "Pose porte intérieure", "category": "Menuiserie", "unit": "unité", "price": 450, "for": ["general"]},
    {"name": "Pose porte blindée", "category": "Menuiserie", "unit": "unité", "price": 1200, "for": ["general"]},
    {"name": "Pose fenêtre PVC", "category": "Menuiserie", "unit": "unité", "price": 650, "for": ["general"]},
    {"name": "Pose fenêtre alu", "category": "Menuiserie", "unit": "unité", "price": 850, "for": ["general"]},
    {"name": "Pose baie vitrée", "category": "Menuiserie", "unit": "unité", "price": 1200, "for": ["general"]},
    {"name": "Pose volet roulant", "category": "Menuiserie", "unit": "unité", "price": 550, "for": ["general"]},
    {"name": "Installation cuisine", "category": "Menuiserie", "unit": "ml", "price": 180, "for": ["general"]},
    {"name": "Création placard", "category": "Menuiserie", "unit": "forfait", "price": 950, "for": ["general"]},
    {"name": "Pose parquet flottant", "category": "Menuiserie", "unit": "m²", "price": 35, "for": ["general"]},
    {"name": "Pose parquet massif collé", "category": "Menuiserie", "unit": "m²", "price": 65, "for": ["general"]},
    {"name": "Ponçage parquet", "category": "Menuiserie", "unit": "m²", "price": 28, "for": ["general"]},
    {"name": "Vitrification parquet", "category": "Menuiserie", "unit": "m²", "price": 22, "for": ["general"]},
    {"name": "Pose plinthes", "category": "Menuiserie", "unit": "ml", "price": 15, "for": ["general"]},
    {"name": "Pose escalier bois", "category": "Menuiserie", "unit": "forfait", "price": 2500, "for": ["general"]},
    {"name": "Habillage escalier", "category": "Menuiserie", "unit": "marche", "price": 120, "for": ["general"]},

    # ========== CARRELAGE (12 articles) ==========
    {"name": "Pose carrelage sol", "category": "Carrelage", "unit": "m²", "price": 45, "for": ["general"]},
    {"name": "Pose carrelage mural", "category": "Carrelage", "unit": "m²", "price": 50, "for": ["general"]},
    {"name": "Pose faïence", "category": "Carrelage", "unit": "m²", "price": 55, "for": ["general"]},
    {"name": "Pose mosaïque", "category": "Carrelage", "unit": "m²", "price": 75, "for": ["general"]},
    {"name": "Dépose carrelage", "category": "Carrelage", "unit": "m²", "price": 22, "for": ["general"]},
    {"name": "Ragréage avant carrelage", "category": "Carrelage", "unit": "m²", "price": 18, "for": ["general"]},
    {"name": "Pose receveur à carreler", "category": "Carrelage", "unit": "forfait", "price": 450, "for": ["general"]},
    {"name": "Pose carrelage grand format", "category": "Carrelage", "unit": "m²", "price": 65, "for": ["general"]},
    {"name": "Pose plinthes carrelage", "category": "Carrelage", "unit": "ml", "price": 18, "for": ["general"]},
    {"name": "Joint carrelage", "category": "Carrelage", "unit": "m²", "price": 12, "for": ["general"]},
    {"name": "Réparation carrelage", "category": "Carrelage", "unit": "unité", "price": 45, "for": ["general"]},
    {"name": "Pose carrelage terrasse", "category": "Carrelage", "unit": "m²", "price": 55, "for": ["general"]},

    # ========== PLÂTRERIE / ISOLATION (15 articles) ==========
    {"name": "Pose placo BA13", "category": "Plâtrerie / Isolation", "unit": "m²", "price": 28, "for": ["general"]},
    {"name": "Pose placo hydrofuge", "category": "Plâtrerie / Isolation", "unit": "m²", "price": 35, "for": ["general"]},
    {"name": "Pose faux plafond", "category": "Plâtrerie / Isolation", "unit": "m²", "price": 45, "for": ["general"]},
    {"name": "Cloison placo", "category": "Plâtrerie / Isolation", "unit": "m²", "price": 55, "for": ["general"]},
    {"name": "Doublage isolant", "category": "Plâtrerie / Isolation", "unit": "m²", "price": 45, "for": ["general"]},
    {"name": "Isolation combles", "category": "Plâtrerie / Isolation", "unit": "m²", "price": 35, "for": ["general"]},
    {"name": "Isolation murs", "category": "Plâtrerie / Isolation", "unit": "m²", "price": 40, "for": ["general"]},
    {"name": "Bandes à joints", "category": "Plâtrerie / Isolation", "unit": "m²", "price": 12, "for": ["general"]},
    {"name": "Enduit plâtre", "category": "Plâtrerie / Isolation", "unit": "m²", "price": 35, "for": ["general"]},
    {"name": "Coffrage technique", "category": "Plâtrerie / Isolation", "unit": "ml", "price": 65, "for": ["general"]},
    {"name": "Niche murale", "category": "Plâtrerie / Isolation", "unit": "unité", "price": 180, "for": ["general"]},
    {"name": "Trappe de visite", "category": "Plâtrerie / Isolation", "unit": "unité", "price": 85, "for": ["general"]},
    {"name": "Corniche décorative", "category": "Plâtrerie / Isolation", "unit": "ml", "price": 25, "for": ["general"]},
    {"name": "Habillage poutre", "category": "Plâtrerie / Isolation", "unit": "ml", "price": 55, "for": ["general"]},
    {"name": "ITE (isolation extérieure)", "category": "Plâtrerie / Isolation", "unit": "m²", "price": 120, "for": ["general"]},

    # ========== RÉNOVATION GÉNÉRALE (15 articles) ==========
    {"name": "Démolition cloison légère", "category": "Rénovation générale", "unit": "m²", "price": 25, "for": ["general"]},
    {"name": "Dépose revêtement sol", "category": "Rénovation générale", "unit": "m²", "price": 15, "for": ["general"]},
    {"name": "Nettoyage fin de chantier", "category": "Rénovation générale", "unit": "m²", "price": 8, "for": ["general"]},
    {"name": "Protection chantier", "category": "Rénovation générale", "unit": "forfait", "price": 150, "for": ["general"]},
    {"name": "Étude technique", "category": "Rénovation générale", "unit": "forfait", "price": 250, "for": ["general"]},
    {"name": "Relevé de cotes", "category": "Rénovation générale", "unit": "forfait", "price": 180, "for": ["general"]},
    {"name": "Suivi de chantier", "category": "Rénovation générale", "unit": "heure", "price": 65, "for": ["general"]},
    {"name": "Coordination travaux", "category": "Rénovation générale", "unit": "jour", "price": 350, "for": ["general"]},
    {"name": "Fournitures diverses", "category": "Rénovation générale", "unit": "forfait", "price": 100, "for": ["general"]},
    {"name": "Transport matériaux", "category": "Rénovation générale", "unit": "forfait", "price": 150, "for": ["general"]},
    {"name": "Location échafaudage", "category": "Rénovation générale", "unit": "jour", "price": 85, "for": ["general"]},
    {"name": "Location nacelle", "category": "Rénovation générale", "unit": "jour", "price": 250, "for": ["general"]},
    {"name": "Diagnostic amiante", "category": "Rénovation générale", "unit": "forfait", "price": 350, "for": ["general"]},
    {"name": "Diagnostic plomb", "category": "Rénovation générale", "unit": "forfait", "price": 250, "for": ["general"]},
    {"name": "Désamiantage", "category": "Rénovation générale", "unit": "m²", "price": 150, "for": ["general"]},

    # ========== MAIN D'ŒUVRE (8 articles) ==========
    {"name": "Main d'œuvre qualifiée", "category": "Main d'œuvre", "unit": "heure", "price": 45, "for": ["general", "electrician", "plumber", "painter", "network_installer"]},
    {"name": "Main d'œuvre aide", "category": "Main d'œuvre", "unit": "heure", "price": 32, "for": ["general", "electrician", "plumber", "painter", "network_installer"]},
    {"name": "Heures supplémentaires", "category": "Main d'œuvre", "unit": "heure", "price": 55, "for": ["general", "electrician", "plumber", "painter", "network_installer"]},
    {"name": "Travail weekend", "category": "Main d'œuvre", "unit": "heure", "price": 65, "for": ["general", "electrician", "plumber", "painter", "network_installer"]},
    {"name": "Déplacement zone 1", "category": "Main d'œuvre", "unit": "forfait", "price": 35, "for": ["general", "electrician", "plumber", "painter", "network_installer"]},
    {"name": "Déplacement zone 2", "category": "Main d'œuvre", "unit": "forfait", "price": 55, "for": ["general", "electrician", "plumber", "painter", "network_installer"]},
    {"name": "Déplacement zone 3", "category": "Main d'œuvre", "unit": "forfait", "price": 85, "for": ["general", "electrician", "plumber", "painter", "network_installer"]},
    {"name": "Forfait intervention", "category": "Main d'œuvre", "unit": "forfait", "price": 50, "for": ["general", "electrician", "plumber", "painter", "network_installer"]},
]


# ============== SERVICE CLASS ==============

class SimplifiedArticleService:
    """Simplified service for managing articles (Category -> Article, no subcategories)"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.articles = db.simplified_articles
        self.categories = db.simplified_categories
    
    async def init_indexes(self) -> None:
        """Create necessary indexes"""
        try:
            await self.articles.create_index("category")
            await self.articles.create_index("recommended_for")
            await self.articles.create_index([("category", 1), ("name", 1)])
            await self.categories.create_index("name", unique=True)
            logger.info("Simplified article service indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def seed_all(self, force: bool = False) -> Dict[str, int]:
        """Seed all articles"""
        stats = {"categories": 0, "articles": 0, "skipped": False}
        
        existing = await self.articles.count_documents({})
        if existing > 0 and not force:
            logger.info(f"Articles already seeded ({existing} found). Skipping.")
            stats["skipped"] = True
            return stats
        
        if force:
            await self.articles.delete_many({})
            await self.categories.delete_many({})
            logger.info("Force reseed: cleared existing simplified articles")
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Seed categories
        for cat_name in CATEGORIES:
            try:
                await self.categories.insert_one({
                    "id": str(uuid.uuid4()),
                    "name": cat_name,
                    "created_at": now
                })
                stats["categories"] += 1
            except Exception as e:
                logger.warning(f"Category {cat_name} already exists or error: {e}")
        
        # Seed articles
        for article in ARTICLES_LIBRARY:
            article_doc = {
                "id": str(uuid.uuid4()),
                "name": article["name"],
                "category": article["category"],
                "default_unit": article["unit"],
                "suggested_price": article["price"],
                "recommended_for": article["for"],
                "created_at": now
            }
            await self.articles.insert_one(article_doc)
            stats["articles"] += 1
        
        logger.info(f"Seeded {stats['categories']} categories and {stats['articles']} articles")
        return stats
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories"""
        categories = []
        cursor = self.categories.find({}).sort("name", 1)
        async for doc in cursor:
            doc.pop("_id", None)
            categories.append(doc)
        return categories
    
    async def get_articles(
        self, 
        business_type: str = "general",
        category: Optional[str] = None,
        show_all: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get articles filtered by business_type and category.
        
        If show_all=False: only show articles where business_type is in recommended_for
        If show_all=True: show ALL articles
        """
        query = {}
        
        if category:
            query["category"] = category
        
        if not show_all and business_type != "general":
            # Filter by recommended_for
            query["recommended_for"] = {"$in": [business_type, "general"]}
        
        articles = []
        cursor = self.articles.find(query).sort([("category", 1), ("name", 1)])
        
        async for doc in cursor:
            doc.pop("_id", None)
            # Add is_recommended flag for UI highlighting
            doc["is_recommended"] = business_type in doc.get("recommended_for", [])
            articles.append(doc)
        
        return articles
    
    async def get_articles_by_category(
        self,
        category: str,
        business_type: str = "general",
        show_all: bool = False
    ) -> List[Dict[str, Any]]:
        """Get articles for a specific category"""
        return await self.get_articles(
            business_type=business_type,
            category=category,
            show_all=show_all
        )
    
    async def search_articles(self, query: str, business_type: str = "general", limit: int = 20) -> List[Dict[str, Any]]:
        """Search articles by name"""
        search_query = {
            "name": {"$regex": query, "$options": "i"}
        }
        
        if business_type != "general":
            search_query["recommended_for"] = {"$in": [business_type, "general"]}
        
        articles = []
        cursor = self.articles.find(search_query).limit(limit)
        
        async for doc in cursor:
            doc.pop("_id", None)
            doc["is_recommended"] = business_type in doc.get("recommended_for", [])
            articles.append(doc)
        
        return articles


def get_simplified_article_service(db: AsyncIOMotorDatabase) -> SimplifiedArticleService:
    """Factory function"""
    return SimplifiedArticleService(db)
