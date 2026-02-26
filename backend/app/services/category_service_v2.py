"""
Service Categories Management V2 for BTP Facture
Enhanced system with subcategories, suggested prices, and professional kits
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
import uuid

logger = logging.getLogger(__name__)

# ============== CONSTANTS ==============

VALID_BUSINESS_TYPES = [
    "general",
    "electrician", 
    "plumber",
    "mason",
    "painter",
    "carpenter",
    "it_installer"
]

BUSINESS_TYPE_LABELS = {
    "general": "Général / Multi-corps",
    "electrician": "Électricien",
    "plumber": "Plombier",
    "mason": "Maçon",
    "painter": "Peintre",
    "carpenter": "Menuisier",
    "it_installer": "Installateur réseaux / IT"
}

# ============== MODELS ==============

class ServiceCategory(BaseModel):
    id: str
    name: str
    business_types: List[str]
    icon: Optional[str] = None
    created_at: str


class ServiceSubcategory(BaseModel):
    id: str
    category_id: str
    name: str
    created_at: str


class SuggestedPrices(BaseModel):
    electrician: Optional[float] = None
    plumber: Optional[float] = None
    mason: Optional[float] = None
    painter: Optional[float] = None
    carpenter: Optional[float] = None
    it_installer: Optional[float] = None
    general: Optional[float] = None


class ServiceItem(BaseModel):
    id: str
    category_id: str
    subcategory_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    unit: Optional[str] = None
    default_price: Optional[float] = None
    suggested_prices: Optional[Dict[str, float]] = None
    created_at: str


class ServiceKitItem(BaseModel):
    service_item_id: str
    quantity: float = 1


class ServiceKit(BaseModel):
    id: str
    name: str
    business_type: str
    description: Optional[str] = None
    items: List[ServiceKitItem]
    created_at: str


# ============== SEED DATA V2 ==============

SEED_CATEGORIES_V2 = [
    {
        "name": "Électricité",
        "business_types": ["electrician", "general"],
        "icon": "Zap",
        "subcategories": ["Installation", "Rénovation", "Dépannage", "Mise aux normes"]
    },
    {
        "name": "Réseaux & Courants Faibles",
        "business_types": ["electrician", "it_installer", "general"],
        "icon": "Network",
        "subcategories": ["Câblage", "Sécurité", "Infrastructure", "Configuration"]
    },
    {
        "name": "Plomberie",
        "business_types": ["plumber", "general"],
        "icon": "Droplets",
        "subcategories": ["Installation", "Dépannage", "Salle de bain", "Chauffage"]
    },
    {
        "name": "Maçonnerie",
        "business_types": ["mason", "general"],
        "icon": "Blocks",
        "subcategories": ["Gros œuvre", "Second œuvre", "Extérieur", "Rénovation"]
    },
    {
        "name": "Peinture",
        "business_types": ["painter", "general"],
        "icon": "Paintbrush",
        "subcategories": ["Intérieur", "Extérieur", "Préparation", "Décoration"]
    },
    {
        "name": "Menuiserie",
        "business_types": ["carpenter", "general"],
        "icon": "Hammer",
        "subcategories": ["Portes & Fenêtres", "Aménagement", "Parquet", "Sur mesure"]
    },
    {
        "name": "Rénovation générale",
        "business_types": ["general"],
        "icon": "Home",
        "subcategories": ["Démolition", "Main d'œuvre", "Études", "Divers"]
    },
]

# Service items with subcategory and suggested prices
SEED_ITEMS_V2 = {
    "Électricité": {
        "Installation": [
            {
                "name": "Installation prise électrique",
                "description": "Pose prise 16A avec encastrement",
                "unit": "unité",
                "default_price": 65,
                "suggested_prices": {"electrician": 55, "general": 70}
            },
            {
                "name": "Installation interrupteur",
                "description": "Pose interrupteur simple ou va-et-vient",
                "unit": "unité",
                "default_price": 55,
                "suggested_prices": {"electrician": 45, "general": 60}
            },
            {
                "name": "Pose luminaire plafonnier",
                "description": "Installation point lumineux avec raccordement",
                "unit": "unité",
                "default_price": 75,
                "suggested_prices": {"electrician": 65, "general": 85}
            },
            {
                "name": "Installation spot encastré",
                "description": "Pose spot LED encastré avec transformateur",
                "unit": "unité",
                "default_price": 45,
                "suggested_prices": {"electrician": 38, "general": 50}
            },
            {
                "name": "Pose prise spécialisée 32A",
                "description": "Installation prise four/plaque cuisson",
                "unit": "unité",
                "default_price": 95,
                "suggested_prices": {"electrician": 80, "general": 110}
            },
        ],
        "Rénovation": [
            {
                "name": "Remplacement tableau électrique",
                "description": "Dépose ancien + pose nouveau tableau",
                "unit": "forfait",
                "default_price": 850,
                "suggested_prices": {"electrician": 750, "general": 950}
            },
            {
                "name": "Tirage de câble",
                "description": "Passage câble électrique sous gaine",
                "unit": "ml",
                "default_price": 15,
                "suggested_prices": {"electrician": 12, "general": 18}
            },
            {
                "name": "Remplacement disjoncteur",
                "description": "Fourniture et pose disjoncteur modulaire",
                "unit": "unité",
                "default_price": 85,
                "suggested_prices": {"electrician": 70, "general": 95}
            },
            {
                "name": "Rénovation circuit électrique",
                "description": "Mise à niveau circuit complet",
                "unit": "forfait",
                "default_price": 450,
                "suggested_prices": {"electrician": 380, "general": 520}
            },
            {
                "name": "Pose goulotte électrique",
                "description": "Installation goulotte apparente",
                "unit": "ml",
                "default_price": 22,
                "suggested_prices": {"electrician": 18, "general": 25}
            },
        ],
        "Dépannage": [
            {
                "name": "Recherche de panne",
                "description": "Diagnostic et localisation défaut électrique",
                "unit": "forfait",
                "default_price": 95,
                "suggested_prices": {"electrician": 80, "general": 110}
            },
            {
                "name": "Remplacement prise défectueuse",
                "description": "Dépose + pose nouvelle prise",
                "unit": "unité",
                "default_price": 75,
                "suggested_prices": {"electrician": 60, "general": 85}
            },
            {
                "name": "Réparation court-circuit",
                "description": "Identification et réparation court-circuit",
                "unit": "forfait",
                "default_price": 150,
                "suggested_prices": {"electrician": 120, "general": 180}
            },
            {
                "name": "Remplacement interrupteur différentiel",
                "description": "Fourniture et pose différentiel 30mA",
                "unit": "unité",
                "default_price": 180,
                "suggested_prices": {"electrician": 150, "general": 210}
            },
            {
                "name": "Intervention urgente",
                "description": "Dépannage électrique urgent",
                "unit": "forfait",
                "default_price": 180,
                "suggested_prices": {"electrician": 150, "general": 220}
            },
        ],
        "Mise aux normes": [
            {
                "name": "Mise aux normes NF C 15-100",
                "description": "Mise en conformité installation complète",
                "unit": "forfait",
                "default_price": 1200,
                "suggested_prices": {"electrician": 1000, "general": 1400}
            },
            {
                "name": "Installation parafoudre",
                "description": "Pose parafoudre tableau électrique",
                "unit": "unité",
                "default_price": 250,
                "suggested_prices": {"electrician": 200, "general": 300}
            },
            {
                "name": "Mise à la terre",
                "description": "Création ou reprise terre + barrette",
                "unit": "forfait",
                "default_price": 350,
                "suggested_prices": {"electrician": 280, "general": 420}
            },
            {
                "name": "Diagnostic électrique",
                "description": "Contrôle conformité avec rapport",
                "unit": "forfait",
                "default_price": 150,
                "suggested_prices": {"electrician": 120, "general": 180}
            },
            {
                "name": "Équipotentialité salle de bain",
                "description": "Liaison équipotentielle supplémentaire",
                "unit": "forfait",
                "default_price": 180,
                "suggested_prices": {"electrician": 150, "general": 220}
            },
        ],
    },
    "Réseaux & Courants Faibles": {
        "Câblage": [
            {
                "name": "Installation prise RJ45",
                "description": "Pose prise réseau cat.6 avec test",
                "unit": "unité",
                "default_price": 85,
                "suggested_prices": {"it_installer": 70, "electrician": 80, "general": 95}
            },
            {
                "name": "Tirage câble réseau",
                "description": "Passage câble cat.6 sous gaine",
                "unit": "ml",
                "default_price": 25,
                "suggested_prices": {"it_installer": 20, "electrician": 22, "general": 30}
            },
            {
                "name": "Pose fibre optique interne",
                "description": "Tirage fibre + soudure connecteurs",
                "unit": "ml",
                "default_price": 35,
                "suggested_prices": {"it_installer": 28, "electrician": 32, "general": 42}
            },
            {
                "name": "Câblage téléphonique",
                "description": "Installation ligne téléphonique RJ11",
                "unit": "unité",
                "default_price": 65,
                "suggested_prices": {"it_installer": 55, "electrician": 60, "general": 75}
            },
            {
                "name": "Câblage coaxial TV",
                "description": "Tirage câble coaxial + connecteurs F",
                "unit": "ml",
                "default_price": 18,
                "suggested_prices": {"it_installer": 15, "electrician": 16, "general": 22}
            },
        ],
        "Sécurité": [
            {
                "name": "Installation caméra IP",
                "description": "Pose caméra + configuration réseau",
                "unit": "unité",
                "default_price": 250,
                "suggested_prices": {"it_installer": 200, "electrician": 230, "general": 300}
            },
            {
                "name": "Installation système alarme",
                "description": "Pose alarme sans fil complète",
                "unit": "forfait",
                "default_price": 450,
                "suggested_prices": {"it_installer": 380, "electrician": 420, "general": 550}
            },
            {
                "name": "Installation interphone",
                "description": "Pose interphone audio 2 fils",
                "unit": "forfait",
                "default_price": 280,
                "suggested_prices": {"it_installer": 230, "electrician": 260, "general": 340}
            },
            {
                "name": "Installation visiophone",
                "description": "Pose visiophone couleur + gâche",
                "unit": "forfait",
                "default_price": 450,
                "suggested_prices": {"it_installer": 380, "electrician": 420, "general": 550}
            },
            {
                "name": "Installation contrôle d'accès",
                "description": "Pose badge/digicode + gâche électrique",
                "unit": "forfait",
                "default_price": 650,
                "suggested_prices": {"it_installer": 550, "electrician": 600, "general": 780}
            },
        ],
        "Infrastructure": [
            {
                "name": "Installation baie de brassage",
                "description": "Pose baie 19 pouces équipée",
                "unit": "forfait",
                "default_price": 650,
                "suggested_prices": {"it_installer": 520, "electrician": 600, "general": 780}
            },
            {
                "name": "Installation switch réseau",
                "description": "Pose et configuration switch manageable",
                "unit": "unité",
                "default_price": 180,
                "suggested_prices": {"it_installer": 140, "electrician": 170, "general": 220}
            },
            {
                "name": "Installation NAS/Serveur",
                "description": "Mise en place serveur de fichiers",
                "unit": "forfait",
                "default_price": 350,
                "suggested_prices": {"it_installer": 280, "electrician": 330, "general": 420}
            },
            {
                "name": "Installation antenne TV/SAT",
                "description": "Pose antenne + réglage orientation",
                "unit": "forfait",
                "default_price": 220,
                "suggested_prices": {"it_installer": 180, "electrician": 200, "general": 270}
            },
            {
                "name": "Installation onduleur",
                "description": "Pose et configuration UPS",
                "unit": "unité",
                "default_price": 180,
                "suggested_prices": {"it_installer": 140, "electrician": 160, "general": 220}
            },
        ],
        "Configuration": [
            {
                "name": "Configuration routeur/box",
                "description": "Paramétrage complet routeur internet",
                "unit": "forfait",
                "default_price": 95,
                "suggested_prices": {"it_installer": 75, "electrician": 90, "general": 120}
            },
            {
                "name": "Configuration réseau WiFi",
                "description": "Installation et sécurisation WiFi",
                "unit": "forfait",
                "default_price": 120,
                "suggested_prices": {"it_installer": 95, "electrician": 110, "general": 150}
            },
            {
                "name": "Configuration borne WiFi pro",
                "description": "Paramétrage point d'accès entreprise",
                "unit": "unité",
                "default_price": 150,
                "suggested_prices": {"it_installer": 120, "electrician": 140, "general": 180}
            },
            {
                "name": "Test et certification câblage",
                "description": "Test Fluke avec rapport certification",
                "unit": "prise",
                "default_price": 25,
                "suggested_prices": {"it_installer": 18, "electrician": 22, "general": 30}
            },
            {
                "name": "Configuration VPN",
                "description": "Mise en place accès distant sécurisé",
                "unit": "forfait",
                "default_price": 180,
                "suggested_prices": {"it_installer": 140, "electrician": 170, "general": 220}
            },
        ],
    },
    "Plomberie": {
        "Installation": [
            {
                "name": "Installation WC suspendu",
                "description": "Pose WC suspendu avec bâti-support",
                "unit": "forfait",
                "default_price": 650,
                "suggested_prices": {"plumber": 550, "general": 750}
            },
            {
                "name": "Installation WC classique",
                "description": "Pose WC à poser avec raccordement",
                "unit": "forfait",
                "default_price": 280,
                "suggested_prices": {"plumber": 230, "general": 340}
            },
            {
                "name": "Installation lavabo",
                "description": "Pose lavabo avec robinetterie",
                "unit": "forfait",
                "default_price": 320,
                "suggested_prices": {"plumber": 260, "general": 380}
            },
            {
                "name": "Installation meuble vasque",
                "description": "Pose meuble + vasque + robinetterie",
                "unit": "forfait",
                "default_price": 450,
                "suggested_prices": {"plumber": 380, "general": 550}
            },
            {
                "name": "Installation évier cuisine",
                "description": "Pose évier + mitigeur + raccordement",
                "unit": "forfait",
                "default_price": 280,
                "suggested_prices": {"plumber": 230, "general": 340}
            },
        ],
        "Dépannage": [
            {
                "name": "Recherche de fuite",
                "description": "Diagnostic et localisation fuite",
                "unit": "forfait",
                "default_price": 120,
                "suggested_prices": {"plumber": 95, "general": 150}
            },
            {
                "name": "Réparation fuite apparente",
                "description": "Réparation fuite visible accessible",
                "unit": "forfait",
                "default_price": 95,
                "suggested_prices": {"plumber": 75, "general": 120}
            },
            {
                "name": "Débouchage canalisation",
                "description": "Débouchage furet ou ventouse",
                "unit": "forfait",
                "default_price": 120,
                "suggested_prices": {"plumber": 95, "general": 150}
            },
            {
                "name": "Débouchage haute pression",
                "description": "Débouchage hydrocurage professionnel",
                "unit": "forfait",
                "default_price": 250,
                "suggested_prices": {"plumber": 200, "general": 300}
            },
            {
                "name": "Remplacement robinet",
                "description": "Fourniture et pose robinet/mitigeur",
                "unit": "unité",
                "default_price": 150,
                "suggested_prices": {"plumber": 120, "general": 180}
            },
        ],
        "Salle de bain": [
            {
                "name": "Installation douche italienne",
                "description": "Création douche à l'italienne complète",
                "unit": "forfait",
                "default_price": 1800,
                "suggested_prices": {"plumber": 1500, "general": 2200}
            },
            {
                "name": "Installation receveur douche",
                "description": "Pose receveur + paroi + mitigeur",
                "unit": "forfait",
                "default_price": 850,
                "suggested_prices": {"plumber": 700, "general": 1000}
            },
            {
                "name": "Installation baignoire",
                "description": "Pose baignoire + robinetterie",
                "unit": "forfait",
                "default_price": 650,
                "suggested_prices": {"plumber": 550, "general": 780}
            },
            {
                "name": "Remplacement colonne douche",
                "description": "Dépose + pose colonne thermostatique",
                "unit": "forfait",
                "default_price": 380,
                "suggested_prices": {"plumber": 300, "general": 450}
            },
            {
                "name": "Installation sèche-serviettes",
                "description": "Pose radiateur sèche-serviettes électrique",
                "unit": "forfait",
                "default_price": 280,
                "suggested_prices": {"plumber": 220, "general": 340}
            },
        ],
        "Chauffage": [
            {
                "name": "Installation chauffe-eau électrique",
                "description": "Pose cumulus électrique avec raccordement",
                "unit": "forfait",
                "default_price": 450,
                "suggested_prices": {"plumber": 380, "general": 550}
            },
            {
                "name": "Installation chauffe-eau thermodynamique",
                "description": "Pose ballon thermodynamique",
                "unit": "forfait",
                "default_price": 850,
                "suggested_prices": {"plumber": 700, "general": 1000}
            },
            {
                "name": "Remplacement radiateur",
                "description": "Dépose + pose radiateur acier/alu",
                "unit": "unité",
                "default_price": 250,
                "suggested_prices": {"plumber": 200, "general": 300}
            },
            {
                "name": "Purge circuit chauffage",
                "description": "Purge complète installation",
                "unit": "forfait",
                "default_price": 120,
                "suggested_prices": {"plumber": 95, "general": 150}
            },
            {
                "name": "Désembouage radiateurs",
                "description": "Nettoyage circuit chauffage",
                "unit": "forfait",
                "default_price": 450,
                "suggested_prices": {"plumber": 380, "general": 550}
            },
        ],
    },
    "Maçonnerie": {
        "Gros œuvre": [
            {
                "name": "Coulage dalle béton",
                "description": "Dalle béton armé épaisseur 10-15cm",
                "unit": "m²",
                "default_price": 85,
                "suggested_prices": {"mason": 70, "general": 100}
            },
            {
                "name": "Montage mur parpaings",
                "description": "Construction mur parpaings 20cm",
                "unit": "m²",
                "default_price": 75,
                "suggested_prices": {"mason": 60, "general": 90}
            },
            {
                "name": "Montage mur briques",
                "description": "Construction mur briques pleines",
                "unit": "m²",
                "default_price": 95,
                "suggested_prices": {"mason": 80, "general": 115}
            },
            {
                "name": "Chaînage béton armé",
                "description": "Réalisation chaînage horizontal/vertical",
                "unit": "ml",
                "default_price": 65,
                "suggested_prices": {"mason": 55, "general": 80}
            },
            {
                "name": "Linteau béton",
                "description": "Pose linteau préfabriqué ou coulé",
                "unit": "ml",
                "default_price": 85,
                "suggested_prices": {"mason": 70, "general": 100}
            },
        ],
        "Second œuvre": [
            {
                "name": "Enduit intérieur plâtre",
                "description": "Application enduit plâtre traditionnel",
                "unit": "m²",
                "default_price": 35,
                "suggested_prices": {"mason": 28, "general": 42}
            },
            {
                "name": "Chape ciment",
                "description": "Réalisation chape mortier 5cm",
                "unit": "m²",
                "default_price": 32,
                "suggested_prices": {"mason": 26, "general": 38}
            },
            {
                "name": "Ragréage sol",
                "description": "Ragréage autolissant P3",
                "unit": "m²",
                "default_price": 22,
                "suggested_prices": {"mason": 18, "general": 28}
            },
            {
                "name": "Montage cloison carreaux plâtre",
                "description": "Cloison carreaux plâtre 7cm",
                "unit": "m²",
                "default_price": 55,
                "suggested_prices": {"mason": 45, "general": 68}
            },
            {
                "name": "Scellement chimique",
                "description": "Fixation par scellement chimique",
                "unit": "unité",
                "default_price": 45,
                "suggested_prices": {"mason": 35, "general": 55}
            },
        ],
        "Extérieur": [
            {
                "name": "Enduit façade monocouche",
                "description": "Application enduit monocouche coloré",
                "unit": "m²",
                "default_price": 48,
                "suggested_prices": {"mason": 40, "general": 58}
            },
            {
                "name": "Ravalement façade complet",
                "description": "Nettoyage + rebouchage + enduit",
                "unit": "m²",
                "default_price": 75,
                "suggested_prices": {"mason": 62, "general": 90}
            },
            {
                "name": "Réparation fissures façade",
                "description": "Traitement fissures avec armature",
                "unit": "ml",
                "default_price": 45,
                "suggested_prices": {"mason": 38, "general": 55}
            },
            {
                "name": "Pose appui fenêtre béton",
                "description": "Fourniture et pose appui préfabriqué",
                "unit": "ml",
                "default_price": 65,
                "suggested_prices": {"mason": 55, "general": 80}
            },
            {
                "name": "Seuil de porte béton",
                "description": "Réalisation seuil béton lissé",
                "unit": "unité",
                "default_price": 120,
                "suggested_prices": {"mason": 100, "general": 145}
            },
        ],
        "Rénovation": [
            {
                "name": "Ouverture mur porteur",
                "description": "Création ouverture avec IPN",
                "unit": "forfait",
                "default_price": 2200,
                "suggested_prices": {"mason": 1800, "general": 2600}
            },
            {
                "name": "Démolition cloison",
                "description": "Démolition cloison non porteuse",
                "unit": "m²",
                "default_price": 35,
                "suggested_prices": {"mason": 28, "general": 42}
            },
            {
                "name": "Rebouchage passage gaines",
                "description": "Rebouchage saignées et passages",
                "unit": "ml",
                "default_price": 18,
                "suggested_prices": {"mason": 14, "general": 22}
            },
            {
                "name": "Reprise de maçonnerie",
                "description": "Réparation maçonnerie dégradée",
                "unit": "m²",
                "default_price": 95,
                "suggested_prices": {"mason": 78, "general": 115}
            },
            {
                "name": "Évacuation gravats",
                "description": "Chargement et évacuation déchets",
                "unit": "m³",
                "default_price": 85,
                "suggested_prices": {"mason": 70, "general": 100}
            },
        ],
    },
    "Peinture": {
        "Intérieur": [
            {
                "name": "Peinture mur",
                "description": "Application peinture acrylique 2 couches",
                "unit": "m²",
                "default_price": 28,
                "suggested_prices": {"painter": 22, "general": 35}
            },
            {
                "name": "Peinture plafond",
                "description": "Application peinture plafond mat",
                "unit": "m²",
                "default_price": 32,
                "suggested_prices": {"painter": 26, "general": 40}
            },
            {
                "name": "Peinture boiseries",
                "description": "Laque satinée portes/plinthes",
                "unit": "ml",
                "default_price": 18,
                "suggested_prices": {"painter": 14, "general": 22}
            },
            {
                "name": "Peinture porte",
                "description": "Peinture porte 2 faces avec huisserie",
                "unit": "unité",
                "default_price": 95,
                "suggested_prices": {"painter": 75, "general": 115}
            },
            {
                "name": "Peinture radiateur",
                "description": "Peinture spéciale haute température",
                "unit": "unité",
                "default_price": 65,
                "suggested_prices": {"painter": 50, "general": 80}
            },
        ],
        "Extérieur": [
            {
                "name": "Peinture façade",
                "description": "Peinture pliolite ou siloxane",
                "unit": "m²",
                "default_price": 25,
                "suggested_prices": {"painter": 20, "general": 32}
            },
            {
                "name": "Peinture volets bois",
                "description": "Décapage + peinture microporeuse",
                "unit": "m²",
                "default_price": 55,
                "suggested_prices": {"painter": 45, "general": 68}
            },
            {
                "name": "Peinture portail métal",
                "description": "Antirouille + laque glycéro",
                "unit": "m²",
                "default_price": 48,
                "suggested_prices": {"painter": 38, "general": 58}
            },
            {
                "name": "Lasure bois extérieur",
                "description": "Application lasure protection UV",
                "unit": "m²",
                "default_price": 22,
                "suggested_prices": {"painter": 18, "general": 28}
            },
            {
                "name": "Traitement anti-mousse",
                "description": "Pulvérisation produit fongicide",
                "unit": "m²",
                "default_price": 8,
                "suggested_prices": {"painter": 6, "general": 10}
            },
        ],
        "Préparation": [
            {
                "name": "Enduit de rebouchage",
                "description": "Rebouchage fissures et trous",
                "unit": "m²",
                "default_price": 12,
                "suggested_prices": {"painter": 9, "general": 15}
            },
            {
                "name": "Enduit de lissage",
                "description": "Application enduit lissage finition",
                "unit": "m²",
                "default_price": 18,
                "suggested_prices": {"painter": 14, "general": 22}
            },
            {
                "name": "Ponçage murs",
                "description": "Ponçage manuel ou mécanique",
                "unit": "m²",
                "default_price": 8,
                "suggested_prices": {"painter": 6, "general": 10}
            },
            {
                "name": "Sous-couche impression",
                "description": "Application primaire d'accrochage",
                "unit": "m²",
                "default_price": 10,
                "suggested_prices": {"painter": 8, "general": 12}
            },
            {
                "name": "Décapage peinture",
                "description": "Décapage chimique ou thermique",
                "unit": "m²",
                "default_price": 25,
                "suggested_prices": {"painter": 20, "general": 32}
            },
        ],
        "Décoration": [
            {
                "name": "Pose papier peint",
                "description": "Pose papier peint intissé",
                "unit": "m²",
                "default_price": 28,
                "suggested_prices": {"painter": 22, "general": 35}
            },
            {
                "name": "Pose toile de verre",
                "description": "Marouflage toile de verre",
                "unit": "m²",
                "default_price": 18,
                "suggested_prices": {"painter": 14, "general": 22}
            },
            {
                "name": "Effet décoratif",
                "description": "Application effet béton ciré/stucco",
                "unit": "m²",
                "default_price": 75,
                "suggested_prices": {"painter": 60, "general": 90}
            },
            {
                "name": "Frise décorative",
                "description": "Pose frise ou bordure murale",
                "unit": "ml",
                "default_price": 15,
                "suggested_prices": {"painter": 12, "general": 18}
            },
            {
                "name": "Patine meuble",
                "description": "Patine effet vieilli sur meuble",
                "unit": "unité",
                "default_price": 150,
                "suggested_prices": {"painter": 120, "general": 180}
            },
        ],
    },
    "Menuiserie": {
        "Portes & Fenêtres": [
            {
                "name": "Pose porte intérieure",
                "description": "Fourniture et pose bloc-porte",
                "unit": "unité",
                "default_price": 450,
                "suggested_prices": {"carpenter": 380, "general": 550}
            },
            {
                "name": "Pose fenêtre PVC",
                "description": "Dépose + pose fenêtre PVC double vitrage",
                "unit": "unité",
                "default_price": 650,
                "suggested_prices": {"carpenter": 550, "general": 780}
            },
            {
                "name": "Pose porte-fenêtre",
                "description": "Dépose + pose porte-fenêtre PVC",
                "unit": "unité",
                "default_price": 850,
                "suggested_prices": {"carpenter": 720, "general": 1020}
            },
            {
                "name": "Pose baie vitrée coulissante",
                "description": "Installation baie alu coulissante",
                "unit": "unité",
                "default_price": 1200,
                "suggested_prices": {"carpenter": 1000, "general": 1450}
            },
            {
                "name": "Pose volet roulant",
                "description": "Installation volet roulant électrique",
                "unit": "unité",
                "default_price": 550,
                "suggested_prices": {"carpenter": 460, "general": 660}
            },
        ],
        "Aménagement": [
            {
                "name": "Installation cuisine",
                "description": "Montage meubles cuisine équipée",
                "unit": "ml",
                "default_price": 180,
                "suggested_prices": {"carpenter": 150, "general": 220}
            },
            {
                "name": "Création placard",
                "description": "Aménagement placard sur mesure",
                "unit": "forfait",
                "default_price": 950,
                "suggested_prices": {"carpenter": 800, "general": 1150}
            },
            {
                "name": "Pose dressing",
                "description": "Installation kit dressing",
                "unit": "forfait",
                "default_price": 650,
                "suggested_prices": {"carpenter": 550, "general": 780}
            },
            {
                "name": "Pose étagères",
                "description": "Fixation étagères murales",
                "unit": "ml",
                "default_price": 45,
                "suggested_prices": {"carpenter": 38, "general": 55}
            },
            {
                "name": "Installation plan de travail",
                "description": "Pose et découpe plan de travail",
                "unit": "ml",
                "default_price": 95,
                "suggested_prices": {"carpenter": 80, "general": 115}
            },
        ],
        "Parquet": [
            {
                "name": "Pose parquet flottant",
                "description": "Pose parquet stratifié clipsable",
                "unit": "m²",
                "default_price": 35,
                "suggested_prices": {"carpenter": 28, "general": 42}
            },
            {
                "name": "Pose parquet massif collé",
                "description": "Pose parquet massif collé pleine masse",
                "unit": "m²",
                "default_price": 65,
                "suggested_prices": {"carpenter": 55, "general": 80}
            },
            {
                "name": "Pose parquet cloué",
                "description": "Pose traditionnelle sur lambourdes",
                "unit": "m²",
                "default_price": 75,
                "suggested_prices": {"carpenter": 62, "general": 90}
            },
            {
                "name": "Ponçage parquet",
                "description": "Ponçage 3 grains + aspiration",
                "unit": "m²",
                "default_price": 28,
                "suggested_prices": {"carpenter": 22, "general": 35}
            },
            {
                "name": "Vitrification parquet",
                "description": "Application vitrificateur 2 couches",
                "unit": "m²",
                "default_price": 22,
                "suggested_prices": {"carpenter": 18, "general": 28}
            },
        ],
        "Sur mesure": [
            {
                "name": "Création meuble sur mesure",
                "description": "Fabrication meuble bois sur mesure",
                "unit": "forfait",
                "default_price": 1500,
                "suggested_prices": {"carpenter": 1250, "general": 1800}
            },
            {
                "name": "Pose escalier bois",
                "description": "Installation escalier quart tournant",
                "unit": "forfait",
                "default_price": 2500,
                "suggested_prices": {"carpenter": 2100, "general": 3000}
            },
            {
                "name": "Habillage escalier",
                "description": "Habillage marches + contremarches",
                "unit": "marche",
                "default_price": 120,
                "suggested_prices": {"carpenter": 100, "general": 145}
            },
            {
                "name": "Pose garde-corps bois",
                "description": "Installation garde-corps intérieur",
                "unit": "ml",
                "default_price": 280,
                "suggested_prices": {"carpenter": 230, "general": 340}
            },
            {
                "name": "Pose plinthes",
                "description": "Fourniture et pose plinthes MDF",
                "unit": "ml",
                "default_price": 15,
                "suggested_prices": {"carpenter": 12, "general": 18}
            },
        ],
    },
    "Rénovation générale": {
        "Démolition": [
            {
                "name": "Démolition cloison légère",
                "description": "Démolition cloison placo/carreau plâtre",
                "unit": "m²",
                "default_price": 25,
                "suggested_prices": {"general": 25}
            },
            {
                "name": "Démolition cloison maçonnée",
                "description": "Démolition cloison brique/parpaing",
                "unit": "m²",
                "default_price": 45,
                "suggested_prices": {"general": 45}
            },
            {
                "name": "Dépose carrelage",
                "description": "Dépose carrelage sol ou mural",
                "unit": "m²",
                "default_price": 22,
                "suggested_prices": {"general": 22}
            },
            {
                "name": "Dépose parquet",
                "description": "Dépose parquet flottant ou collé",
                "unit": "m²",
                "default_price": 15,
                "suggested_prices": {"general": 15}
            },
            {
                "name": "Dépose faux plafond",
                "description": "Démontage faux plafond suspendu",
                "unit": "m²",
                "default_price": 18,
                "suggested_prices": {"general": 18}
            },
        ],
        "Main d'œuvre": [
            {
                "name": "Main d'œuvre qualifiée",
                "description": "Heure de travail artisan qualifié",
                "unit": "heure",
                "default_price": 45,
                "suggested_prices": {"general": 45}
            },
            {
                "name": "Main d'œuvre aide",
                "description": "Heure manœuvre/aide",
                "unit": "heure",
                "default_price": 32,
                "suggested_prices": {"general": 32}
            },
            {
                "name": "Heures supplémentaires",
                "description": "Majoration heures hors horaires",
                "unit": "heure",
                "default_price": 55,
                "suggested_prices": {"general": 55}
            },
            {
                "name": "Travail weekend",
                "description": "Majoration intervention weekend",
                "unit": "heure",
                "default_price": 65,
                "suggested_prices": {"general": 65}
            },
            {
                "name": "Déplacement",
                "description": "Frais de déplacement zone",
                "unit": "forfait",
                "default_price": 50,
                "suggested_prices": {"general": 50}
            },
        ],
        "Études": [
            {
                "name": "Étude technique",
                "description": "Analyse technique et préconisations",
                "unit": "forfait",
                "default_price": 250,
                "suggested_prices": {"general": 250}
            },
            {
                "name": "Relevé de cotes",
                "description": "Métrés et plans côtés",
                "unit": "forfait",
                "default_price": 180,
                "suggested_prices": {"general": 180}
            },
            {
                "name": "Devis détaillé",
                "description": "Établissement devis complexe",
                "unit": "forfait",
                "default_price": 150,
                "suggested_prices": {"general": 150}
            },
            {
                "name": "Suivi de chantier",
                "description": "Coordination et suivi travaux",
                "unit": "heure",
                "default_price": 65,
                "suggested_prices": {"general": 65}
            },
            {
                "name": "Conseil décoration",
                "description": "Accompagnement choix matériaux/couleurs",
                "unit": "heure",
                "default_price": 75,
                "suggested_prices": {"general": 75}
            },
        ],
        "Divers": [
            {
                "name": "Évacuation gravats",
                "description": "Chargement et transport déchetterie",
                "unit": "m³",
                "default_price": 85,
                "suggested_prices": {"general": 85}
            },
            {
                "name": "Location benne",
                "description": "Location benne 8m³ semaine",
                "unit": "semaine",
                "default_price": 350,
                "suggested_prices": {"general": 350}
            },
            {
                "name": "Protection chantier",
                "description": "Bâchage et protection mobilier",
                "unit": "forfait",
                "default_price": 150,
                "suggested_prices": {"general": 150}
            },
            {
                "name": "Nettoyage fin de chantier",
                "description": "Nettoyage complet après travaux",
                "unit": "m²",
                "default_price": 8,
                "suggested_prices": {"general": 8}
            },
            {
                "name": "Fournitures diverses",
                "description": "Petit matériel et consommables",
                "unit": "forfait",
                "default_price": 100,
                "suggested_prices": {"general": 100}
            },
        ],
    },
}

# Predefined kits
SEED_KITS_V2 = [
    {
        "name": "Installation électrique appartement T3",
        "business_type": "electrician",
        "description": "Kit complet pour installation électrique appartement 60-80m²",
        "items_refs": [
            ("Électricité", "Installation", "Installation prise électrique", 18),
            ("Électricité", "Installation", "Installation interrupteur", 12),
            ("Électricité", "Installation", "Pose luminaire plafonnier", 8),
            ("Électricité", "Installation", "Installation spot encastré", 12),
            ("Électricité", "Rénovation", "Remplacement tableau électrique", 1),
            ("Électricité", "Rénovation", "Tirage de câble", 150),
            ("Électricité", "Mise aux normes", "Mise à la terre", 1),
        ]
    },
    {
        "name": "Rénovation tableau électrique",
        "business_type": "electrician",
        "description": "Mise aux normes et remplacement tableau électrique",
        "items_refs": [
            ("Électricité", "Rénovation", "Remplacement tableau électrique", 1),
            ("Électricité", "Rénovation", "Remplacement disjoncteur", 8),
            ("Électricité", "Mise aux normes", "Installation parafoudre", 1),
            ("Électricité", "Mise aux normes", "Mise à la terre", 1),
            ("Électricité", "Mise aux normes", "Diagnostic électrique", 1),
        ]
    },
    {
        "name": "Rénovation salle de bain complète",
        "business_type": "plumber",
        "description": "Rénovation complète salle de bain 6-8m²",
        "items_refs": [
            ("Plomberie", "Salle de bain", "Installation douche italienne", 1),
            ("Plomberie", "Installation", "Installation WC suspendu", 1),
            ("Plomberie", "Installation", "Installation meuble vasque", 1),
            ("Plomberie", "Salle de bain", "Installation sèche-serviettes", 1),
            ("Plomberie", "Chauffage", "Installation chauffe-eau électrique", 1),
        ]
    },
    {
        "name": "Installation chauffe-eau",
        "business_type": "plumber",
        "description": "Remplacement chauffe-eau avec mise aux normes",
        "items_refs": [
            ("Plomberie", "Chauffage", "Installation chauffe-eau électrique", 1),
            ("Plomberie", "Dépannage", "Réparation fuite apparente", 1),
            ("Plomberie", "Chauffage", "Purge circuit chauffage", 1),
        ]
    },
    {
        "name": "Installation réseau bureau complet",
        "business_type": "it_installer",
        "description": "Infrastructure réseau bureau 10 postes",
        "items_refs": [
            ("Réseaux & Courants Faibles", "Câblage", "Installation prise RJ45", 12),
            ("Réseaux & Courants Faibles", "Câblage", "Tirage câble réseau", 100),
            ("Réseaux & Courants Faibles", "Infrastructure", "Installation baie de brassage", 1),
            ("Réseaux & Courants Faibles", "Infrastructure", "Installation switch réseau", 2),
            ("Réseaux & Courants Faibles", "Configuration", "Configuration routeur/box", 1),
            ("Réseaux & Courants Faibles", "Configuration", "Configuration réseau WiFi", 1),
            ("Réseaux & Courants Faibles", "Configuration", "Test et certification câblage", 12),
        ]
    },
    {
        "name": "Rénovation appartement clé en main",
        "business_type": "general",
        "description": "Rénovation complète appartement 50-70m²",
        "items_refs": [
            ("Rénovation générale", "Démolition", "Démolition cloison légère", 15),
            ("Rénovation générale", "Démolition", "Dépose carrelage", 25),
            ("Rénovation générale", "Divers", "Évacuation gravats", 3),
            ("Peinture", "Préparation", "Enduit de lissage", 120),
            ("Peinture", "Intérieur", "Peinture mur", 120),
            ("Peinture", "Intérieur", "Peinture plafond", 55),
            ("Menuiserie", "Parquet", "Pose parquet flottant", 55),
            ("Rénovation générale", "Divers", "Nettoyage fin de chantier", 55),
        ]
    },
    {
        "name": "Peinture appartement T3",
        "business_type": "painter",
        "description": "Peinture complète appartement 60-70m²",
        "items_refs": [
            ("Peinture", "Préparation", "Enduit de rebouchage", 100),
            ("Peinture", "Préparation", "Ponçage murs", 100),
            ("Peinture", "Préparation", "Sous-couche impression", 100),
            ("Peinture", "Intérieur", "Peinture mur", 100),
            ("Peinture", "Intérieur", "Peinture plafond", 55),
            ("Peinture", "Intérieur", "Peinture porte", 5),
            ("Peinture", "Intérieur", "Peinture boiseries", 40),
        ]
    },
    {
        "name": "Création salle de bain maçonnerie",
        "business_type": "mason",
        "description": "Travaux de maçonnerie pour création salle de bain",
        "items_refs": [
            ("Maçonnerie", "Rénovation", "Démolition cloison", 8),
            ("Maçonnerie", "Second œuvre", "Chape ciment", 6),
            ("Maçonnerie", "Second œuvre", "Ragréage sol", 6),
            ("Maçonnerie", "Second œuvre", "Montage cloison carreaux plâtre", 12),
            ("Maçonnerie", "Rénovation", "Évacuation gravats", 1),
        ]
    },
]


# ============== SERVICE CLASS V2 ==============

class CategoryServiceV2:
    """Enhanced service for managing categories, subcategories, items, and kits"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.categories = db.service_categories
        self.subcategories = db.service_subcategories
        self.items = db.service_items
        self.kits = db.service_kits
    
    async def init_indexes(self) -> None:
        """Create necessary indexes"""
        try:
            # Categories
            await self.categories.create_index("name", unique=True)
            await self.categories.create_index("business_types")
            
            # Subcategories
            await self.subcategories.create_index("category_id")
            await self.subcategories.create_index([("category_id", 1), ("name", 1)], unique=True)
            
            # Items
            await self.items.create_index("category_id")
            await self.items.create_index("subcategory_id")
            await self.items.create_index([("category_id", 1), ("subcategory_id", 1), ("name", 1)])
            
            # Kits
            await self.kits.create_index("business_type")
            await self.kits.create_index("name")
            
            logger.info("Category service V2 indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def seed_all(self, force: bool = False) -> Dict[str, int]:
        """
        Seed all categories, subcategories, items, and kits.
        
        Args:
            force: If True, delete existing and reseed
            
        Returns:
            Dict with counts of seeded data
        """
        stats = {"categories": 0, "subcategories": 0, "items": 0, "kits": 0, "skipped": False}
        
        # Check if already seeded
        existing_count = await self.subcategories.count_documents({})
        if existing_count > 0 and not force:
            logger.info(f"Data already seeded ({existing_count} subcategories found). Skipping.")
            stats["skipped"] = True
            return stats
        
        if force:
            await self.categories.delete_many({})
            await self.subcategories.delete_many({})
            await self.items.delete_many({})
            await self.kits.delete_many({})
            logger.info("Force reseed: cleared existing data")
        
        now = datetime.now(timezone.utc).isoformat()
        category_map = {}  # name -> id
        subcategory_map = {}  # (cat_name, subcat_name) -> id
        item_map = {}  # (cat_name, subcat_name, item_name) -> id
        
        # Seed categories and subcategories
        for cat_data in SEED_CATEGORIES_V2:
            cat_id = str(uuid.uuid4())
            category_doc = {
                "id": cat_id,
                "name": cat_data["name"],
                "business_types": cat_data["business_types"],
                "icon": cat_data.get("icon"),
                "created_at": now
            }
            
            try:
                await self.categories.insert_one(category_doc)
                category_map[cat_data["name"]] = cat_id
                stats["categories"] += 1
                
                # Seed subcategories
                for subcat_name in cat_data.get("subcategories", []):
                    subcat_id = str(uuid.uuid4())
                    subcat_doc = {
                        "id": subcat_id,
                        "category_id": cat_id,
                        "name": subcat_name,
                        "created_at": now
                    }
                    await self.subcategories.insert_one(subcat_doc)
                    subcategory_map[(cat_data["name"], subcat_name)] = subcat_id
                    stats["subcategories"] += 1
                    
            except Exception as e:
                logger.warning(f"Error seeding category {cat_data['name']}: {e}")
        
        # Seed items
        for cat_name, subcats in SEED_ITEMS_V2.items():
            cat_id = category_map.get(cat_name)
            if not cat_id:
                logger.warning(f"Category not found: {cat_name}")
                continue
                
            for subcat_name, items_list in subcats.items():
                subcat_id = subcategory_map.get((cat_name, subcat_name))
                if not subcat_id:
                    logger.warning(f"Subcategory not found: {cat_name}/{subcat_name}")
                    continue
                
                for item_data in items_list:
                    item_id = str(uuid.uuid4())
                    item_doc = {
                        "id": item_id,
                        "category_id": cat_id,
                        "subcategory_id": subcat_id,
                        "name": item_data["name"],
                        "description": item_data.get("description"),
                        "unit": item_data.get("unit", "unité"),
                        "default_price": item_data.get("default_price", 0),
                        "suggested_prices": item_data.get("suggested_prices", {}),
                        "created_at": now
                    }
                    await self.items.insert_one(item_doc)
                    item_map[(cat_name, subcat_name, item_data["name"])] = item_id
                    stats["items"] += 1
        
        # Seed kits
        for kit_data in SEED_KITS_V2:
            kit_id = str(uuid.uuid4())
            kit_items = []
            
            for cat_name, subcat_name, item_name, qty in kit_data["items_refs"]:
                item_id = item_map.get((cat_name, subcat_name, item_name))
                if item_id:
                    kit_items.append({
                        "service_item_id": item_id,
                        "quantity": qty
                    })
                else:
                    logger.warning(f"Kit item not found: {cat_name}/{subcat_name}/{item_name}")
            
            if kit_items:
                kit_doc = {
                    "id": kit_id,
                    "name": kit_data["name"],
                    "business_type": kit_data["business_type"],
                    "description": kit_data.get("description", ""),
                    "items": kit_items,
                    "created_at": now
                }
                await self.kits.insert_one(kit_doc)
                stats["kits"] += 1
        
        logger.info(f"Seeded {stats['categories']} categories, {stats['subcategories']} subcategories, {stats['items']} items, {stats['kits']} kits")
        return stats
    
    # ============== CATEGORIES ==============
    
    async def get_categories_for_user(self, business_type: str = "general") -> List[Dict[str, Any]]:
        """Get categories filtered by user's business type"""
        if business_type not in VALID_BUSINESS_TYPES:
            business_type = "general"
        
        # User's type OR general
        if business_type == "general":
            query = {}
        else:
            query = {
                "$or": [
                    {"business_types": business_type},
                    {"business_types": "general"}
                ]
            }
        
        categories = []
        cursor = self.categories.find(query).sort("name", 1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            categories.append(doc)
        
        return categories
    
    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories (admin view)"""
        categories = []
        cursor = self.categories.find({}).sort("name", 1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            categories.append(doc)
        
        return categories
    
    async def get_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get a single category by ID"""
        doc = await self.categories.find_one({"id": category_id})
        if doc:
            doc.pop("_id", None)
            return doc
        return None
    
    # ============== SUBCATEGORIES ==============
    
    async def get_subcategories(self, category_id: str) -> List[Dict[str, Any]]:
        """Get subcategories for a category"""
        subcategories = []
        cursor = self.subcategories.find({"category_id": category_id}).sort("name", 1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            subcategories.append(doc)
        
        return subcategories
    
    async def get_subcategory_by_id(self, subcategory_id: str) -> Optional[Dict[str, Any]]:
        """Get a single subcategory by ID"""
        doc = await self.subcategories.find_one({"id": subcategory_id})
        if doc:
            doc.pop("_id", None)
            return doc
        return None
    
    # ============== ITEMS ==============
    
    async def get_items_by_subcategory(self, subcategory_id: str) -> List[Dict[str, Any]]:
        """Get items for a subcategory"""
        items = []
        cursor = self.items.find({"subcategory_id": subcategory_id}).sort("name", 1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            items.append(doc)
        
        return items
    
    async def get_items_by_category(self, category_id: str) -> List[Dict[str, Any]]:
        """Get all items for a category (all subcategories)"""
        items = []
        cursor = self.items.find({"category_id": category_id}).sort("name", 1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            items.append(doc)
        
        return items
    
    async def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get a single item by ID"""
        doc = await self.items.find_one({"id": item_id})
        if doc:
            doc.pop("_id", None)
            return doc
        return None
    
    async def get_smart_price(self, item_id: str, business_type: str) -> float:
        """Get the smart price for an item based on business type"""
        item = await self.get_item_by_id(item_id)
        if not item:
            return 0.0
        
        suggested = item.get("suggested_prices", {})
        if business_type in suggested and suggested[business_type] is not None:
            return suggested[business_type]
        
        return item.get("default_price", 0.0)
    
    async def search_items(self, query: str, business_type: str = "general", limit: int = 20) -> List[Dict[str, Any]]:
        """Search items by name across allowed categories"""
        # First get allowed category IDs
        categories = await self.get_categories_for_user(business_type)
        category_ids = [c["id"] for c in categories]
        
        # Search items in those categories
        search_query = {
            "category_id": {"$in": category_ids},
            "name": {"$regex": query, "$options": "i"}
        }
        
        items = []
        cursor = self.items.find(search_query).limit(limit)
        
        async for doc in cursor:
            doc.pop("_id", None)
            items.append(doc)
        
        return items
    
    # ============== KITS ==============
    
    async def get_kits_for_user(self, business_type: str = "general") -> List[Dict[str, Any]]:
        """Get kits filtered by user's business type"""
        if business_type not in VALID_BUSINESS_TYPES:
            business_type = "general"
        
        if business_type == "general":
            query = {}
        else:
            query = {
                "$or": [
                    {"business_type": business_type},
                    {"business_type": "general"}
                ]
            }
        
        kits = []
        cursor = self.kits.find(query).sort("name", 1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            kits.append(doc)
        
        return kits
    
    async def get_kit_by_id(self, kit_id: str) -> Optional[Dict[str, Any]]:
        """Get a single kit by ID"""
        doc = await self.kits.find_one({"id": kit_id})
        if doc:
            doc.pop("_id", None)
            return doc
        return None
    
    async def get_kit_with_items(self, kit_id: str, business_type: str = "general") -> Optional[Dict[str, Any]]:
        """Get a kit with full item details and smart prices"""
        kit = await self.get_kit_by_id(kit_id)
        if not kit:
            return None
        
        expanded_items = []
        for kit_item in kit.get("items", []):
            item = await self.get_item_by_id(kit_item["service_item_id"])
            if item:
                smart_price = await self.get_smart_price(kit_item["service_item_id"], business_type)
                expanded_items.append({
                    "id": item["id"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "unit": item.get("unit", "unité"),
                    "quantity": kit_item["quantity"],
                    "unit_price": smart_price,
                    "total": smart_price * kit_item["quantity"]
                })
        
        kit["expanded_items"] = expanded_items
        kit["total_ht"] = sum(i["total"] for i in expanded_items)
        
        return kit
    
    # ============== COMBINED DATA ==============
    
    async def get_categories_with_subcategories(self, business_type: str = "general") -> List[Dict[str, Any]]:
        """Get categories with their subcategories"""
        categories = await self.get_categories_for_user(business_type)
        
        result = []
        for cat in categories:
            subcats = await self.get_subcategories(cat["id"])
            result.append({
                **cat,
                "subcategories": subcats
            })
        
        return result
    
    async def get_full_catalog(self, business_type: str = "general") -> List[Dict[str, Any]]:
        """Get full catalog: categories -> subcategories -> items"""
        categories = await self.get_categories_for_user(business_type)
        
        result = []
        for cat in categories:
            subcats = await self.get_subcategories(cat["id"])
            subcats_with_items = []
            
            for subcat in subcats:
                items = await self.get_items_by_subcategory(subcat["id"])
                # Add smart price to each item
                for item in items:
                    item["smart_price"] = await self.get_smart_price(item["id"], business_type)
                
                subcats_with_items.append({
                    **subcat,
                    "items": items
                })
            
            result.append({
                **cat,
                "subcategories": subcats_with_items
            })
        
        return result


def get_category_service_v2(db: AsyncIOMotorDatabase) -> CategoryServiceV2:
    """Factory function for CategoryServiceV2"""
    return CategoryServiceV2(db)
