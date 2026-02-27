"""
Service Categories Management - Simplified Version
Direct Category -> Article structure (no subcategories)
Enriched library with 150+ professional articles
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
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

# ============== ENRICHED SEED DATA ==============
# 150+ professional articles organized by category

SEED_CATEGORIES_SIMPLE = [
    {
        "name": "Électricité",
        "business_types": ["electrician", "general"],
        "icon": "Zap"
    },
    {
        "name": "Réseaux & Courants Faibles",
        "business_types": ["electrician", "it_installer", "general"],
        "icon": "Network"
    },
    {
        "name": "Plomberie",
        "business_types": ["plumber", "general"],
        "icon": "Droplets"
    },
    {
        "name": "Chauffage & Climatisation",
        "business_types": ["plumber", "general"],
        "icon": "Thermometer"
    },
    {
        "name": "Maçonnerie",
        "business_types": ["mason", "general"],
        "icon": "Blocks"
    },
    {
        "name": "Peinture & Revêtements",
        "business_types": ["painter", "general"],
        "icon": "Paintbrush"
    },
    {
        "name": "Menuiserie",
        "business_types": ["carpenter", "general"],
        "icon": "Hammer"
    },
    {
        "name": "Carrelage & Sols",
        "business_types": ["mason", "painter", "general"],
        "icon": "Grid3X3"
    },
    {
        "name": "Plâtrerie & Isolation",
        "business_types": ["mason", "painter", "general"],
        "icon": "Layers"
    },
    {
        "name": "Rénovation & Divers",
        "business_types": ["general"],
        "icon": "Home"
    }
]

# Enriched articles: 150+ items with realistic professional pricing
SEED_ITEMS_SIMPLE = {
    "Électricité": [
        # Installation
        {"name": "Installation prise électrique 16A", "description": "Pose prise encastrée avec boîtier", "unit": "unité", "default_price": 65, "suggested_prices": {"electrician": 55, "general": 70}},
        {"name": "Installation prise 32A (cuisson)", "description": "Pose prise spécialisée four/plaque", "unit": "unité", "default_price": 95, "suggested_prices": {"electrician": 80, "general": 110}},
        {"name": "Installation prise USB intégrée", "description": "Prise 16A avec ports USB", "unit": "unité", "default_price": 85, "suggested_prices": {"electrician": 70, "general": 95}},
        {"name": "Installation interrupteur simple", "description": "Interrupteur va-et-vient", "unit": "unité", "default_price": 55, "suggested_prices": {"electrician": 45, "general": 60}},
        {"name": "Installation interrupteur double", "description": "Double interrupteur encastré", "unit": "unité", "default_price": 70, "suggested_prices": {"electrician": 58, "general": 78}},
        {"name": "Installation variateur de lumière", "description": "Dimmer LED compatible", "unit": "unité", "default_price": 95, "suggested_prices": {"electrician": 78, "general": 105}},
        {"name": "Installation détecteur de mouvement", "description": "Détecteur infrarouge intérieur", "unit": "unité", "default_price": 120, "suggested_prices": {"electrician": 95, "general": 135}},
        {"name": "Pose luminaire plafonnier", "description": "Installation point lumineux", "unit": "unité", "default_price": 75, "suggested_prices": {"electrician": 65, "general": 85}},
        {"name": "Installation spot encastré LED", "description": "Spot avec transformateur", "unit": "unité", "default_price": 45, "suggested_prices": {"electrician": 38, "general": 50}},
        {"name": "Installation applique murale", "description": "Pose applique avec raccordement", "unit": "unité", "default_price": 85, "suggested_prices": {"electrician": 70, "general": 95}},
        {"name": "Installation suspension luminaire", "description": "Lustre ou suspension design", "unit": "unité", "default_price": 95, "suggested_prices": {"electrician": 80, "general": 110}},
        {"name": "Installation éclairage LED sous meuble", "description": "Bandeau LED cuisine/dressing", "unit": "ml", "default_price": 35, "suggested_prices": {"electrician": 28, "general": 40}},
        # Tableau électrique
        {"name": "Remplacement tableau électrique", "description": "Dépose + pose nouveau tableau", "unit": "forfait", "default_price": 850, "suggested_prices": {"electrician": 750, "general": 950}},
        {"name": "Extension tableau électrique", "description": "Ajout modules supplémentaires", "unit": "forfait", "default_price": 350, "suggested_prices": {"electrician": 280, "general": 400}},
        {"name": "Installation disjoncteur divisionnaire", "description": "Disjoncteur 10-32A", "unit": "unité", "default_price": 85, "suggested_prices": {"electrician": 70, "general": 95}},
        {"name": "Installation interrupteur différentiel 30mA", "description": "Protection personnes type A/AC", "unit": "unité", "default_price": 180, "suggested_prices": {"electrician": 150, "general": 210}},
        {"name": "Installation parafoudre", "description": "Protection surtensions", "unit": "unité", "default_price": 250, "suggested_prices": {"electrician": 200, "general": 300}},
        {"name": "Installation contacteur jour/nuit", "description": "Pilotage chauffe-eau", "unit": "unité", "default_price": 120, "suggested_prices": {"electrician": 95, "general": 140}},
        {"name": "Installation délesteur", "description": "Gestion priorité circuits", "unit": "unité", "default_price": 180, "suggested_prices": {"electrician": 145, "general": 210}},
        # Câblage
        {"name": "Tirage de câble sous gaine", "description": "Câble 1.5-2.5mm² ICTA", "unit": "ml", "default_price": 15, "suggested_prices": {"electrician": 12, "general": 18}},
        {"name": "Tirage câble 6mm² (cuisson)", "description": "Alimentation gros électroménager", "unit": "ml", "default_price": 22, "suggested_prices": {"electrician": 18, "general": 25}},
        {"name": "Pose goulotte électrique", "description": "Goulotte apparente PVC", "unit": "ml", "default_price": 22, "suggested_prices": {"electrician": 18, "general": 25}},
        {"name": "Création saignée murale", "description": "Rainurage pour encastrement", "unit": "ml", "default_price": 25, "suggested_prices": {"electrician": 20, "general": 30}},
        {"name": "Rebouchage saignée", "description": "Après passage câbles", "unit": "ml", "default_price": 12, "suggested_prices": {"electrician": 10, "general": 15}},
        # Mise aux normes
        {"name": "Mise aux normes NF C 15-100", "description": "Mise en conformité complète", "unit": "forfait", "default_price": 1200, "suggested_prices": {"electrician": 1000, "general": 1400}},
        {"name": "Mise à la terre", "description": "Création/reprise terre + barrette", "unit": "forfait", "default_price": 350, "suggested_prices": {"electrician": 280, "general": 420}},
        {"name": "Équipotentialité salle de bain", "description": "Liaison équipotentielle SDB", "unit": "forfait", "default_price": 180, "suggested_prices": {"electrician": 150, "general": 220}},
        {"name": "Diagnostic électrique", "description": "Contrôle conformité avec rapport", "unit": "forfait", "default_price": 150, "suggested_prices": {"electrician": 120, "general": 180}},
        # Dépannage
        {"name": "Recherche de panne électrique", "description": "Diagnostic et localisation", "unit": "forfait", "default_price": 95, "suggested_prices": {"electrician": 80, "general": 110}},
        {"name": "Réparation court-circuit", "description": "Identification et réparation", "unit": "forfait", "default_price": 150, "suggested_prices": {"electrician": 120, "general": 180}},
        {"name": "Remplacement prise défectueuse", "description": "Dépose + pose nouvelle", "unit": "unité", "default_price": 75, "suggested_prices": {"electrician": 60, "general": 85}},
        {"name": "Intervention urgente électricité", "description": "Dépannage urgent", "unit": "forfait", "default_price": 180, "suggested_prices": {"electrician": 150, "general": 220}},
    ],
    "Réseaux & Courants Faibles": [
        # Câblage réseau
        {"name": "Installation prise RJ45 cat.6", "description": "Prise réseau avec test", "unit": "unité", "default_price": 85, "suggested_prices": {"it_installer": 70, "electrician": 80, "general": 95}},
        {"name": "Installation prise RJ45 cat.6A", "description": "Prise réseau haute performance", "unit": "unité", "default_price": 110, "suggested_prices": {"it_installer": 90, "electrician": 100, "general": 125}},
        {"name": "Tirage câble réseau cat.6", "description": "Câble FTP/STP sous gaine", "unit": "ml", "default_price": 25, "suggested_prices": {"it_installer": 20, "electrician": 22, "general": 30}},
        {"name": "Tirage fibre optique", "description": "Fibre + soudure connecteurs", "unit": "ml", "default_price": 35, "suggested_prices": {"it_installer": 28, "electrician": 32, "general": 42}},
        {"name": "Pose câble coaxial TV/SAT", "description": "Avec connecteurs F", "unit": "ml", "default_price": 18, "suggested_prices": {"it_installer": 15, "electrician": 16, "general": 22}},
        {"name": "Test et certification câblage", "description": "Test Fluke avec rapport", "unit": "prise", "default_price": 25, "suggested_prices": {"it_installer": 18, "electrician": 22, "general": 30}},
        # Infrastructure
        {"name": "Installation baie de brassage 10U", "description": "Baie 19 pouces murale", "unit": "forfait", "default_price": 450, "suggested_prices": {"it_installer": 360, "electrician": 420, "general": 550}},
        {"name": "Installation baie de brassage 24U", "description": "Baie 19 pouces sol", "unit": "forfait", "default_price": 750, "suggested_prices": {"it_installer": 600, "electrician": 700, "general": 900}},
        {"name": "Installation panneau de brassage 24 ports", "description": "Patch panel cat.6", "unit": "unité", "default_price": 180, "suggested_prices": {"it_installer": 140, "electrician": 170, "general": 220}},
        {"name": "Installation switch 8 ports", "description": "Switch manageable Gigabit", "unit": "unité", "default_price": 150, "suggested_prices": {"it_installer": 120, "electrician": 140, "general": 180}},
        {"name": "Installation switch 24 ports", "description": "Switch manageable entreprise", "unit": "unité", "default_price": 280, "suggested_prices": {"it_installer": 220, "electrician": 260, "general": 340}},
        {"name": "Installation onduleur UPS", "description": "Protection alimentation", "unit": "unité", "default_price": 180, "suggested_prices": {"it_installer": 140, "electrician": 160, "general": 220}},
        {"name": "Installation NAS serveur fichiers", "description": "Mise en place stockage réseau", "unit": "forfait", "default_price": 350, "suggested_prices": {"it_installer": 280, "electrician": 330, "general": 420}},
        # WiFi & Configuration
        {"name": "Configuration routeur/box Internet", "description": "Paramétrage complet", "unit": "forfait", "default_price": 95, "suggested_prices": {"it_installer": 75, "electrician": 90, "general": 120}},
        {"name": "Installation borne WiFi professionnelle", "description": "Point d'accès entreprise", "unit": "unité", "default_price": 220, "suggested_prices": {"it_installer": 175, "electrician": 200, "general": 270}},
        {"name": "Extension réseau WiFi mesh", "description": "Système multi-points", "unit": "forfait", "default_price": 280, "suggested_prices": {"it_installer": 220, "electrician": 260, "general": 340}},
        {"name": "Configuration VPN entreprise", "description": "Accès distant sécurisé", "unit": "forfait", "default_price": 250, "suggested_prices": {"it_installer": 200, "electrician": 230, "general": 300}},
        # Sécurité
        {"name": "Installation caméra IP intérieure", "description": "Caméra + configuration", "unit": "unité", "default_price": 220, "suggested_prices": {"it_installer": 175, "electrician": 200, "general": 270}},
        {"name": "Installation caméra IP extérieure", "description": "Caméra étanche + câblage", "unit": "unité", "default_price": 320, "suggested_prices": {"it_installer": 260, "electrician": 290, "general": 380}},
        {"name": "Installation système alarme sans fil", "description": "Centrale + détecteurs", "unit": "forfait", "default_price": 550, "suggested_prices": {"it_installer": 450, "electrician": 500, "general": 650}},
        {"name": "Installation visiophone couleur", "description": "Écran + platine de rue", "unit": "forfait", "default_price": 450, "suggested_prices": {"it_installer": 380, "electrician": 420, "general": 550}},
        {"name": "Installation interphone audio", "description": "Système 2 fils", "unit": "forfait", "default_price": 280, "suggested_prices": {"it_installer": 230, "electrician": 260, "general": 340}},
        {"name": "Installation contrôle d'accès badge", "description": "Lecteur + gâche électrique", "unit": "forfait", "default_price": 650, "suggested_prices": {"it_installer": 550, "electrician": 600, "general": 780}},
        {"name": "Installation antenne TV/TNT", "description": "Pose + réglage orientation", "unit": "forfait", "default_price": 180, "suggested_prices": {"it_installer": 145, "electrician": 165, "general": 220}},
        {"name": "Installation parabole satellite", "description": "Pose + pointage + décodeur", "unit": "forfait", "default_price": 250, "suggested_prices": {"it_installer": 200, "electrician": 230, "general": 300}},
    ],
    "Plomberie": [
        # Sanitaires
        {"name": "Installation WC suspendu complet", "description": "Bâti-support + cuvette + abattant", "unit": "forfait", "default_price": 750, "suggested_prices": {"plumber": 620, "general": 880}},
        {"name": "Installation WC à poser", "description": "Pack WC complet + raccordement", "unit": "forfait", "default_price": 320, "suggested_prices": {"plumber": 260, "general": 380}},
        {"name": "Remplacement mécanisme WC", "description": "Chasse d'eau complète", "unit": "forfait", "default_price": 120, "suggested_prices": {"plumber": 95, "general": 145}},
        {"name": "Installation lavabo sur colonne", "description": "Lavabo + robinetterie + évacuation", "unit": "forfait", "default_price": 350, "suggested_prices": {"plumber": 280, "general": 420}},
        {"name": "Installation meuble vasque", "description": "Meuble + vasque + mitigeur", "unit": "forfait", "default_price": 480, "suggested_prices": {"plumber": 400, "general": 580}},
        {"name": "Installation double vasque", "description": "Plan double + 2 mitigeurs", "unit": "forfait", "default_price": 750, "suggested_prices": {"plumber": 620, "general": 900}},
        {"name": "Installation évier cuisine", "description": "Évier + mitigeur + broyeur optionnel", "unit": "forfait", "default_price": 320, "suggested_prices": {"plumber": 260, "general": 380}},
        {"name": "Installation mitigeur cuisine douchette", "description": "Robinet extractible", "unit": "forfait", "default_price": 180, "suggested_prices": {"plumber": 145, "general": 220}},
        {"name": "Remplacement robinetterie", "description": "Mitigeur lavabo/évier", "unit": "unité", "default_price": 150, "suggested_prices": {"plumber": 120, "general": 180}},
        # Douche & Baignoire
        {"name": "Création douche à l'italienne", "description": "Receveur extra-plat + étanchéité", "unit": "forfait", "default_price": 1800, "suggested_prices": {"plumber": 1500, "general": 2200}},
        {"name": "Installation receveur de douche", "description": "Pose receveur + paroi + mitigeur", "unit": "forfait", "default_price": 950, "suggested_prices": {"plumber": 780, "general": 1150}},
        {"name": "Installation paroi de douche fixe", "description": "Paroi verre 8mm", "unit": "unité", "default_price": 280, "suggested_prices": {"plumber": 230, "general": 340}},
        {"name": "Installation porte de douche", "description": "Porte pivotante ou coulissante", "unit": "unité", "default_price": 380, "suggested_prices": {"plumber": 310, "general": 460}},
        {"name": "Installation colonne de douche thermostatique", "description": "Colonne complète + pommeau", "unit": "forfait", "default_price": 420, "suggested_prices": {"plumber": 350, "general": 500}},
        {"name": "Installation baignoire droite", "description": "Baignoire + robinetterie + tablier", "unit": "forfait", "default_price": 750, "suggested_prices": {"plumber": 620, "general": 900}},
        {"name": "Installation baignoire d'angle", "description": "Avec habillage", "unit": "forfait", "default_price": 950, "suggested_prices": {"plumber": 780, "general": 1150}},
        {"name": "Installation baignoire balnéo", "description": "Baignoire hydromassage", "unit": "forfait", "default_price": 1200, "suggested_prices": {"plumber": 1000, "general": 1450}},
        # Dépannage
        {"name": "Recherche de fuite", "description": "Diagnostic et localisation", "unit": "forfait", "default_price": 120, "suggested_prices": {"plumber": 95, "general": 150}},
        {"name": "Réparation fuite apparente", "description": "Joint, raccord, soudure", "unit": "forfait", "default_price": 95, "suggested_prices": {"plumber": 75, "general": 120}},
        {"name": "Réparation fuite encastrée", "description": "Avec ouverture et rebouchage", "unit": "forfait", "default_price": 280, "suggested_prices": {"plumber": 230, "general": 340}},
        {"name": "Débouchage canalisation manuel", "description": "Furet ou ventouse", "unit": "forfait", "default_price": 95, "suggested_prices": {"plumber": 75, "general": 120}},
        {"name": "Débouchage haute pression", "description": "Hydrocurage professionnel", "unit": "forfait", "default_price": 280, "suggested_prices": {"plumber": 230, "general": 340}},
        {"name": "Débouchage WC", "description": "Intervention rapide", "unit": "forfait", "default_price": 95, "suggested_prices": {"plumber": 75, "general": 120}},
        {"name": "Remplacement siphon", "description": "Siphon lavabo/évier/douche", "unit": "unité", "default_price": 65, "suggested_prices": {"plumber": 50, "general": 80}},
        {"name": "Remplacement flexible douche", "description": "Flexible + pommeau", "unit": "forfait", "default_price": 75, "suggested_prices": {"plumber": 60, "general": 90}},
        {"name": "Intervention urgente plomberie", "description": "Dépannage urgent", "unit": "forfait", "default_price": 180, "suggested_prices": {"plumber": 150, "general": 220}},
    ],
    "Chauffage & Climatisation": [
        # Chauffe-eau
        {"name": "Installation chauffe-eau électrique 100L", "description": "Cumulus + groupe sécurité", "unit": "forfait", "default_price": 450, "suggested_prices": {"plumber": 380, "general": 550}},
        {"name": "Installation chauffe-eau électrique 200L", "description": "Cumulus grande capacité", "unit": "forfait", "default_price": 550, "suggested_prices": {"plumber": 460, "general": 660}},
        {"name": "Installation chauffe-eau thermodynamique", "description": "Ballon thermodynamique", "unit": "forfait", "default_price": 950, "suggested_prices": {"plumber": 780, "general": 1150}},
        {"name": "Installation chauffe-eau instantané", "description": "Sans réservoir", "unit": "forfait", "default_price": 380, "suggested_prices": {"plumber": 310, "general": 460}},
        {"name": "Remplacement groupe de sécurité", "description": "Avec vidange", "unit": "forfait", "default_price": 120, "suggested_prices": {"plumber": 95, "general": 145}},
        {"name": "Détartrage chauffe-eau", "description": "Nettoyage résistance + cuve", "unit": "forfait", "default_price": 180, "suggested_prices": {"plumber": 145, "general": 220}},
        # Radiateurs
        {"name": "Installation radiateur électrique", "description": "Radiateur inertie + raccordement", "unit": "unité", "default_price": 280, "suggested_prices": {"plumber": 230, "electrician": 250, "general": 340}},
        {"name": "Installation radiateur eau chaude", "description": "Radiateur acier/alu + raccordement", "unit": "unité", "default_price": 320, "suggested_prices": {"plumber": 260, "general": 380}},
        {"name": "Installation sèche-serviettes électrique", "description": "Radiateur SDB", "unit": "unité", "default_price": 280, "suggested_prices": {"plumber": 230, "electrician": 250, "general": 340}},
        {"name": "Installation sèche-serviettes mixte", "description": "Électrique + eau chaude", "unit": "unité", "default_price": 380, "suggested_prices": {"plumber": 310, "general": 460}},
        {"name": "Remplacement vanne thermostatique", "description": "Tête thermostatique radiateur", "unit": "unité", "default_price": 85, "suggested_prices": {"plumber": 70, "general": 100}},
        {"name": "Purge radiateurs", "description": "Purge circuit complet", "unit": "forfait", "default_price": 95, "suggested_prices": {"plumber": 75, "general": 120}},
        {"name": "Désembouage circuit chauffage", "description": "Nettoyage chimique circuit", "unit": "forfait", "default_price": 480, "suggested_prices": {"plumber": 400, "general": 580}},
        # Climatisation
        {"name": "Installation climatisation mono-split", "description": "Unité intérieure + extérieure", "unit": "forfait", "default_price": 1200, "suggested_prices": {"plumber": 1000, "electrician": 1100, "general": 1450}},
        {"name": "Installation climatisation multi-split 2 unités", "description": "2 intérieures + 1 extérieure", "unit": "forfait", "default_price": 2200, "suggested_prices": {"plumber": 1850, "electrician": 2000, "general": 2650}},
        {"name": "Installation climatisation réversible", "description": "Chaud/froid", "unit": "forfait", "default_price": 1400, "suggested_prices": {"plumber": 1150, "electrician": 1300, "general": 1700}},
        {"name": "Recharge gaz climatisation", "description": "Recharge R410A/R32", "unit": "forfait", "default_price": 180, "suggested_prices": {"plumber": 145, "general": 220}},
        {"name": "Entretien climatisation", "description": "Nettoyage + contrôle annuel", "unit": "forfait", "default_price": 120, "suggested_prices": {"plumber": 95, "general": 145}},
        {"name": "Installation VMC simple flux", "description": "VMC + bouches + gaines", "unit": "forfait", "default_price": 650, "suggested_prices": {"plumber": 550, "electrician": 580, "general": 780}},
        {"name": "Installation VMC double flux", "description": "VMC récupération chaleur", "unit": "forfait", "default_price": 1800, "suggested_prices": {"plumber": 1500, "electrician": 1650, "general": 2150}},
    ],
    "Maçonnerie": [
        # Gros œuvre
        {"name": "Coulage dalle béton armé", "description": "Dalle 10-15cm ferraillée", "unit": "m²", "default_price": 95, "suggested_prices": {"mason": 78, "general": 115}},
        {"name": "Coulage chape béton", "description": "Chape de finition 5-7cm", "unit": "m²", "default_price": 45, "suggested_prices": {"mason": 36, "general": 55}},
        {"name": "Montage mur parpaings 20cm", "description": "Parpaings creux", "unit": "m²", "default_price": 85, "suggested_prices": {"mason": 70, "general": 100}},
        {"name": "Montage mur briques", "description": "Briques pleines ou creuses", "unit": "m²", "default_price": 95, "suggested_prices": {"mason": 78, "general": 115}},
        {"name": "Montage mur béton cellulaire", "description": "Blocs type Siporex", "unit": "m²", "default_price": 75, "suggested_prices": {"mason": 62, "general": 90}},
        {"name": "Chaînage béton armé horizontal", "description": "Ceinturage", "unit": "ml", "default_price": 65, "suggested_prices": {"mason": 55, "general": 80}},
        {"name": "Chaînage béton armé vertical", "description": "Poteaux d'angle", "unit": "ml", "default_price": 75, "suggested_prices": {"mason": 62, "general": 90}},
        {"name": "Pose linteau préfabriqué", "description": "Linteau béton armé", "unit": "ml", "default_price": 85, "suggested_prices": {"mason": 70, "general": 100}},
        {"name": "Création ouverture mur porteur", "description": "Avec pose IPN", "unit": "forfait", "default_price": 2500, "suggested_prices": {"mason": 2100, "general": 3000}},
        # Finitions
        {"name": "Enduit monocouche façade", "description": "Enduit coloré projeté", "unit": "m²", "default_price": 55, "suggested_prices": {"mason": 45, "general": 65}},
        {"name": "Enduit traditionnel 3 couches", "description": "Gobetis + corps + finition", "unit": "m²", "default_price": 75, "suggested_prices": {"mason": 62, "general": 90}},
        {"name": "Ravalement façade complet", "description": "Nettoyage + réparation + enduit", "unit": "m²", "default_price": 85, "suggested_prices": {"mason": 70, "general": 100}},
        {"name": "Réparation fissures façade", "description": "Traitement + armature", "unit": "ml", "default_price": 55, "suggested_prices": {"mason": 45, "general": 65}},
        {"name": "Ragréage sol autolissant", "description": "Préparation support", "unit": "m²", "default_price": 28, "suggested_prices": {"mason": 22, "general": 35}},
        {"name": "Pose appui fenêtre béton", "description": "Appui préfabriqué", "unit": "ml", "default_price": 75, "suggested_prices": {"mason": 62, "general": 90}},
        {"name": "Réalisation seuil béton", "description": "Seuil de porte lissé", "unit": "unité", "default_price": 150, "suggested_prices": {"mason": 125, "general": 180}},
        # Démolition
        {"name": "Démolition cloison légère", "description": "Placo, carreau plâtre", "unit": "m²", "default_price": 25, "suggested_prices": {"mason": 20, "general": 30}},
        {"name": "Démolition cloison maçonnée", "description": "Brique, parpaing", "unit": "m²", "default_price": 45, "suggested_prices": {"mason": 36, "general": 55}},
        {"name": "Démolition mur porteur", "description": "Avec étaiement", "unit": "forfait", "default_price": 1500, "suggested_prices": {"mason": 1250, "general": 1800}},
        {"name": "Évacuation gravats", "description": "Chargement + transport déchetterie", "unit": "m³", "default_price": 95, "suggested_prices": {"mason": 78, "general": 115}},
    ],
    "Peinture & Revêtements": [
        # Peinture intérieure
        {"name": "Peinture mur acrylique 2 couches", "description": "Mat ou satiné", "unit": "m²", "default_price": 28, "suggested_prices": {"painter": 22, "general": 35}},
        {"name": "Peinture plafond mat", "description": "2 couches blanc mat", "unit": "m²", "default_price": 32, "suggested_prices": {"painter": 26, "general": 40}},
        {"name": "Peinture lessivable cuisine/SDB", "description": "Peinture spéciale humidité", "unit": "m²", "default_price": 35, "suggested_prices": {"painter": 28, "general": 42}},
        {"name": "Peinture boiseries laque satinée", "description": "Portes, plinthes, moulures", "unit": "ml", "default_price": 18, "suggested_prices": {"painter": 14, "general": 22}},
        {"name": "Peinture porte 2 faces + huisserie", "description": "Complète avec sous-couche", "unit": "unité", "default_price": 120, "suggested_prices": {"painter": 95, "general": 145}},
        {"name": "Peinture fenêtre bois 2 faces", "description": "Décapage optionnel", "unit": "unité", "default_price": 95, "suggested_prices": {"painter": 78, "general": 115}},
        {"name": "Peinture radiateur", "description": "Peinture haute température", "unit": "unité", "default_price": 75, "suggested_prices": {"painter": 60, "general": 90}},
        {"name": "Peinture escalier bois", "description": "Marches + contremarches + garde-corps", "unit": "forfait", "default_price": 650, "suggested_prices": {"painter": 520, "general": 780}},
        # Préparation
        {"name": "Enduit de rebouchage", "description": "Fissures et trous", "unit": "m²", "default_price": 15, "suggested_prices": {"painter": 12, "general": 18}},
        {"name": "Enduit de lissage", "description": "Surface parfaitement lisse", "unit": "m²", "default_price": 22, "suggested_prices": {"painter": 18, "general": 28}},
        {"name": "Ratissage complet", "description": "Enduit + ponçage intégral", "unit": "m²", "default_price": 28, "suggested_prices": {"painter": 22, "general": 35}},
        {"name": "Ponçage murs/plafonds", "description": "Ponçage mécanique", "unit": "m²", "default_price": 10, "suggested_prices": {"painter": 8, "general": 12}},
        {"name": "Sous-couche impression", "description": "Primaire d'accrochage", "unit": "m²", "default_price": 12, "suggested_prices": {"painter": 10, "general": 15}},
        {"name": "Décapage peinture écaillée", "description": "Chimique ou thermique", "unit": "m²", "default_price": 28, "suggested_prices": {"painter": 22, "general": 35}},
        {"name": "Traitement anti-humidité", "description": "Traitement murs humides", "unit": "m²", "default_price": 35, "suggested_prices": {"painter": 28, "general": 42}},
        # Peinture extérieure
        {"name": "Peinture façade", "description": "Peinture pliolite/siloxane", "unit": "m²", "default_price": 28, "suggested_prices": {"painter": 22, "general": 35}},
        {"name": "Peinture volets bois", "description": "Décapage + microporeuse", "unit": "m²", "default_price": 65, "suggested_prices": {"painter": 52, "general": 78}},
        {"name": "Peinture portail métal", "description": "Antirouille + laque", "unit": "m²", "default_price": 55, "suggested_prices": {"painter": 44, "general": 65}},
        {"name": "Lasure bois extérieur", "description": "Protection UV 3 couches", "unit": "m²", "default_price": 28, "suggested_prices": {"painter": 22, "general": 35}},
        {"name": "Traitement anti-mousse façade", "description": "Nettoyage + traitement", "unit": "m²", "default_price": 12, "suggested_prices": {"painter": 10, "general": 15}},
        # Décoration
        {"name": "Pose papier peint intissé", "description": "Préparation + pose", "unit": "m²", "default_price": 32, "suggested_prices": {"painter": 26, "general": 40}},
        {"name": "Pose toile de verre à peindre", "description": "Marouflage + peinture", "unit": "m²", "default_price": 28, "suggested_prices": {"painter": 22, "general": 35}},
        {"name": "Effet décoratif béton ciré mur", "description": "Application stucco", "unit": "m²", "default_price": 85, "suggested_prices": {"painter": 70, "general": 100}},
        {"name": "Effet décoratif patine", "description": "Effet vieilli/patiné", "unit": "m²", "default_price": 55, "suggested_prices": {"painter": 44, "general": 65}},
        {"name": "Pose frise décorative", "description": "Bordure murale", "unit": "ml", "default_price": 18, "suggested_prices": {"painter": 14, "general": 22}},
    ],
    "Menuiserie": [
        # Portes
        {"name": "Pose porte intérieure bloc-porte", "description": "Porte + huisserie + quincaillerie", "unit": "unité", "default_price": 480, "suggested_prices": {"carpenter": 400, "general": 580}},
        {"name": "Pose porte coulissante galandage", "description": "Avec châssis à galandage", "unit": "unité", "default_price": 850, "suggested_prices": {"carpenter": 700, "general": 1020}},
        {"name": "Pose porte coulissante apparente", "description": "Rail apparent + porte", "unit": "unité", "default_price": 550, "suggested_prices": {"carpenter": 460, "general": 660}},
        {"name": "Pose porte d'entrée blindée", "description": "Porte sécurisée A2P", "unit": "unité", "default_price": 1500, "suggested_prices": {"carpenter": 1250, "general": 1800}},
        {"name": "Pose porte de service", "description": "Porte technique/garage", "unit": "unité", "default_price": 550, "suggested_prices": {"carpenter": 460, "general": 660}},
        # Fenêtres
        {"name": "Pose fenêtre PVC double vitrage", "description": "Dépose ancien + pose", "unit": "unité", "default_price": 650, "suggested_prices": {"carpenter": 550, "general": 780}},
        {"name": "Pose fenêtre alu double vitrage", "description": "Dépose ancien + pose", "unit": "unité", "default_price": 850, "suggested_prices": {"carpenter": 700, "general": 1020}},
        {"name": "Pose porte-fenêtre PVC", "description": "Dépose ancien + pose", "unit": "unité", "default_price": 950, "suggested_prices": {"carpenter": 780, "general": 1150}},
        {"name": "Pose baie vitrée coulissante alu", "description": "Grande ouverture", "unit": "unité", "default_price": 1400, "suggested_prices": {"carpenter": 1150, "general": 1700}},
        {"name": "Pose fenêtre de toit Velux", "description": "Avec raccord étanchéité", "unit": "unité", "default_price": 850, "suggested_prices": {"carpenter": 700, "general": 1020}},
        {"name": "Pose volet roulant électrique", "description": "Coffre + tablier + moteur", "unit": "unité", "default_price": 650, "suggested_prices": {"carpenter": 550, "general": 780}},
        {"name": "Pose volet battant bois", "description": "Paire de volets + gonds", "unit": "unité", "default_price": 480, "suggested_prices": {"carpenter": 400, "general": 580}},
        {"name": "Remplacement vitrage simple", "description": "Verre 4mm", "unit": "unité", "default_price": 85, "suggested_prices": {"carpenter": 70, "general": 100}},
        {"name": "Remplacement double vitrage", "description": "Vitrage isolant 4/16/4", "unit": "unité", "default_price": 180, "suggested_prices": {"carpenter": 150, "general": 220}},
        # Aménagement
        {"name": "Pose cuisine équipée", "description": "Montage meubles bas + hauts", "unit": "ml", "default_price": 220, "suggested_prices": {"carpenter": 180, "general": 270}},
        {"name": "Création placard sur mesure", "description": "Caisson + portes + aménagement", "unit": "forfait", "default_price": 1200, "suggested_prices": {"carpenter": 1000, "general": 1450}},
        {"name": "Pose dressing kit", "description": "Kit aménagement + montage", "unit": "forfait", "default_price": 650, "suggested_prices": {"carpenter": 550, "general": 780}},
        {"name": "Pose étagères sur mesure", "description": "Découpe + fixation", "unit": "ml", "default_price": 55, "suggested_prices": {"carpenter": 45, "general": 65}},
        {"name": "Pose plan de travail cuisine", "description": "Découpe + pose + joints", "unit": "ml", "default_price": 120, "suggested_prices": {"carpenter": 100, "general": 145}},
        {"name": "Pose crédence cuisine", "description": "Verre/alu/stratifié", "unit": "ml", "default_price": 95, "suggested_prices": {"carpenter": 78, "general": 115}},
        # Escalier
        {"name": "Pose escalier bois droit", "description": "Escalier + rampe", "unit": "forfait", "default_price": 2200, "suggested_prices": {"carpenter": 1850, "general": 2650}},
        {"name": "Pose escalier 1/4 tournant", "description": "Avec palier intermédiaire", "unit": "forfait", "default_price": 2800, "suggested_prices": {"carpenter": 2350, "general": 3350}},
        {"name": "Pose escalier 2/4 tournant", "description": "Double quart tournant", "unit": "forfait", "default_price": 3500, "suggested_prices": {"carpenter": 2900, "general": 4200}},
        {"name": "Habillage escalier béton", "description": "Marches + contremarches bois", "unit": "marche", "default_price": 150, "suggested_prices": {"carpenter": 125, "general": 180}},
        {"name": "Pose garde-corps bois", "description": "Main courante + balustres", "unit": "ml", "default_price": 320, "suggested_prices": {"carpenter": 260, "general": 380}},
        {"name": "Pose garde-corps inox/verre", "description": "Design moderne", "unit": "ml", "default_price": 450, "suggested_prices": {"carpenter": 380, "general": 550}},
    ],
    "Carrelage & Sols": [
        # Carrelage
        {"name": "Pose carrelage sol standard", "description": "Carreaux 30x30 à 60x60", "unit": "m²", "default_price": 55, "suggested_prices": {"mason": 45, "painter": 50, "general": 65}},
        {"name": "Pose carrelage sol grand format", "description": "Carreaux 60x120 et plus", "unit": "m²", "default_price": 75, "suggested_prices": {"mason": 62, "painter": 68, "general": 90}},
        {"name": "Pose carrelage imitation parquet", "description": "Format lames", "unit": "m²", "default_price": 65, "suggested_prices": {"mason": 55, "painter": 58, "general": 78}},
        {"name": "Pose carrelage mural", "description": "Faïence salle de bain/cuisine", "unit": "m²", "default_price": 55, "suggested_prices": {"mason": 45, "painter": 50, "general": 65}},
        {"name": "Pose mosaïque", "description": "Plaques mosaïque verre/pierre", "unit": "m²", "default_price": 85, "suggested_prices": {"mason": 70, "painter": 75, "general": 100}},
        {"name": "Pose crédence carrelage", "description": "Carrelage mural cuisine", "unit": "m²", "default_price": 65, "suggested_prices": {"mason": 55, "painter": 58, "general": 78}},
        {"name": "Réalisation douche italienne carrelée", "description": "Étanchéité + carrelage complet", "unit": "forfait", "default_price": 1500, "suggested_prices": {"mason": 1250, "general": 1800}},
        {"name": "Joints carrelage", "description": "Pose joints époxy ou ciment", "unit": "m²", "default_price": 15, "suggested_prices": {"mason": 12, "painter": 13, "general": 18}},
        {"name": "Dépose carrelage existant", "description": "Démolition + évacuation", "unit": "m²", "default_price": 28, "suggested_prices": {"mason": 22, "general": 35}},
        # Parquet
        {"name": "Pose parquet flottant stratifié", "description": "Avec sous-couche", "unit": "m²", "default_price": 38, "suggested_prices": {"carpenter": 32, "painter": 35, "general": 45}},
        {"name": "Pose parquet contrecollé clipsable", "description": "Bois noble", "unit": "m²", "default_price": 55, "suggested_prices": {"carpenter": 45, "painter": 50, "general": 65}},
        {"name": "Pose parquet massif collé", "description": "Pleine masse", "unit": "m²", "default_price": 75, "suggested_prices": {"carpenter": 62, "general": 90}},
        {"name": "Pose parquet massif cloué", "description": "Sur lambourdes", "unit": "m²", "default_price": 95, "suggested_prices": {"carpenter": 78, "general": 115}},
        {"name": "Ponçage parquet", "description": "3 grains + aspiration", "unit": "m²", "default_price": 32, "suggested_prices": {"carpenter": 26, "painter": 28, "general": 40}},
        {"name": "Vitrification parquet", "description": "2 couches vitrificateur", "unit": "m²", "default_price": 28, "suggested_prices": {"carpenter": 22, "painter": 24, "general": 35}},
        {"name": "Huile parquet", "description": "2 couches huile dure", "unit": "m²", "default_price": 25, "suggested_prices": {"carpenter": 20, "painter": 22, "general": 32}},
        {"name": "Dépose parquet existant", "description": "Flottant ou collé", "unit": "m²", "default_price": 18, "suggested_prices": {"carpenter": 14, "general": 22}},
        # Autres sols
        {"name": "Pose sol PVC en lés", "description": "Vinyle souple", "unit": "m²", "default_price": 32, "suggested_prices": {"painter": 26, "general": 40}},
        {"name": "Pose sol PVC clipsable LVT", "description": "Lames vinyle rigide", "unit": "m²", "default_price": 45, "suggested_prices": {"painter": 36, "carpenter": 38, "general": 55}},
        {"name": "Pose moquette", "description": "Moquette aiguilletée ou bouclée", "unit": "m²", "default_price": 28, "suggested_prices": {"painter": 22, "general": 35}},
        {"name": "Pose jonc de mer/sisal", "description": "Revêtement naturel", "unit": "m²", "default_price": 45, "suggested_prices": {"painter": 36, "general": 55}},
        {"name": "Pose plinthes bois", "description": "Plinthes MDF ou massif", "unit": "ml", "default_price": 18, "suggested_prices": {"carpenter": 14, "painter": 15, "general": 22}},
        {"name": "Pose plinthes carrelage", "description": "Plinthes assorties", "unit": "ml", "default_price": 22, "suggested_prices": {"mason": 18, "general": 28}},
    ],
    "Plâtrerie & Isolation": [
        # Cloisons
        {"name": "Cloison placo BA13 simple", "description": "Ossature + 1 plaque par face", "unit": "m²", "default_price": 55, "suggested_prices": {"mason": 45, "painter": 48, "general": 65}},
        {"name": "Cloison placo BA13 isolée", "description": "Ossature + laine 45mm + plaques", "unit": "m²", "default_price": 75, "suggested_prices": {"mason": 62, "painter": 68, "general": 90}},
        {"name": "Cloison placo hydrofuge", "description": "Plaque verte salle de bain", "unit": "m²", "default_price": 65, "suggested_prices": {"mason": 55, "painter": 58, "general": 78}},
        {"name": "Cloison placo phonique", "description": "Double plaque + isolant", "unit": "m²", "default_price": 95, "suggested_prices": {"mason": 78, "general": 115}},
        {"name": "Doublage mur placo sur rail", "description": "Isolation + parement", "unit": "m²", "default_price": 65, "suggested_prices": {"mason": 55, "painter": 58, "general": 78}},
        {"name": "Doublage mur placo collé", "description": "Complexe isolant collé", "unit": "m²", "default_price": 55, "suggested_prices": {"mason": 45, "painter": 48, "general": 65}},
        # Plafonds
        {"name": "Faux plafond placo BA13", "description": "Ossature suspendue + plaques", "unit": "m²", "default_price": 65, "suggested_prices": {"mason": 55, "painter": 58, "general": 78}},
        {"name": "Faux plafond dalles 60x60", "description": "Ossature + dalles minérales", "unit": "m²", "default_price": 55, "suggested_prices": {"mason": 45, "general": 65}},
        {"name": "Plafond tendu", "description": "Toile PVC tendue", "unit": "m²", "default_price": 85, "suggested_prices": {"painter": 70, "general": 100}},
        {"name": "Habillage coffre/gaine", "description": "Placo sur ossature", "unit": "ml", "default_price": 55, "suggested_prices": {"mason": 45, "painter": 48, "general": 65}},
        {"name": "Création niche murale", "description": "Structure + parement", "unit": "unité", "default_price": 180, "suggested_prices": {"mason": 150, "painter": 160, "general": 220}},
        # Isolation
        {"name": "Isolation laine de verre murs", "description": "Laine 100mm R=2.5", "unit": "m²", "default_price": 35, "suggested_prices": {"mason": 28, "general": 42}},
        {"name": "Isolation laine de roche murs", "description": "Laine 100mm R=2.5", "unit": "m²", "default_price": 42, "suggested_prices": {"mason": 34, "general": 50}},
        {"name": "Isolation combles perdus soufflée", "description": "Laine 30cm R=7", "unit": "m²", "default_price": 32, "suggested_prices": {"mason": 26, "general": 40}},
        {"name": "Isolation combles rampants", "description": "Entre chevrons + sous chevrons", "unit": "m²", "default_price": 65, "suggested_prices": {"mason": 55, "general": 78}},
        {"name": "Isolation sol sous chape", "description": "Polystyrène + pare-vapeur", "unit": "m²", "default_price": 35, "suggested_prices": {"mason": 28, "general": 42}},
        # Finitions plâtre
        {"name": "Bandes à joints placo", "description": "Calicot + enduit", "unit": "m²", "default_price": 12, "suggested_prices": {"mason": 10, "painter": 11, "general": 15}},
        {"name": "Enduit plâtre projeté", "description": "Finition lissée", "unit": "m²", "default_price": 38, "suggested_prices": {"mason": 32, "general": 45}},
        {"name": "Pose corniche staff", "description": "Moulure plâtre", "unit": "ml", "default_price": 35, "suggested_prices": {"mason": 28, "painter": 30, "general": 42}},
        {"name": "Pose rosace plafond", "description": "Décoration staff", "unit": "unité", "default_price": 120, "suggested_prices": {"mason": 100, "painter": 105, "general": 145}},
    ],
    "Rénovation & Divers": [
        # Main d'œuvre
        {"name": "Main d'œuvre qualifiée", "description": "Artisan qualifié", "unit": "heure", "default_price": 50, "suggested_prices": {"general": 50}},
        {"name": "Main d'œuvre aide/manœuvre", "description": "Assistant chantier", "unit": "heure", "default_price": 35, "suggested_prices": {"general": 35}},
        {"name": "Heures supplémentaires", "description": "Majoration 25%", "unit": "heure", "default_price": 62, "suggested_prices": {"general": 62}},
        {"name": "Travail samedi", "description": "Majoration 50%", "unit": "heure", "default_price": 75, "suggested_prices": {"general": 75}},
        {"name": "Travail dimanche/férié", "description": "Majoration 100%", "unit": "heure", "default_price": 100, "suggested_prices": {"general": 100}},
        # Déplacements
        {"name": "Déplacement zone 1 (< 20km)", "description": "Frais déplacement", "unit": "forfait", "default_price": 35, "suggested_prices": {"general": 35}},
        {"name": "Déplacement zone 2 (20-50km)", "description": "Frais déplacement", "unit": "forfait", "default_price": 55, "suggested_prices": {"general": 55}},
        {"name": "Déplacement zone 3 (> 50km)", "description": "Frais déplacement", "unit": "forfait", "default_price": 85, "suggested_prices": {"general": 85}},
        # Études et suivi
        {"name": "Étude technique sur site", "description": "Analyse et préconisations", "unit": "forfait", "default_price": 280, "suggested_prices": {"general": 280}},
        {"name": "Relevé de cotes complet", "description": "Métrés et plans côtés", "unit": "forfait", "default_price": 220, "suggested_prices": {"general": 220}},
        {"name": "Établissement devis détaillé", "description": "Devis complexe multi-lots", "unit": "forfait", "default_price": 180, "suggested_prices": {"general": 180}},
        {"name": "Suivi de chantier", "description": "Coordination travaux", "unit": "heure", "default_price": 75, "suggested_prices": {"general": 75}},
        {"name": "Réception de chantier", "description": "PV réception + levée réserves", "unit": "forfait", "default_price": 250, "suggested_prices": {"general": 250}},
        # Évacuation et nettoyage
        {"name": "Évacuation gravats", "description": "Chargement + déchetterie", "unit": "m³", "default_price": 95, "suggested_prices": {"general": 95}},
        {"name": "Location benne 8m³", "description": "Livraison + enlèvement", "unit": "semaine", "default_price": 380, "suggested_prices": {"general": 380}},
        {"name": "Protection chantier", "description": "Bâchage + protection meubles", "unit": "forfait", "default_price": 180, "suggested_prices": {"general": 180}},
        {"name": "Nettoyage fin de chantier", "description": "Nettoyage complet", "unit": "m²", "default_price": 10, "suggested_prices": {"general": 10}},
        {"name": "Nettoyage vitrerie fin chantier", "description": "Nettoyage vitres", "unit": "m²", "default_price": 8, "suggested_prices": {"general": 8}},
        # Fournitures
        {"name": "Fournitures diverses", "description": "Petit matériel consommable", "unit": "forfait", "default_price": 120, "suggested_prices": {"general": 120}},
        {"name": "Location outillage spécifique", "description": "Matériel spécialisé", "unit": "jour", "default_price": 85, "suggested_prices": {"general": 85}},
        {"name": "Location échafaudage", "description": "Échafaudage roulant", "unit": "semaine", "default_price": 180, "suggested_prices": {"general": 180}},
        {"name": "Location nacelle élévatrice", "description": "Travaux en hauteur", "unit": "jour", "default_price": 280, "suggested_prices": {"general": 280}},
    ]
}

# Simplified kits (without subcategory references)
SEED_KITS_SIMPLE = [
    {
        "name": "Installation électrique appartement T3",
        "business_type": "electrician",
        "description": "Kit complet pour installation électrique 60-80m²",
        "items_refs": [
            ("Électricité", "Installation prise électrique 16A", 18),
            ("Électricité", "Installation interrupteur simple", 12),
            ("Électricité", "Pose luminaire plafonnier", 8),
            ("Électricité", "Installation spot encastré LED", 12),
            ("Électricité", "Remplacement tableau électrique", 1),
            ("Électricité", "Tirage de câble sous gaine", 150),
            ("Électricité", "Mise à la terre", 1),
        ]
    },
    {
        "name": "Rénovation tableau électrique",
        "business_type": "electrician",
        "description": "Mise aux normes et remplacement tableau",
        "items_refs": [
            ("Électricité", "Remplacement tableau électrique", 1),
            ("Électricité", "Installation disjoncteur divisionnaire", 8),
            ("Électricité", "Installation parafoudre", 1),
            ("Électricité", "Mise à la terre", 1),
            ("Électricité", "Diagnostic électrique", 1),
        ]
    },
    {
        "name": "Rénovation salle de bain complète",
        "business_type": "plumber",
        "description": "Rénovation complète SDB 6-8m²",
        "items_refs": [
            ("Plomberie", "Création douche à l'italienne", 1),
            ("Plomberie", "Installation WC suspendu complet", 1),
            ("Plomberie", "Installation meuble vasque", 1),
            ("Chauffage & Climatisation", "Installation sèche-serviettes électrique", 1),
            ("Chauffage & Climatisation", "Installation chauffe-eau électrique 100L", 1),
        ]
    },
    {
        "name": "Installation réseau bureau 10 postes",
        "business_type": "it_installer",
        "description": "Infrastructure réseau bureau complet",
        "items_refs": [
            ("Réseaux & Courants Faibles", "Installation prise RJ45 cat.6", 12),
            ("Réseaux & Courants Faibles", "Tirage câble réseau cat.6", 100),
            ("Réseaux & Courants Faibles", "Installation baie de brassage 10U", 1),
            ("Réseaux & Courants Faibles", "Installation switch 24 ports", 1),
            ("Réseaux & Courants Faibles", "Configuration routeur/box Internet", 1),
            ("Réseaux & Courants Faibles", "Installation borne WiFi professionnelle", 2),
            ("Réseaux & Courants Faibles", "Test et certification câblage", 12),
        ]
    },
    {
        "name": "Rénovation appartement clé en main",
        "business_type": "general",
        "description": "Rénovation complète 50-70m²",
        "items_refs": [
            ("Maçonnerie", "Démolition cloison légère", 15),
            ("Carrelage & Sols", "Dépose carrelage existant", 25),
            ("Rénovation & Divers", "Évacuation gravats", 3),
            ("Peinture & Revêtements", "Enduit de lissage", 120),
            ("Peinture & Revêtements", "Peinture mur acrylique 2 couches", 120),
            ("Peinture & Revêtements", "Peinture plafond mat", 55),
            ("Carrelage & Sols", "Pose parquet flottant stratifié", 55),
            ("Rénovation & Divers", "Nettoyage fin de chantier", 55),
        ]
    },
    {
        "name": "Peinture appartement T3",
        "business_type": "painter",
        "description": "Peinture complète 60-70m²",
        "items_refs": [
            ("Peinture & Revêtements", "Enduit de rebouchage", 100),
            ("Peinture & Revêtements", "Ponçage murs/plafonds", 100),
            ("Peinture & Revêtements", "Sous-couche impression", 100),
            ("Peinture & Revêtements", "Peinture mur acrylique 2 couches", 100),
            ("Peinture & Revêtements", "Peinture plafond mat", 55),
            ("Peinture & Revêtements", "Peinture porte 2 faces + huisserie", 5),
            ("Peinture & Revêtements", "Peinture boiseries laque satinée", 40),
        ]
    },
    {
        "name": "Création salle de bain maçonnerie",
        "business_type": "mason",
        "description": "Travaux maçonnerie pour SDB",
        "items_refs": [
            ("Maçonnerie", "Démolition cloison légère", 8),
            ("Maçonnerie", "Coulage chape béton", 6),
            ("Maçonnerie", "Ragréage sol autolissant", 6),
            ("Plâtrerie & Isolation", "Cloison placo hydrofuge", 12),
            ("Rénovation & Divers", "Évacuation gravats", 1),
        ]
    },
    {
        "name": "Installation climatisation maison",
        "business_type": "plumber",
        "description": "Climatisation multi-split 3 pièces",
        "items_refs": [
            ("Chauffage & Climatisation", "Installation climatisation multi-split 2 unités", 1),
            ("Chauffage & Climatisation", "Installation climatisation mono-split", 1),
            ("Électricité", "Tirage de câble sous gaine", 30),
            ("Électricité", "Installation disjoncteur divisionnaire", 2),
        ]
    }
]


# ============== SERVICE CLASS ==============

class CategoryServiceSimple:
    """Simplified service for managing categories and items (no subcategories)"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.categories = db.service_categories_simple
        self.items = db.service_items_simple
        self.kits = db.service_kits_simple
    
    async def init_indexes(self) -> None:
        """Create necessary indexes"""
        try:
            await self.categories.create_index("name", unique=True)
            await self.categories.create_index("business_types")
            
            await self.items.create_index("category_id")
            await self.items.create_index([("category_id", 1), ("name", 1)])
            await self.items.create_index("name")
            
            await self.kits.create_index("business_type")
            await self.kits.create_index("name")
            
            logger.info("Category service (simplified) indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def seed_all(self, force: bool = False) -> Dict[str, int]:
        """Seed all categories, items, and kits"""
        stats = {"categories": 0, "items": 0, "kits": 0, "skipped": False}
        
        existing_count = await self.items.count_documents({})
        if existing_count > 0 and not force:
            logger.info(f"Data already seeded ({existing_count} items found). Skipping.")
            stats["skipped"] = True
            return stats
        
        if force:
            await self.categories.delete_many({})
            await self.items.delete_many({})
            await self.kits.delete_many({})
            logger.info("Force reseed: cleared existing data")
        
        now = datetime.now(timezone.utc).isoformat()
        category_map = {}  # name -> id
        item_map = {}  # (cat_name, item_name) -> id
        
        # Seed categories
        for cat_data in SEED_CATEGORIES_SIMPLE:
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
            except Exception as e:
                logger.warning(f"Error seeding category {cat_data['name']}: {e}")
        
        # Seed items
        for cat_name, items_list in SEED_ITEMS_SIMPLE.items():
            cat_id = category_map.get(cat_name)
            if not cat_id:
                logger.warning(f"Category not found: {cat_name}")
                continue
            
            for item_data in items_list:
                item_id = str(uuid.uuid4())
                item_doc = {
                    "id": item_id,
                    "category_id": cat_id,
                    "name": item_data["name"],
                    "description": item_data.get("description"),
                    "unit": item_data.get("unit", "unité"),
                    "default_price": item_data.get("default_price", 0),
                    "suggested_prices": item_data.get("suggested_prices", {}),
                    "created_at": now
                }
                await self.items.insert_one(item_doc)
                item_map[(cat_name, item_data["name"])] = item_id
                stats["items"] += 1
        
        # Seed kits
        for kit_data in SEED_KITS_SIMPLE:
            kit_id = str(uuid.uuid4())
            kit_items = []
            
            for cat_name, item_name, qty in kit_data["items_refs"]:
                item_id = item_map.get((cat_name, item_name))
                if item_id:
                    kit_items.append({
                        "service_item_id": item_id,
                        "quantity": qty
                    })
                else:
                    logger.warning(f"Kit item not found: {cat_name}/{item_name}")
            
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
        
        logger.info(f"Seeded {stats['categories']} categories, {stats['items']} items, {stats['kits']} kits")
        return stats
    
    # ============== CATEGORIES ==============
    
    async def get_categories_for_user(self, business_type: str = "general") -> List[Dict[str, Any]]:
        """Get categories filtered by user's business type"""
        if business_type not in VALID_BUSINESS_TYPES:
            business_type = "general"
        
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
        """Get all categories"""
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
    
    # ============== ITEMS ==============
    
    async def get_items_by_category(self, category_id: str, business_type: str = "general") -> List[Dict[str, Any]]:
        """Get items for a category with smart prices"""
        items = []
        cursor = self.items.find({"category_id": category_id}).sort("name", 1)
        
        async for doc in cursor:
            doc.pop("_id", None)
            # Add smart price based on business type
            suggested = doc.get("suggested_prices", {})
            if business_type in suggested and suggested[business_type] is not None:
                doc["smart_price"] = suggested[business_type]
            else:
                doc["smart_price"] = doc.get("default_price", 0)
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
        categories = await self.get_categories_for_user(business_type)
        category_ids = [c["id"] for c in categories]
        
        search_query = {
            "category_id": {"$in": category_ids},
            "name": {"$regex": query, "$options": "i"}
        }
        
        items = []
        cursor = self.items.find(search_query).limit(limit)
        
        async for doc in cursor:
            doc.pop("_id", None)
            suggested = doc.get("suggested_prices", {})
            if business_type in suggested and suggested[business_type] is not None:
                doc["smart_price"] = suggested[business_type]
            else:
                doc["smart_price"] = doc.get("default_price", 0)
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
    
    async def get_categories_with_items(self, business_type: str = "general") -> List[Dict[str, Any]]:
        """Get categories with their items (simplified structure)"""
        categories = await self.get_categories_for_user(business_type)
        
        result = []
        for cat in categories:
            items = await self.get_items_by_category(cat["id"], business_type)
            result.append({
                **cat,
                "items": items
            })
        
        return result
