from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from io import BytesIO
import base64
import resend

# ReportLab imports for PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Resend configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'btp-invoice-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== MODELS ==============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ClientCreate(BaseModel):
    name: str
    address: str = ""
    phone: str = ""
    email: str = ""

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class ClientResponse(BaseModel):
    id: str
    name: str
    address: str
    phone: str
    email: str
    created_at: str

class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    vat_rate: float = 20.0

class QuoteCreate(BaseModel):
    client_id: str
    validity_days: int = 30
    items: List[LineItem]
    notes: str = ""

class QuoteUpdate(BaseModel):
    client_id: Optional[str] = None
    validity_days: Optional[int] = None
    items: Optional[List[LineItem]] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class QuoteResponse(BaseModel):
    id: str
    quote_number: str
    client_id: str
    client_name: str
    issue_date: str
    validity_date: str
    items: List[dict]
    total_ht: float
    total_vat: float
    total_ttc: float
    status: str
    notes: str
    created_at: str
    share_token: Optional[str] = None

class InvoiceCreate(BaseModel):
    client_id: str
    quote_id: Optional[str] = None
    items: List[LineItem]
    notes: str = ""
    payment_method: str = "virement"
    payment_delay_days: Optional[int] = None  # If None, use company default

class InvoiceUpdate(BaseModel):
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    paid_amount: Optional[float] = None
    notes: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    client_id: str
    client_name: str
    quote_id: Optional[str]
    issue_date: str
    payment_due_date: str
    items: List[dict]
    total_ht: float
    total_vat: float
    total_ttc: float
    payment_status: str
    payment_method: str
    paid_amount: float
    notes: str
    created_at: str
    share_token: Optional[str] = None
    # Acompte fields
    is_acompte: bool = False
    acompte_type: Optional[str] = None
    acompte_value: Optional[float] = None
    parent_quote_id: Optional[str] = None
    acompte_number: Optional[int] = None
    # Situation fields
    is_situation: bool = False
    situation_number: Optional[int] = None
    situation_percentage: Optional[float] = None  # Current cumulative %
    previous_percentage: Optional[float] = None  # Previous cumulative %
    chantier_ref: Optional[str] = None

# ============== ACOMPTE MODELS ==============

class AcompteCreate(BaseModel):
    quote_id: str
    acompte_type: str  # "percentage" or "amount"
    value: float  # percentage (e.g., 30) or amount (e.g., 1000)
    notes: str = ""
    payment_method: str = "virement"

class AcompteResponse(BaseModel):
    id: str
    invoice_number: str
    quote_id: str
    quote_number: str
    client_id: str
    client_name: str
    issue_date: str
    payment_due_date: str
    acompte_type: str
    acompte_value: float
    acompte_number: int
    total_ht: float
    total_vat: float
    total_ttc: float
    payment_status: str
    payment_method: str
    paid_amount: float
    notes: str
    created_at: str

# ============== SITUATION MODELS ==============

class SituationLineItem(BaseModel):
    """Line item with progress percentage for per-line situation"""
    description: str
    quantity: float
    unit_price: float
    vat_rate: float = 20.0
    progress_percent: float  # % of this line completed in this situation

class SituationCreate(BaseModel):
    quote_id: str
    situation_type: str  # "global" or "per_line"
    global_percentage: Optional[float] = None  # For global type: cumulative %
    line_items: Optional[List[SituationLineItem]] = None  # For per_line type
    notes: str = ""
    payment_method: str = "virement"
    chantier_ref: str = ""  # Optional site reference

class SituationResponse(BaseModel):
    id: str
    invoice_number: str
    quote_id: str
    quote_number: str
    client_id: str
    client_name: str
    issue_date: str
    payment_due_date: str
    situation_type: str
    situation_number: int
    current_percentage: float  # Current cumulative %
    previous_percentage: float  # Previous cumulative %
    situation_percentage: float  # % for this situation only (current - previous)
    items: List[dict]
    total_ht: float
    total_vat: float
    total_ttc: float
    payment_status: str
    payment_method: str
    paid_amount: float
    notes: str
    chantier_ref: str
    created_at: str

class CompanySettings(BaseModel):
    company_name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    siret: str = ""
    vat_number: str = ""
    default_vat_rates: List[float] = [20.0, 10.0, 5.5, 2.1]
    logo_base64: Optional[str] = None
    # New fields for French legal compliance
    rcs_rm: str = ""  # RCS ou RM (Registre des Métiers)
    code_ape: str = ""  # Code APE/NAF
    capital_social: str = ""  # Capital social
    iban: str = ""  # IBAN for bank payments
    bic: str = ""  # BIC/SWIFT code
    # Auto-entrepreneur mode
    is_auto_entrepreneur: bool = False  # If true, hide TVA
    auto_entrepreneur_mention: str = "TVA non applicable, art. 293B du CGI"
    # Payment settings
    default_payment_delay_days: int = 30  # Default payment delay
    late_payment_rate: float = 3.0  # Late payment interest rate (x3 BCE rate)

class DashboardStats(BaseModel):
    total_turnover: float
    unpaid_invoices_count: int
    unpaid_invoices_amount: float
    pending_quotes_count: int
    total_clients: int
    total_quotes: int
    total_invoices: int

# ============== RENOVATION KITS MODELS ==============

class KitItem(BaseModel):
    description: str
    unit: str = "unité"
    quantity: float = 1.0
    unit_price: float = 0.0
    vat_rate: float = 20.0

class KitCreate(BaseModel):
    name: str
    description: str = ""
    items: List[KitItem]
    is_default: bool = False

class KitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[KitItem]] = None

class KitResponse(BaseModel):
    id: str
    name: str
    description: str
    items: List[dict]
    is_default: bool
    created_at: str

# Default renovation kits
DEFAULT_RENOVATION_KITS = [
    {
        "name": "Rénovation salle de bain",
        "description": "Kit complet pour la rénovation d'une salle de bain standard",
        "items": [
            {"description": "Démolition / Dépose sanitaires existants", "unit": "forfait", "quantity": 1, "unit_price": 450.0, "vat_rate": 20.0},
            {"description": "Plomberie - Alimentation et évacuation", "unit": "forfait", "quantity": 1, "unit_price": 850.0, "vat_rate": 20.0},
            {"description": "Carrelage sol", "unit": "m²", "quantity": 8, "unit_price": 55.0, "vat_rate": 20.0},
            {"description": "Carrelage mural / Faïence", "unit": "m²", "quantity": 15, "unit_price": 60.0, "vat_rate": 20.0},
            {"description": "Peinture plafond (2 couches)", "unit": "m²", "quantity": 8, "unit_price": 22.0, "vat_rate": 20.0},
            {"description": "Installation sanitaires (WC, lavabo, douche)", "unit": "forfait", "quantity": 1, "unit_price": 650.0, "vat_rate": 20.0},
        ]
    },
    {
        "name": "Installation cuisine",
        "description": "Kit pour l'installation complète d'une cuisine équipée",
        "items": [
            {"description": "Dépose ancienne cuisine", "unit": "forfait", "quantity": 1, "unit_price": 350.0, "vat_rate": 20.0},
            {"description": "Installation meubles de cuisine", "unit": "ml", "quantity": 5, "unit_price": 180.0, "vat_rate": 20.0},
            {"description": "Installation électroménager", "unit": "unité", "quantity": 4, "unit_price": 85.0, "vat_rate": 20.0},
            {"description": "Plomberie - Évier et lave-vaisselle", "unit": "forfait", "quantity": 1, "unit_price": 380.0, "vat_rate": 20.0},
            {"description": "Électricité - Prises et raccordements", "unit": "forfait", "quantity": 1, "unit_price": 450.0, "vat_rate": 20.0},
            {"description": "Crédence et finitions", "unit": "ml", "quantity": 3, "unit_price": 120.0, "vat_rate": 20.0},
        ]
    },
    {
        "name": "Rénovation électrique complète",
        "description": "Mise aux normes et rénovation complète de l'installation électrique",
        "items": [
            {"description": "Tableau électrique avec disjoncteurs", "unit": "unité", "quantity": 1, "unit_price": 950.0, "vat_rate": 20.0},
            {"description": "Tirage de câbles", "unit": "ml", "quantity": 80, "unit_price": 12.0, "vat_rate": 20.0},
            {"description": "Pose prises électriques", "unit": "unité", "quantity": 15, "unit_price": 65.0, "vat_rate": 20.0},
            {"description": "Pose interrupteurs", "unit": "unité", "quantity": 8, "unit_price": 55.0, "vat_rate": 20.0},
            {"description": "Mise en conformité NF C 15-100", "unit": "forfait", "quantity": 1, "unit_price": 350.0, "vat_rate": 20.0},
        ]
    }
]

# ============== PREDEFINED ITEMS MODELS ==============

class PredefinedItemCreate(BaseModel):
    category: str
    description: str
    unit: str = "unité"
    default_price: float = 0.0
    default_vat_rate: float = 20.0

class PredefinedItemUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    default_price: Optional[float] = None
    default_vat_rate: Optional[float] = None

class PredefinedItemResponse(BaseModel):
    id: str
    category: str
    description: str
    unit: str
    default_price: float
    default_vat_rate: float

class CategoryResponse(BaseModel):
    name: str
    items: List[PredefinedItemResponse]

# Default BTP categories and items
DEFAULT_BTP_CATEGORIES = {
    "Menuiserie": [
        {"description": "Pose de porte intérieure", "unit": "unité", "default_price": 250.0},
        {"description": "Pose de fenêtre PVC", "unit": "unité", "default_price": 350.0},
        {"description": "Pose de porte-fenêtre", "unit": "unité", "default_price": 450.0},
        {"description": "Pose de volet roulant", "unit": "unité", "default_price": 300.0},
        {"description": "Pose de parquet flottant", "unit": "m²", "default_price": 35.0},
        {"description": "Pose de parquet massif", "unit": "m²", "default_price": 55.0},
        {"description": "Pose de plinthes", "unit": "ml", "default_price": 12.0},
    ],
    "Plomberie": [
        {"description": "Installation WC complet", "unit": "unité", "default_price": 450.0},
        {"description": "Installation lavabo", "unit": "unité", "default_price": 280.0},
        {"description": "Installation douche complète", "unit": "unité", "default_price": 850.0},
        {"description": "Installation baignoire", "unit": "unité", "default_price": 650.0},
        {"description": "Pose de chauffe-eau", "unit": "unité", "default_price": 380.0},
        {"description": "Remplacement robinetterie", "unit": "unité", "default_price": 120.0},
        {"description": "Création point d'eau", "unit": "unité", "default_price": 350.0},
    ],
    "Électricité": [
        {"description": "Pose de prise électrique", "unit": "unité", "default_price": 65.0},
        {"description": "Pose d'interrupteur", "unit": "unité", "default_price": 55.0},
        {"description": "Pose de spot encastré", "unit": "unité", "default_price": 45.0},
        {"description": "Pose de tableau électrique", "unit": "unité", "default_price": 850.0},
        {"description": "Tirage de câble", "unit": "ml", "default_price": 15.0},
        {"description": "Mise aux normes électriques", "unit": "forfait", "default_price": 1200.0},
        {"description": "Pose de VMC", "unit": "unité", "default_price": 450.0},
    ],
    "Peinture": [
        {"description": "Peinture mur (2 couches)", "unit": "m²", "default_price": 18.0},
        {"description": "Peinture plafond (2 couches)", "unit": "m²", "default_price": 22.0},
        {"description": "Peinture boiseries", "unit": "ml", "default_price": 15.0},
        {"description": "Pose de papier peint", "unit": "m²", "default_price": 25.0},
        {"description": "Préparation des surfaces", "unit": "m²", "default_price": 8.0},
        {"description": "Lessivage des murs", "unit": "m²", "default_price": 5.0},
    ],
    "Maçonnerie": [
        {"description": "Création de mur en parpaings", "unit": "m²", "default_price": 85.0},
        {"description": "Création d'ouverture", "unit": "unité", "default_price": 650.0},
        {"description": "Coulage de dalle béton", "unit": "m²", "default_price": 75.0},
        {"description": "Ragréage sol", "unit": "m²", "default_price": 25.0},
        {"description": "Chape traditionnelle", "unit": "m²", "default_price": 35.0},
        {"description": "Démolition de cloison", "unit": "m²", "default_price": 45.0},
    ],
    "Carrelage": [
        {"description": "Pose de carrelage sol", "unit": "m²", "default_price": 45.0},
        {"description": "Pose de carrelage mural", "unit": "m²", "default_price": 55.0},
        {"description": "Pose de faïence", "unit": "m²", "default_price": 50.0},
        {"description": "Pose de mosaïque", "unit": "m²", "default_price": 75.0},
        {"description": "Pose de plinthes carrelage", "unit": "ml", "default_price": 15.0},
        {"description": "Jointage carrelage", "unit": "m²", "default_price": 12.0},
    ],
    "Plâtrerie / Isolation": [
        {"description": "Pose de placo BA13", "unit": "m²", "default_price": 28.0},
        {"description": "Pose de placo hydrofuge", "unit": "m²", "default_price": 35.0},
        {"description": "Création faux plafond", "unit": "m²", "default_price": 45.0},
        {"description": "Isolation laine de verre", "unit": "m²", "default_price": 25.0},
        {"description": "Isolation laine de roche", "unit": "m²", "default_price": 30.0},
        {"description": "Bandes et joints placo", "unit": "m²", "default_price": 12.0},
        {"description": "Doublage isolant", "unit": "m²", "default_price": 40.0},
    ],
    "Rénovation générale": [
        {"description": "Main d'œuvre qualifiée", "unit": "heure", "default_price": 45.0},
        {"description": "Main d'œuvre aide", "unit": "heure", "default_price": 30.0},
        {"description": "Déplacement", "unit": "forfait", "default_price": 50.0},
        {"description": "Évacuation gravats", "unit": "m³", "default_price": 85.0},
        {"description": "Nettoyage fin de chantier", "unit": "forfait", "default_price": 150.0},
        {"description": "Location benne", "unit": "jour", "default_price": 120.0},
    ],
}

# ============== AUTH HELPERS ==============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalide")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=user_data.email, name=user_data.name)
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], name=user["name"])
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(id=user["id"], email=user["email"], name=user["name"])

# ============== CLIENT ROUTES ==============

@api_router.post("/clients", response_model=ClientResponse)
async def create_client(client_data: ClientCreate, user: dict = Depends(get_current_user)):
    client_id = str(uuid.uuid4())
    client_doc = {
        "id": client_id,
        "name": client_data.name,
        "address": client_data.address,
        "phone": client_data.phone,
        "email": client_data.email,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.clients.insert_one(client_doc)
    return ClientResponse(**client_doc)

@api_router.get("/clients", response_model=List[ClientResponse])
async def list_clients(user: dict = Depends(get_current_user)):
    clients = await db.clients.find({}, {"_id": 0}).to_list(1000)
    return [ClientResponse(**c) for c in clients]

@api_router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, user: dict = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return ClientResponse(**client)

@api_router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, client_data: ClientUpdate, user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in client_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
    
    result = await db.clients.update_one({"id": client_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return ClientResponse(**client)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, user: dict = Depends(get_current_user)):
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return {"message": "Client supprimé"}

# ============== QUOTE HELPERS ==============

async def get_next_quote_number():
    year = datetime.now().year
    last_quote = await db.quotes.find_one(
        {"quote_number": {"$regex": f"^DEV-{year}"}},
        sort=[("quote_number", -1)]
    )
    if last_quote:
        last_num = int(last_quote["quote_number"].split("-")[-1])
        return f"DEV-{year}-{str(last_num + 1).zfill(4)}"
    return f"DEV-{year}-0001"

def calculate_totals(items: List[dict]):
    total_ht = 0
    total_vat = 0
    for item in items:
        line_ht = item["quantity"] * item["unit_price"]
        line_vat = line_ht * (item["vat_rate"] / 100)
        total_ht += line_ht
        total_vat += line_vat
    return round(total_ht, 2), round(total_vat, 2), round(total_ht + total_vat, 2)

# ============== QUOTE ROUTES ==============

@api_router.post("/quotes", response_model=QuoteResponse)
async def create_quote(quote_data: QuoteCreate, user: dict = Depends(get_current_user)):
    client = await db.clients.find_one({"id": quote_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    quote_id = str(uuid.uuid4())
    quote_number = await get_next_quote_number()
    issue_date = datetime.now(timezone.utc)
    validity_date = issue_date + timedelta(days=quote_data.validity_days)
    
    items = [item.model_dump() for item in quote_data.items]
    total_ht, total_vat, total_ttc = calculate_totals(items)
    
    quote_doc = {
        "id": quote_id,
        "quote_number": quote_number,
        "client_id": quote_data.client_id,
        "client_name": client["name"],
        "issue_date": issue_date.isoformat(),
        "validity_date": validity_date.isoformat(),
        "items": items,
        "total_ht": total_ht,
        "total_vat": total_vat,
        "total_ttc": total_ttc,
        "status": "brouillon",
        "notes": quote_data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.quotes.insert_one(quote_doc)
    return QuoteResponse(**quote_doc)

@api_router.get("/quotes", response_model=List[QuoteResponse])
async def list_quotes(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    quotes = await db.quotes.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [QuoteResponse(**q) for q in quotes]

@api_router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: str, user: dict = Depends(get_current_user)):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    return QuoteResponse(**quote)

@api_router.put("/quotes/{quote_id}", response_model=QuoteResponse)
async def update_quote(quote_id: str, quote_data: QuoteUpdate, user: dict = Depends(get_current_user)):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    update_data = {}
    if quote_data.client_id:
        client = await db.clients.find_one({"id": quote_data.client_id}, {"_id": 0})
        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        update_data["client_id"] = quote_data.client_id
        update_data["client_name"] = client["name"]
    
    if quote_data.validity_days:
        issue_date = datetime.fromisoformat(quote["issue_date"].replace('Z', '+00:00'))
        validity_date = issue_date + timedelta(days=quote_data.validity_days)
        update_data["validity_date"] = validity_date.isoformat()
    
    if quote_data.items:
        items = [item.model_dump() for item in quote_data.items]
        total_ht, total_vat, total_ttc = calculate_totals(items)
        update_data["items"] = items
        update_data["total_ht"] = total_ht
        update_data["total_vat"] = total_vat
        update_data["total_ttc"] = total_ttc
    
    if quote_data.notes is not None:
        update_data["notes"] = quote_data.notes
    
    if quote_data.status:
        update_data["status"] = quote_data.status
    
    if update_data:
        await db.quotes.update_one({"id": quote_id}, {"$set": update_data})
    
    updated_quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    return QuoteResponse(**updated_quote)

@api_router.delete("/quotes/{quote_id}")
async def delete_quote(quote_id: str, user: dict = Depends(get_current_user)):
    result = await db.quotes.delete_one({"id": quote_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    return {"message": "Devis supprimé"}

@api_router.post("/quotes/{quote_id}/convert", response_model=InvoiceResponse)
async def convert_quote_to_invoice(quote_id: str, user: dict = Depends(get_current_user)):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote["status"] != "accepte":
        raise HTTPException(status_code=400, detail="Seuls les devis acceptés peuvent être convertis en facture")
    
    # Get company settings for payment delay
    settings = await get_company_settings()
    
    invoice_id = str(uuid.uuid4())
    invoice_number = await get_next_invoice_number()
    
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=settings.default_payment_delay_days)
    
    # Handle auto-entrepreneur mode
    items = quote["items"]
    if settings.is_auto_entrepreneur:
        items = [{**item, "vat_rate": 0.0} for item in items]
        total_ht = sum(item["quantity"] * item["unit_price"] for item in items)
        total_vat = 0.0
        total_ttc = total_ht
    else:
        total_ht = quote["total_ht"]
        total_vat = quote["total_vat"]
        total_ttc = quote["total_ttc"]
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": items,
        "total_ht": total_ht,
        "total_vat": total_vat,
        "total_ttc": total_ttc,
        "payment_status": "impaye",
        "payment_method": "virement",
        "paid_amount": 0,
        "notes": quote["notes"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.invoices.insert_one(invoice_doc)
    
    # Update quote status
    await db.quotes.update_one({"id": quote_id}, {"$set": {"status": "facture"}})
    
    return InvoiceResponse(**invoice_doc)

# ============== INVOICE HELPERS ==============

async def get_next_invoice_number():
    year = datetime.now().year
    last_invoice = await db.invoices.find_one(
        {"invoice_number": {"$regex": f"^FAC-{year}"}},
        sort=[("invoice_number", -1)]
    )
    if last_invoice:
        last_num = int(last_invoice["invoice_number"].split("-")[-1])
        return f"FAC-{year}-{str(last_num + 1).zfill(4)}"
    return f"FAC-{year}-0001"

# ============== INVOICE ROUTES ==============

@api_router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(invoice_data: InvoiceCreate, user: dict = Depends(get_current_user)):
    client = await db.clients.find_one({"id": invoice_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    # Get company settings for default payment delay
    settings = await get_company_settings()
    payment_delay = invoice_data.payment_delay_days or settings.default_payment_delay_days
    
    invoice_id = str(uuid.uuid4())
    invoice_number = await get_next_invoice_number()
    
    items = [item.model_dump() for item in invoice_data.items]
    
    # Handle auto-entrepreneur mode (no VAT)
    if settings.is_auto_entrepreneur:
        for item in items:
            item["vat_rate"] = 0.0
        total_ht = sum(item["quantity"] * item["unit_price"] for item in items)
        total_vat = 0.0
        total_ttc = total_ht
    else:
        total_ht, total_vat, total_ttc = calculate_totals(items)
    
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=payment_delay)
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "client_id": invoice_data.client_id,
        "client_name": client["name"],
        "quote_id": invoice_data.quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": items,
        "total_ht": total_ht,
        "total_vat": total_vat,
        "total_ttc": total_ttc,
        "payment_status": "impaye",
        "payment_method": invoice_data.payment_method,
        "paid_amount": 0,
        "notes": invoice_data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.invoices.insert_one(invoice_doc)
    return InvoiceResponse(**invoice_doc)

@api_router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(payment_status: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {}
    if payment_status:
        query["payment_status"] = payment_status
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    # Add default fields for compatibility
    for inv in invoices:
        if "payment_due_date" not in inv:
            issue_date = datetime.fromisoformat(inv["issue_date"].replace("Z", "+00:00"))
            inv["payment_due_date"] = (issue_date + timedelta(days=30)).isoformat()
        # Add acompte defaults
        inv.setdefault("is_acompte", False)
        inv.setdefault("acompte_type", None)
        inv.setdefault("acompte_value", None)
        inv.setdefault("parent_quote_id", None)
        inv.setdefault("acompte_number", None)
    return [InvoiceResponse(**i) for i in invoices]

@api_router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    # Add default fields for compatibility
    if "payment_due_date" not in invoice:
        issue_date = datetime.fromisoformat(invoice["issue_date"].replace("Z", "+00:00"))
        invoice["payment_due_date"] = (issue_date + timedelta(days=30)).isoformat()
    # Add acompte defaults
    invoice.setdefault("is_acompte", False)
    invoice.setdefault("acompte_type", None)
    invoice.setdefault("acompte_value", None)
    invoice.setdefault("parent_quote_id", None)
    invoice.setdefault("acompte_number", None)
    return InvoiceResponse(**invoice)

@api_router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: str, invoice_data: InvoiceUpdate, user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    update_data = {}
    if invoice_data.payment_status:
        update_data["payment_status"] = invoice_data.payment_status
    if invoice_data.payment_method:
        update_data["payment_method"] = invoice_data.payment_method
    if invoice_data.paid_amount is not None:
        update_data["paid_amount"] = invoice_data.paid_amount
        # Auto-update payment status based on paid amount
        if invoice_data.paid_amount >= invoice["total_ttc"]:
            update_data["payment_status"] = "paye"
        elif invoice_data.paid_amount > 0:
            update_data["payment_status"] = "partiel"
    if invoice_data.notes is not None:
        update_data["notes"] = invoice_data.notes
    
    if update_data:
        await db.invoices.update_one({"id": invoice_id}, {"$set": update_data})
    
    updated_invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    return InvoiceResponse(**updated_invoice)

@api_router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    result = await db.invoices.delete_one({"id": invoice_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return {"message": "Facture supprimée"}

# ============== ACOMPTES (ADVANCE PAYMENTS) ==============

@api_router.post("/quotes/{quote_id}/acompte", response_model=AcompteResponse)
async def create_acompte(quote_id: str, acompte_data: AcompteCreate, user: dict = Depends(get_current_user)):
    """Create an acompte (advance payment invoice) from a quote"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote["status"] not in ["accepte", "envoye"]:
        raise HTTPException(status_code=400, detail="Le devis doit être accepté ou envoyé pour créer un acompte")
    
    # Get company settings
    settings = await get_company_settings()
    
    # Calculate acompte amounts
    if acompte_data.acompte_type == "percentage":
        acompte_ht = quote["total_ht"] * (acompte_data.value / 100)
        acompte_vat = quote["total_vat"] * (acompte_data.value / 100) if not settings.is_auto_entrepreneur else 0
    else:  # amount
        # If amount, we need to calculate proportional VAT
        proportion = acompte_data.value / quote["total_ttc"] if quote["total_ttc"] > 0 else 0
        acompte_ht = quote["total_ht"] * proportion
        acompte_vat = quote["total_vat"] * proportion if not settings.is_auto_entrepreneur else 0
    
    acompte_ttc = acompte_ht + acompte_vat
    
    # Get existing acomptes for this quote to determine the number
    existing_acomptes = await db.invoices.count_documents({"parent_quote_id": quote_id, "is_acompte": True})
    acompte_number = existing_acomptes + 1
    
    # Generate invoice number
    invoice_number = await get_next_invoice_number()
    
    # Calculate payment due date
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=settings.default_payment_delay_days)
    
    # Create acompte items (simplified - shows as single line)
    acompte_items = [{
        "description": f"Acompte n°{acompte_number} - {acompte_data.value}{'%' if acompte_data.acompte_type == 'percentage' else '€'} sur devis {quote['quote_number']}",
        "quantity": 1,
        "unit_price": acompte_ht,
        "vat_rate": (acompte_vat / acompte_ht * 100) if acompte_ht > 0 else 0,
        "unit": "forfait"
    }]
    
    acompte_doc = {
        "id": str(uuid.uuid4()),
        "invoice_number": invoice_number,
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "parent_quote_id": quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": acompte_items,
        "total_ht": round(acompte_ht, 2),
        "total_vat": round(acompte_vat, 2),
        "total_ttc": round(acompte_ttc, 2),
        "payment_status": "impaye",
        "payment_method": acompte_data.payment_method,
        "paid_amount": 0,
        "notes": acompte_data.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        # Acompte specific fields
        "is_acompte": True,
        "acompte_type": acompte_data.acompte_type,
        "acompte_value": acompte_data.value,
        "acompte_number": acompte_number
    }
    
    await db.invoices.insert_one(acompte_doc)
    
    return AcompteResponse(
        id=acompte_doc["id"],
        invoice_number=acompte_doc["invoice_number"],
        quote_id=quote_id,
        quote_number=quote["quote_number"],
        client_id=acompte_doc["client_id"],
        client_name=acompte_doc["client_name"],
        issue_date=acompte_doc["issue_date"],
        payment_due_date=acompte_doc["payment_due_date"],
        acompte_type=acompte_doc["acompte_type"],
        acompte_value=acompte_doc["acompte_value"],
        acompte_number=acompte_doc["acompte_number"],
        total_ht=acompte_doc["total_ht"],
        total_vat=acompte_doc["total_vat"],
        total_ttc=acompte_doc["total_ttc"],
        payment_status=acompte_doc["payment_status"],
        payment_method=acompte_doc["payment_method"],
        paid_amount=acompte_doc["paid_amount"],
        notes=acompte_doc["notes"],
        created_at=acompte_doc["created_at"]
    )

@api_router.get("/quotes/{quote_id}/acomptes", response_model=List[AcompteResponse])
async def list_quote_acomptes(quote_id: str, user: dict = Depends(get_current_user)):
    """List all acomptes for a quote"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    acomptes = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_acompte": True},
        {"_id": 0}
    ).sort("acompte_number", 1).to_list(100)
    
    return [
        AcompteResponse(
            id=a["id"],
            invoice_number=a["invoice_number"],
            quote_id=quote_id,
            quote_number=quote["quote_number"],
            client_id=a["client_id"],
            client_name=a["client_name"],
            issue_date=a["issue_date"],
            payment_due_date=a.get("payment_due_date", a["issue_date"]),
            acompte_type=a["acompte_type"],
            acompte_value=a["acompte_value"],
            acompte_number=a["acompte_number"],
            total_ht=a["total_ht"],
            total_vat=a["total_vat"],
            total_ttc=a["total_ttc"],
            payment_status=a["payment_status"],
            payment_method=a["payment_method"],
            paid_amount=a.get("paid_amount", 0),
            notes=a.get("notes", ""),
            created_at=a["created_at"]
        )
        for a in acomptes
    ]

@api_router.get("/quotes/{quote_id}/acomptes/summary")
async def get_acomptes_summary(quote_id: str, user: dict = Depends(get_current_user)):
    """Get summary of acomptes for a quote (total paid, remaining)"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    acomptes = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_acompte": True},
        {"_id": 0}
    ).to_list(100)
    
    total_acomptes_ht = sum(a["total_ht"] for a in acomptes)
    total_acomptes_vat = sum(a["total_vat"] for a in acomptes)
    total_acomptes_ttc = sum(a["total_ttc"] for a in acomptes)
    total_paid = sum(a.get("paid_amount", 0) for a in acomptes if a["payment_status"] == "paye")
    
    remaining_ht = quote["total_ht"] - total_acomptes_ht
    remaining_vat = quote["total_vat"] - total_acomptes_vat
    remaining_ttc = quote["total_ttc"] - total_acomptes_ttc
    
    return {
        "quote_total_ht": quote["total_ht"],
        "quote_total_vat": quote["total_vat"],
        "quote_total_ttc": quote["total_ttc"],
        "acomptes_count": len(acomptes),
        "total_acomptes_ht": round(total_acomptes_ht, 2),
        "total_acomptes_vat": round(total_acomptes_vat, 2),
        "total_acomptes_ttc": round(total_acomptes_ttc, 2),
        "total_paid": round(total_paid, 2),
        "remaining_ht": round(max(0, remaining_ht), 2),
        "remaining_vat": round(max(0, remaining_vat), 2),
        "remaining_ttc": round(max(0, remaining_ttc), 2),
        "percentage_invoiced": round((total_acomptes_ttc / quote["total_ttc"] * 100) if quote["total_ttc"] > 0 else 0, 1),
        "percentage_paid": round((total_paid / quote["total_ttc"] * 100) if quote["total_ttc"] > 0 else 0, 1),
        "acomptes": [
            {
                "id": a["id"],
                "invoice_number": a["invoice_number"],
                "acompte_number": a["acompte_number"],
                "acompte_type": a["acompte_type"],
                "acompte_value": a["acompte_value"],
                "total_ttc": a["total_ttc"],
                "payment_status": a["payment_status"],
                "paid_amount": a.get("paid_amount", 0)
            }
            for a in acomptes
        ]
    }

@api_router.post("/quotes/{quote_id}/final-invoice", response_model=InvoiceResponse)
async def create_final_invoice(quote_id: str, user: dict = Depends(get_current_user)):
    """Create final invoice from quote, deducting all acomptes"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote["status"] != "accepte":
        raise HTTPException(status_code=400, detail="Le devis doit être accepté pour créer la facture finale")
    
    # Get company settings
    settings = await get_company_settings()
    
    # Get all paid acomptes
    acomptes = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_acompte": True},
        {"_id": 0}
    ).to_list(100)
    
    total_acomptes_ttc = sum(a["total_ttc"] for a in acomptes if a["payment_status"] == "paye")
    
    invoice_id = str(uuid.uuid4())
    invoice_number = await get_next_invoice_number()
    
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=settings.default_payment_delay_days)
    
    # Handle auto-entrepreneur mode
    items = quote["items"]
    if settings.is_auto_entrepreneur:
        items = [{**item, "vat_rate": 0.0} for item in items]
        total_ht = sum(item["quantity"] * item["unit_price"] for item in items)
        total_vat = 0.0
        total_ttc = total_ht
    else:
        total_ht = quote["total_ht"]
        total_vat = quote["total_vat"]
        total_ttc = quote["total_ttc"]
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "parent_quote_id": quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": items,
        "total_ht": total_ht,
        "total_vat": total_vat,
        "total_ttc": total_ttc,
        "payment_status": "impaye",
        "payment_method": "virement",
        "paid_amount": 0,
        "notes": quote.get("notes", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        # Final invoice specific
        "is_acompte": False,
        "is_final_invoice": True,
        "acomptes_deducted": total_acomptes_ttc,
        "net_to_pay": round(total_ttc - total_acomptes_ttc, 2)
    }
    
    await db.invoices.insert_one(invoice_doc)
    
    # Update quote status
    await db.quotes.update_one({"id": quote_id}, {"$set": {"status": "facture"}})
    
    # Add default values for missing fields
    invoice_doc["acompte_type"] = None
    invoice_doc["acompte_value"] = None
    invoice_doc["acompte_number"] = None
    
    return InvoiceResponse(**invoice_doc)

# ============== SITUATIONS (PROGRESSIVE BILLING) ==============

@api_router.post("/quotes/{quote_id}/situation", response_model=SituationResponse)
async def create_situation(quote_id: str, situation_data: SituationCreate, user: dict = Depends(get_current_user)):
    """Create a situation invoice (progressive billing) from a quote"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote["status"] not in ["accepte", "envoye"]:
        raise HTTPException(status_code=400, detail="Le devis doit être accepté ou envoyé pour créer une situation")
    
    # Get company settings
    settings = await get_company_settings()
    
    # Get existing situations for this quote to determine the number and previous %
    existing_situations = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_situation": True},
        {"_id": 0}
    ).sort("situation_number", -1).to_list(100)
    
    situation_number = len(existing_situations) + 1
    
    # Calculate previous cumulative percentage
    if existing_situations:
        previous_percentage = existing_situations[0].get("situation_percentage", 0) or 0
    else:
        previous_percentage = 0
    
    # Calculate current situation based on type
    if situation_data.situation_type == "global":
        # Global percentage mode
        if situation_data.global_percentage is None or situation_data.global_percentage <= 0:
            raise HTTPException(status_code=400, detail="Le pourcentage global doit être supérieur à 0")
        
        if situation_data.global_percentage > 100:
            raise HTTPException(status_code=400, detail="Le pourcentage ne peut pas dépasser 100%")
        
        if situation_data.global_percentage <= previous_percentage:
            raise HTTPException(
                status_code=400, 
                detail=f"Le pourcentage ({situation_data.global_percentage}%) doit être supérieur au cumul précédent ({previous_percentage}%)"
            )
        
        current_percentage = situation_data.global_percentage
        situation_percentage = current_percentage - previous_percentage
        
        # Calculate amounts for this situation
        situation_ht = quote["total_ht"] * (situation_percentage / 100)
        situation_vat = quote["total_vat"] * (situation_percentage / 100) if not settings.is_auto_entrepreneur else 0
        situation_ttc = situation_ht + situation_vat
        
        # Create situation items (proportional to situation %)
        situation_items = []
        for item in quote["items"]:
            item_ht = item["quantity"] * item["unit_price"] * (situation_percentage / 100)
            situation_items.append({
                "description": item["description"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "vat_rate": 0.0 if settings.is_auto_entrepreneur else item["vat_rate"],
                "situation_percent": situation_percentage,
                "original_total_ht": item["quantity"] * item["unit_price"],
                "situation_amount_ht": round(item_ht, 2)
            })
    
    else:  # per_line mode
        if not situation_data.line_items or len(situation_data.line_items) == 0:
            raise HTTPException(status_code=400, detail="Les lignes de situation sont requises pour le mode par ligne")
        
        if len(situation_data.line_items) != len(quote["items"]):
            raise HTTPException(status_code=400, detail="Le nombre de lignes doit correspondre au devis")
        
        # Get previous line-by-line progress
        previous_line_progress = {}
        if existing_situations:
            last_situation = existing_situations[0]
            for item in last_situation.get("items", []):
                previous_line_progress[item.get("description", "")] = item.get("cumulative_percent", 0)
        
        situation_items = []
        total_situation_ht = 0
        total_situation_vat = 0
        
        for i, (quote_item, sit_item) in enumerate(zip(quote["items"], situation_data.line_items)):
            prev_progress = previous_line_progress.get(quote_item["description"], 0)
            
            if sit_item.progress_percent < prev_progress:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ligne {i+1}: le % ({sit_item.progress_percent}%) ne peut pas être inférieur au cumul précédent ({prev_progress}%)"
                )
            
            if sit_item.progress_percent > 100:
                raise HTTPException(status_code=400, detail=f"Ligne {i+1}: le pourcentage ne peut pas dépasser 100%")
            
            line_situation_percent = sit_item.progress_percent - prev_progress
            item_base_ht = quote_item["quantity"] * quote_item["unit_price"]
            item_situation_ht = item_base_ht * (line_situation_percent / 100)
            item_situation_vat = item_situation_ht * (quote_item["vat_rate"] / 100) if not settings.is_auto_entrepreneur else 0
            
            total_situation_ht += item_situation_ht
            total_situation_vat += item_situation_vat
            
            situation_items.append({
                "description": quote_item["description"],
                "quantity": quote_item["quantity"],
                "unit_price": quote_item["unit_price"],
                "vat_rate": 0.0 if settings.is_auto_entrepreneur else quote_item["vat_rate"],
                "situation_percent": line_situation_percent,
                "cumulative_percent": sit_item.progress_percent,
                "original_total_ht": item_base_ht,
                "situation_amount_ht": round(item_situation_ht, 2)
            })
        
        situation_ht = total_situation_ht
        situation_vat = total_situation_vat
        situation_ttc = situation_ht + situation_vat
        
        # Calculate average progress for current_percentage
        total_weight = sum(item["original_total_ht"] for item in situation_items)
        if total_weight > 0:
            current_percentage = sum(
                item["cumulative_percent"] * item["original_total_ht"] / total_weight 
                for item in situation_items
            )
        else:
            current_percentage = 0
        
        situation_percentage = current_percentage - previous_percentage
    
    # Generate invoice number
    invoice_number = await get_next_invoice_number()
    
    # Calculate payment due date
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=settings.default_payment_delay_days)
    
    situation_doc = {
        "id": str(uuid.uuid4()),
        "invoice_number": invoice_number,
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "parent_quote_id": quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": situation_items,
        "total_ht": round(situation_ht, 2),
        "total_vat": round(situation_vat, 2),
        "total_ttc": round(situation_ttc, 2),
        "payment_status": "impaye",
        "payment_method": situation_data.payment_method,
        "paid_amount": 0,
        "notes": situation_data.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        # Situation specific fields
        "is_situation": True,
        "situation_type": situation_data.situation_type,
        "situation_number": situation_number,
        "situation_percentage": round(current_percentage, 2),  # Cumulative %
        "previous_percentage": round(previous_percentage, 2),
        "chantier_ref": situation_data.chantier_ref or f"Chantier {quote['quote_number']}"
    }
    
    await db.invoices.insert_one(situation_doc)
    
    return SituationResponse(
        id=situation_doc["id"],
        invoice_number=situation_doc["invoice_number"],
        quote_id=quote_id,
        quote_number=quote["quote_number"],
        client_id=situation_doc["client_id"],
        client_name=situation_doc["client_name"],
        issue_date=situation_doc["issue_date"],
        payment_due_date=situation_doc["payment_due_date"],
        situation_type=situation_doc["situation_type"],
        situation_number=situation_doc["situation_number"],
        current_percentage=situation_doc["situation_percentage"],
        previous_percentage=situation_doc["previous_percentage"],
        situation_percentage=round(situation_percentage, 2),
        items=situation_doc["items"],
        total_ht=situation_doc["total_ht"],
        total_vat=situation_doc["total_vat"],
        total_ttc=situation_doc["total_ttc"],
        payment_status=situation_doc["payment_status"],
        payment_method=situation_doc["payment_method"],
        paid_amount=situation_doc["paid_amount"],
        notes=situation_doc["notes"],
        chantier_ref=situation_doc["chantier_ref"],
        created_at=situation_doc["created_at"]
    )

@api_router.get("/quotes/{quote_id}/situations", response_model=List[SituationResponse])
async def list_quote_situations(quote_id: str, user: dict = Depends(get_current_user)):
    """List all situations for a quote"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    situations = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_situation": True},
        {"_id": 0}
    ).sort("situation_number", 1).to_list(100)
    
    result = []
    for i, s in enumerate(situations):
        # Calculate situation_percentage (difference from previous)
        prev_pct = situations[i-1].get("situation_percentage", 0) if i > 0 else 0
        current_pct = s.get("situation_percentage", 0)
        sit_pct = current_pct - prev_pct
        
        result.append(SituationResponse(
            id=s["id"],
            invoice_number=s["invoice_number"],
            quote_id=quote_id,
            quote_number=quote["quote_number"],
            client_id=s["client_id"],
            client_name=s["client_name"],
            issue_date=s["issue_date"],
            payment_due_date=s.get("payment_due_date", s["issue_date"]),
            situation_type=s.get("situation_type", "global"),
            situation_number=s["situation_number"],
            current_percentage=current_pct,
            previous_percentage=s.get("previous_percentage", prev_pct),
            situation_percentage=round(sit_pct, 2),
            items=s.get("items", []),
            total_ht=s["total_ht"],
            total_vat=s["total_vat"],
            total_ttc=s["total_ttc"],
            payment_status=s["payment_status"],
            payment_method=s["payment_method"],
            paid_amount=s.get("paid_amount", 0),
            notes=s.get("notes", ""),
            chantier_ref=s.get("chantier_ref", ""),
            created_at=s["created_at"]
        ))
    
    return result

@api_router.get("/quotes/{quote_id}/situations/summary")
async def get_situations_summary(quote_id: str, user: dict = Depends(get_current_user)):
    """Get summary of situations for a quote (total progress, remaining)"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    situations = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_situation": True},
        {"_id": 0}
    ).sort("situation_number", 1).to_list(100)
    
    total_situations_ht = sum(s["total_ht"] for s in situations)
    total_situations_vat = sum(s["total_vat"] for s in situations)
    total_situations_ttc = sum(s["total_ttc"] for s in situations)
    total_paid = sum(s.get("paid_amount", 0) for s in situations if s["payment_status"] == "paye")
    
    remaining_ht = quote["total_ht"] - total_situations_ht
    remaining_vat = quote["total_vat"] - total_situations_vat
    remaining_ttc = quote["total_ttc"] - total_situations_ttc
    
    # Get current progress percentage
    current_progress = situations[-1].get("situation_percentage", 0) if situations else 0
    
    # Build line-by-line progress for per_line situations
    line_progress = []
    if situations:
        last_situation = situations[-1]
        for item in last_situation.get("items", []):
            line_progress.append({
                "description": item.get("description", ""),
                "cumulative_percent": item.get("cumulative_percent", item.get("situation_percent", 0) + 
                    (situations[-2].get("items", [{}])[0].get("cumulative_percent", 0) if len(situations) > 1 else 0))
            })
    
    return {
        "quote_total_ht": quote["total_ht"],
        "quote_total_vat": quote["total_vat"],
        "quote_total_ttc": quote["total_ttc"],
        "situations_count": len(situations),
        "current_progress_percentage": round(current_progress, 2),
        "total_situations_ht": round(total_situations_ht, 2),
        "total_situations_vat": round(total_situations_vat, 2),
        "total_situations_ttc": round(total_situations_ttc, 2),
        "total_paid": round(total_paid, 2),
        "remaining_ht": round(max(0, remaining_ht), 2),
        "remaining_vat": round(max(0, remaining_vat), 2),
        "remaining_ttc": round(max(0, remaining_ttc), 2),
        "percentage_invoiced": round(current_progress, 2),
        "percentage_paid": round((total_paid / quote["total_ttc"] * 100) if quote["total_ttc"] > 0 else 0, 1),
        "line_progress": line_progress,
        "situations": [
            {
                "id": s["id"],
                "invoice_number": s["invoice_number"],
                "situation_number": s["situation_number"],
                "situation_type": s.get("situation_type", "global"),
                "cumulative_percentage": s.get("situation_percentage", 0),
                "total_ttc": s["total_ttc"],
                "payment_status": s["payment_status"],
                "paid_amount": s.get("paid_amount", 0)
            }
            for s in situations
        ]
    }

@api_router.post("/quotes/{quote_id}/situation/final-invoice", response_model=InvoiceResponse)
async def create_situation_final_invoice(quote_id: str, user: dict = Depends(get_current_user)):
    """Create final invoice from quote after situations, showing all previous situations"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    if quote["status"] != "accepte":
        raise HTTPException(status_code=400, detail="Le devis doit être accepté pour créer la facture finale")
    
    # Get company settings
    settings = await get_company_settings()
    
    # Get all situations
    situations = await db.invoices.find(
        {"parent_quote_id": quote_id, "is_situation": True},
        {"_id": 0}
    ).sort("situation_number", 1).to_list(100)
    
    if not situations:
        raise HTTPException(status_code=400, detail="Aucune situation trouvée. Créez d'abord des situations.")
    
    # Calculate totals from situations
    total_situations_ttc = sum(s["total_ttc"] for s in situations)
    total_paid_situations = sum(s.get("paid_amount", 0) for s in situations if s["payment_status"] == "paye")
    
    invoice_id = str(uuid.uuid4())
    invoice_number = await get_next_invoice_number()
    
    issue_date = datetime.now(timezone.utc)
    payment_due_date = issue_date + timedelta(days=settings.default_payment_delay_days)
    
    # Handle auto-entrepreneur mode
    items = quote["items"]
    if settings.is_auto_entrepreneur:
        items = [{**item, "vat_rate": 0.0} for item in items]
        total_ht = sum(item["quantity"] * item["unit_price"] for item in items)
        total_vat = 0.0
        total_ttc = total_ht
    else:
        total_ht = quote["total_ht"]
        total_vat = quote["total_vat"]
        total_ttc = quote["total_ttc"]
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "parent_quote_id": quote_id,
        "issue_date": issue_date.isoformat(),
        "payment_due_date": payment_due_date.isoformat(),
        "items": items,
        "total_ht": total_ht,
        "total_vat": total_vat,
        "total_ttc": total_ttc,
        "payment_status": "impaye",
        "payment_method": "virement",
        "paid_amount": 0,
        "notes": quote.get("notes", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        # Final invoice specific
        "is_acompte": False,
        "is_final_invoice": True,
        "is_situation_final": True,
        "situations_deducted": total_situations_ttc,
        "situations_recap": [
            {
                "invoice_number": s["invoice_number"],
                "situation_number": s["situation_number"],
                "percentage": s.get("situation_percentage", 0),
                "total_ttc": s["total_ttc"],
                "payment_status": s["payment_status"]
            }
            for s in situations
        ],
        "net_to_pay": round(total_ttc - total_situations_ttc, 2)
    }
    
    await db.invoices.insert_one(invoice_doc)
    
    # Update quote status
    await db.quotes.update_one({"id": quote_id}, {"$set": {"status": "facture"}})
    
    # Add default values for missing fields
    invoice_doc["acompte_type"] = None
    invoice_doc["acompte_value"] = None
    invoice_doc["acompte_number"] = None
    
    return InvoiceResponse(**invoice_doc)

# ============== COMPANY SETTINGS ==============

@api_router.get("/settings", response_model=CompanySettings)
async def get_settings(user: dict = Depends(get_current_user)):
    settings = await db.settings.find_one({"type": "company"}, {"_id": 0})
    if not settings:
        return CompanySettings()
    return CompanySettings(**{k: v for k, v in settings.items() if k != "type"})

@api_router.put("/settings", response_model=CompanySettings)
async def update_settings(settings_data: CompanySettings, user: dict = Depends(get_current_user)):
    settings_doc = settings_data.model_dump()
    settings_doc["type"] = "company"
    
    await db.settings.update_one(
        {"type": "company"},
        {"$set": settings_doc},
        upsert=True
    )
    return settings_data

@api_router.post("/settings/logo")
async def upload_logo(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image")
    
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="L'image ne doit pas dépasser 5MB")
    
    logo_base64 = base64.b64encode(contents).decode('utf-8')
    logo_data = f"data:{file.content_type};base64,{logo_base64}"
    
    await db.settings.update_one(
        {"type": "company"},
        {"$set": {"logo_base64": logo_data}},
        upsert=True
    )
    
    return {"message": "Logo téléchargé avec succès", "logo": logo_data}

# ============== DASHBOARD ==============

@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(user: dict = Depends(get_current_user)):
    # Total turnover (paid invoices)
    paid_invoices = await db.invoices.find({"payment_status": "paye"}, {"_id": 0}).to_list(10000)
    total_turnover = sum(inv["total_ttc"] for inv in paid_invoices)
    
    # Unpaid invoices
    unpaid_invoices = await db.invoices.find({"payment_status": {"$in": ["impaye", "partiel"]}}, {"_id": 0}).to_list(10000)
    unpaid_count = len(unpaid_invoices)
    unpaid_amount = sum(inv["total_ttc"] - inv.get("paid_amount", 0) for inv in unpaid_invoices)
    
    # Pending quotes (sent but not accepted/refused)
    pending_quotes = await db.quotes.count_documents({"status": "envoye"})
    
    # Totals
    total_clients = await db.clients.count_documents({})
    total_quotes = await db.quotes.count_documents({})
    total_invoices = await db.invoices.count_documents({})
    
    return DashboardStats(
        total_turnover=round(total_turnover, 2),
        unpaid_invoices_count=unpaid_count,
        unpaid_invoices_amount=round(unpaid_amount, 2),
        pending_quotes_count=pending_quotes,
        total_clients=total_clients,
        total_quotes=total_quotes,
        total_invoices=total_invoices
    )

# ============== PREDEFINED ITEMS ROUTES ==============

async def initialize_default_items():
    """Initialize default BTP items if none exist"""
    count = await db.predefined_items.count_documents({})
    if count == 0:
        for category, items in DEFAULT_BTP_CATEGORIES.items():
            for item in items:
                item_doc = {
                    "id": str(uuid.uuid4()),
                    "category": category,
                    "description": item["description"],
                    "unit": item["unit"],
                    "default_price": item["default_price"],
                    "default_vat_rate": 20.0
                }
                await db.predefined_items.insert_one(item_doc)

@api_router.get("/predefined-items/categories")
async def get_categories(user: dict = Depends(get_current_user)):
    """Get all categories with their items"""
    await initialize_default_items()
    items = await db.predefined_items.find({}, {"_id": 0}).to_list(1000)
    
    # Group by category
    categories = {}
    for item in items:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(PredefinedItemResponse(**item))
    
    # Return as list of categories
    result = [{"name": name, "items": items} for name, items in sorted(categories.items())]
    return result

@api_router.get("/predefined-items", response_model=List[PredefinedItemResponse])
async def list_predefined_items(category: Optional[str] = None, user: dict = Depends(get_current_user)):
    """List all predefined items, optionally filtered by category"""
    await initialize_default_items()
    query = {}
    if category:
        query["category"] = category
    items = await db.predefined_items.find(query, {"_id": 0}).to_list(1000)
    return [PredefinedItemResponse(**item) for item in items]

@api_router.post("/predefined-items", response_model=PredefinedItemResponse)
async def create_predefined_item(item_data: PredefinedItemCreate, user: dict = Depends(get_current_user)):
    """Create a new predefined item"""
    item_id = str(uuid.uuid4())
    item_doc = {
        "id": item_id,
        "category": item_data.category,
        "description": item_data.description,
        "unit": item_data.unit,
        "default_price": item_data.default_price,
        "default_vat_rate": item_data.default_vat_rate
    }
    await db.predefined_items.insert_one(item_doc)
    return PredefinedItemResponse(**item_doc)

@api_router.put("/predefined-items/{item_id}", response_model=PredefinedItemResponse)
async def update_predefined_item(item_id: str, item_data: PredefinedItemUpdate, user: dict = Depends(get_current_user)):
    """Update a predefined item"""
    item = await db.predefined_items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    update_data = {k: v for k, v in item_data.model_dump().items() if v is not None}
    if update_data:
        await db.predefined_items.update_one({"id": item_id}, {"$set": update_data})
    
    updated_item = await db.predefined_items.find_one({"id": item_id}, {"_id": 0})
    return PredefinedItemResponse(**updated_item)

@api_router.delete("/predefined-items/{item_id}")
async def delete_predefined_item(item_id: str, user: dict = Depends(get_current_user)):
    """Delete a predefined item"""
    result = await db.predefined_items.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return {"message": "Article supprimé"}

@api_router.post("/predefined-items/reset")
async def reset_predefined_items(user: dict = Depends(get_current_user)):
    """Reset predefined items to defaults"""
    await db.predefined_items.delete_many({})
    await initialize_default_items()
    return {"message": "Articles réinitialisés"}

# ============== RENOVATION KITS ROUTES ==============

async def initialize_default_kits():
    """Initialize default renovation kits if none exist"""
    count = await db.renovation_kits.count_documents({"is_default": True})
    if count == 0:
        for kit in DEFAULT_RENOVATION_KITS:
            kit_doc = {
                "id": str(uuid.uuid4()),
                "name": kit["name"],
                "description": kit["description"],
                "items": kit["items"],
                "is_default": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.renovation_kits.insert_one(kit_doc)

@api_router.get("/kits", response_model=List[KitResponse])
async def list_kits(user: dict = Depends(get_current_user)):
    """List all renovation kits"""
    await initialize_default_kits()
    kits = await db.renovation_kits.find({}, {"_id": 0}).sort("name", 1).to_list(1000)
    return [KitResponse(**kit) for kit in kits]

@api_router.get("/kits/{kit_id}", response_model=KitResponse)
async def get_kit(kit_id: str, user: dict = Depends(get_current_user)):
    """Get a specific kit"""
    kit = await db.renovation_kits.find_one({"id": kit_id}, {"_id": 0})
    if not kit:
        raise HTTPException(status_code=404, detail="Kit non trouvé")
    return KitResponse(**kit)

@api_router.post("/kits", response_model=KitResponse)
async def create_kit(kit_data: KitCreate, user: dict = Depends(get_current_user)):
    """Create a new renovation kit"""
    kit_id = str(uuid.uuid4())
    kit_doc = {
        "id": kit_id,
        "name": kit_data.name,
        "description": kit_data.description,
        "items": [item.model_dump() for item in kit_data.items],
        "is_default": False,  # User-created kits are not default
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.renovation_kits.insert_one(kit_doc)
    return KitResponse(**kit_doc)

@api_router.put("/kits/{kit_id}", response_model=KitResponse)
async def update_kit(kit_id: str, kit_data: KitUpdate, user: dict = Depends(get_current_user)):
    """Update a renovation kit"""
    kit = await db.renovation_kits.find_one({"id": kit_id}, {"_id": 0})
    if not kit:
        raise HTTPException(status_code=404, detail="Kit non trouvé")
    
    update_data = {}
    if kit_data.name is not None:
        update_data["name"] = kit_data.name
    if kit_data.description is not None:
        update_data["description"] = kit_data.description
    if kit_data.items is not None:
        update_data["items"] = [item.model_dump() for item in kit_data.items]
    
    if update_data:
        await db.renovation_kits.update_one({"id": kit_id}, {"$set": update_data})
    
    updated_kit = await db.renovation_kits.find_one({"id": kit_id}, {"_id": 0})
    return KitResponse(**updated_kit)

@api_router.delete("/kits/{kit_id}")
async def delete_kit(kit_id: str, user: dict = Depends(get_current_user)):
    """Delete a renovation kit"""
    result = await db.renovation_kits.delete_one({"id": kit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kit non trouvé")
    return {"message": "Kit supprimé"}

@api_router.post("/kits/from-quote/{quote_id}", response_model=KitResponse)
async def create_kit_from_quote(quote_id: str, kit_name: str, kit_description: str = "", user: dict = Depends(get_current_user)):
    """Create a kit from an existing quote"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    # Convert quote items to kit items
    kit_items = []
    for item in quote["items"]:
        kit_items.append({
            "description": item["description"],
            "unit": item.get("unit", "unité"),
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "vat_rate": item["vat_rate"]
        })
    
    kit_id = str(uuid.uuid4())
    kit_doc = {
        "id": kit_id,
        "name": kit_name,
        "description": kit_description,
        "items": kit_items,
        "is_default": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.renovation_kits.insert_one(kit_doc)
    return KitResponse(**kit_doc)

@api_router.post("/kits/reset")
async def reset_kits(user: dict = Depends(get_current_user)):
    """Reset kits to defaults (removes user kits)"""
    await db.renovation_kits.delete_many({})
    await initialize_default_kits()
    return {"message": "Kits réinitialisés"}

# ============== PDF GENERATION ==============

async def get_company_settings():
    settings = await db.settings.find_one({"type": "company"}, {"_id": 0})
    if not settings:
        return CompanySettings()
    return CompanySettings(**{k: v for k, v in settings.items() if k != "type"})

def create_pdf(doc_type: str, doc_data: dict, company: CompanySettings, client: dict):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#EA580C'), spaceAfter=8)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#475569'), leading=12)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=9, leading=12)
    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', leading=12)
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#64748B'), leading=10)
    legal_style = ParagraphStyle('Legal', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#374151'), leading=10)
    
    elements = []
    
    # ========== HEADER: Company Info ==========
    company_name = company.company_name or "Votre Entreprise BTP"
    elements.append(Paragraph(company_name, title_style))
    
    # Company details (all required French legal info)
    company_lines = []
    if company.address:
        company_lines.append(company.address)
    
    contact_parts = []
    if company.phone:
        contact_parts.append(f"Tél: {company.phone}")
    if company.email:
        contact_parts.append(f"Email: {company.email}")
    if contact_parts:
        company_lines.append(" | ".join(contact_parts))
    
    legal_parts = []
    if company.siret:
        legal_parts.append(f"SIRET: {company.siret}")
    if company.rcs_rm:
        legal_parts.append(company.rcs_rm)
    if company.code_ape:
        legal_parts.append(f"Code APE: {company.code_ape}")
    if legal_parts:
        company_lines.append(" | ".join(legal_parts))
    
    if company.capital_social:
        company_lines.append(f"Capital social: {company.capital_social}")
    
    # VAT number or auto-entrepreneur mention
    if company.is_auto_entrepreneur:
        company_lines.append(company.auto_entrepreneur_mention)
    elif company.vat_number:
        company_lines.append(f"N° TVA Intracommunautaire: {company.vat_number}")
    
    for line in company_lines:
        elements.append(Paragraph(line, header_style))
    
    elements.append(Spacer(1, 12*mm))
    
    # ========== DOCUMENT TITLE ==========
    if doc_type == "quote":
        doc_title = f"DEVIS N° {doc_data['quote_number']}"
    else:
        # Check if it's an acompte, situation or final invoice
        is_acompte = doc_data.get('is_acompte', False)
        is_situation = doc_data.get('is_situation', False)
        is_final = doc_data.get('is_final_invoice', False)
        is_situation_final = doc_data.get('is_situation_final', False)
        
        if is_situation:
            situation_num = doc_data.get('situation_number', 1)
            current_pct = doc_data.get('situation_percentage', 0)
            chantier_ref = doc_data.get('chantier_ref', '')
            doc_title = f"SITUATION DE TRAVAUX N° {doc_data['invoice_number']}"
            elements.append(Paragraph(doc_title, ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'))))
            elements.append(Paragraph(f"Situation n°{situation_num} - Avancement {current_pct}%", ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#059669'))))
            if chantier_ref:
                elements.append(Paragraph(f"Réf. chantier: {chantier_ref}", ParagraphStyle('RefStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6B7280'))))
        elif is_acompte:
            acompte_num = doc_data.get('acompte_number', 1)
            doc_title = f"FACTURE D'ACOMPTE N° {doc_data['invoice_number']}"
            elements.append(Paragraph(doc_title, ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'))))
            elements.append(Paragraph(f"Acompte n°{acompte_num}", ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#6366F1'))))
        elif is_situation_final:
            doc_title = f"DÉCOMPTE FINAL N° {doc_data['invoice_number']}"
            elements.append(Paragraph(doc_title, ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'))))
            elements.append(Paragraph("Facture de solde après situations", ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#059669'))))
        elif is_final:
            doc_title = f"FACTURE DE SOLDE N° {doc_data['invoice_number']}"
            elements.append(Paragraph(doc_title, ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'))))
        else:
            doc_title = f"FACTURE N° {doc_data['invoice_number']}"
            elements.append(Paragraph(doc_title, ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'))))
    
    if doc_type == "quote":
        elements.append(Paragraph(doc_title, ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'))))
    
    elements.append(Spacer(1, 4*mm))
    
    # ========== DATE & CLIENT INFO ==========
    issue_date = doc_data['issue_date'][:10] if isinstance(doc_data['issue_date'], str) else doc_data['issue_date'].strftime('%Y-%m-%d')
    
    left_col = []
    left_col.append(Paragraph(f"<b>Date d'émission:</b> {issue_date}", normal_style))
    
    if doc_type == "quote":
        validity_date = doc_data['validity_date'][:10] if isinstance(doc_data['validity_date'], str) else doc_data['validity_date'].strftime('%Y-%m-%d')
        left_col.append(Paragraph(f"<b>Date de validité:</b> {validity_date}", normal_style))
    else:
        # Invoice: payment due date
        payment_due = doc_data.get('payment_due_date', '')
        if payment_due:
            due_date = payment_due[:10] if isinstance(payment_due, str) else payment_due.strftime('%Y-%m-%d')
            left_col.append(Paragraph(f"<b>Date d'échéance:</b> {due_date}", normal_style))
    
    right_col = []
    right_col.append(Paragraph("<b>Client:</b>", normal_style))
    right_col.append(Paragraph(client.get('name', ''), bold_style))
    if client.get('address'):
        right_col.append(Paragraph(client.get('address', ''), normal_style))
    if client.get('email'):
        right_col.append(Paragraph(client.get('email', ''), normal_style))
    if client.get('phone'):
        right_col.append(Paragraph(f"Tél: {client.get('phone', '')}", normal_style))
    
    # Create two-column layout
    info_data = [[left_col[0] if left_col else '', right_col[0] if right_col else '']]
    max_rows = max(len(left_col), len(right_col))
    for i in range(1, max_rows):
        left_item = left_col[i] if i < len(left_col) else ''
        right_item = right_col[i] if i < len(right_col) else ''
        info_data.append([left_item, right_item])
    
    info_table = Table(info_data, colWidths=[90*mm, 80*mm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))
    
    # ========== ITEMS TABLE ==========
    is_auto_entrepreneur = company.is_auto_entrepreneur
    is_situation = doc_data.get('is_situation', False)
    is_situation_final = doc_data.get('is_situation_final', False)
    
    if is_situation:
        # Special table format for situation invoices
        if is_auto_entrepreneur:
            table_data = [
                [Paragraph("<b>Description</b>", bold_style), 
                 Paragraph("<b>Base HT</b>", bold_style), 
                 Paragraph("<b>%</b>", bold_style), 
                 Paragraph("<b>Montant</b>", bold_style)]
            ]
            
            for item in doc_data['items']:
                base_ht = item.get('original_total_ht', item['quantity'] * item['unit_price'])
                sit_pct = item.get('situation_percent', item.get('cumulative_percent', 0))
                sit_amount = item.get('situation_amount_ht', base_ht * sit_pct / 100)
                table_data.append([
                    Paragraph(item['description'], normal_style),
                    Paragraph(f"{base_ht:.2f} €", normal_style),
                    Paragraph(f"{sit_pct:.1f}%", normal_style),
                    Paragraph(f"{sit_amount:.2f} €", normal_style)
                ])
            
            items_table = Table(table_data, colWidths=[80*mm, 35*mm, 20*mm, 35*mm])
        else:
            table_data = [
                [Paragraph("<b>Description</b>", bold_style), 
                 Paragraph("<b>Base HT</b>", bold_style),
                 Paragraph("<b>TVA</b>", bold_style), 
                 Paragraph("<b>% Sit.</b>", bold_style), 
                 Paragraph("<b>Montant HT</b>", bold_style)]
            ]
            
            for item in doc_data['items']:
                base_ht = item.get('original_total_ht', item['quantity'] * item['unit_price'])
                sit_pct = item.get('situation_percent', item.get('cumulative_percent', 0))
                sit_amount = item.get('situation_amount_ht', base_ht * sit_pct / 100)
                table_data.append([
                    Paragraph(item['description'], normal_style),
                    Paragraph(f"{base_ht:.2f} €", normal_style),
                    Paragraph(f"{item['vat_rate']}%", normal_style),
                    Paragraph(f"{sit_pct:.1f}%", normal_style),
                    Paragraph(f"{sit_amount:.2f} €", normal_style)
                ])
            
            items_table = Table(table_data, colWidths=[65*mm, 30*mm, 18*mm, 22*mm, 30*mm])
    
    elif is_auto_entrepreneur:
        # No VAT columns for auto-entrepreneur
        table_data = [
            [Paragraph("<b>Description</b>", bold_style), 
             Paragraph("<b>Qté</b>", bold_style), 
             Paragraph("<b>Prix unitaire</b>", bold_style), 
             Paragraph("<b>Total</b>", bold_style)]
        ]
        
        for item in doc_data['items']:
            line_total = item['quantity'] * item['unit_price']
            table_data.append([
                Paragraph(item['description'], normal_style),
                Paragraph(str(item['quantity']), normal_style),
                Paragraph(f"{item['unit_price']:.2f} €", normal_style),
                Paragraph(f"{line_total:.2f} €", normal_style)
            ])
        
        items_table = Table(table_data, colWidths=[85*mm, 20*mm, 35*mm, 35*mm])
    else:
        # Full table with VAT
        table_data = [
            [Paragraph("<b>Description</b>", bold_style), 
             Paragraph("<b>Qté</b>", bold_style), 
             Paragraph("<b>Prix unit. HT</b>", bold_style), 
             Paragraph("<b>TVA</b>", bold_style), 
             Paragraph("<b>Total HT</b>", bold_style)]
        ]
        
        for item in doc_data['items']:
            line_total = item['quantity'] * item['unit_price']
            table_data.append([
                Paragraph(item['description'], normal_style),
                Paragraph(str(item['quantity']), normal_style),
                Paragraph(f"{item['unit_price']:.2f} €", normal_style),
                Paragraph(f"{item['vat_rate']}%", normal_style),
                Paragraph(f"{line_total:.2f} €", normal_style)
            ])
        
        items_table = Table(table_data, colWidths=[70*mm, 18*mm, 30*mm, 20*mm, 30*mm])
    
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 6*mm))
    
    # ========== TOTALS ==========
    if is_auto_entrepreneur:
        totals_data = [
            ["Total:", f"{doc_data['total_ht']:.2f} €"],
        ]
    else:
        # Group VAT by rate
        vat_by_rate = {}
        for item in doc_data['items']:
            rate = item['vat_rate']
            line_ht = item['quantity'] * item['unit_price']
            line_vat = line_ht * rate / 100
            if rate not in vat_by_rate:
                vat_by_rate[rate] = 0
            vat_by_rate[rate] += line_vat
        
        totals_data = [
            ["Total HT:", f"{doc_data['total_ht']:.2f} €"],
        ]
        
        # Show VAT breakdown by rate
        for rate in sorted(vat_by_rate.keys()):
            if vat_by_rate[rate] > 0:
                totals_data.append([f"TVA {rate}%:", f"{vat_by_rate[rate]:.2f} €"])
        
        totals_data.append(["Total TTC:", f"{doc_data['total_ttc']:.2f} €"])
    
    # Invoice-specific: payment info
    if doc_type == "invoice":
        # For final invoice with acomptes deducted
        is_final = doc_data.get('is_final_invoice', False)
        acomptes_deducted = doc_data.get('acomptes_deducted', 0)
        
        if is_final and acomptes_deducted > 0:
            totals_data.append(["Acomptes versés:", f"-{acomptes_deducted:.2f} €"])
            net_to_pay = doc_data.get('net_to_pay', doc_data['total_ttc'] - acomptes_deducted)
            totals_data.append(["NET À PAYER:", f"{net_to_pay:.2f} €"])
        
        payment_status_map = {"impaye": "Impayé", "paye": "Payé", "partiel": "Partiellement payé"}
        totals_data.append(["Statut:", payment_status_map.get(doc_data['payment_status'], doc_data['payment_status'])])
        
        if not is_final:
            if doc_data.get('paid_amount', 0) > 0:
                totals_data.append(["Montant payé:", f"{doc_data['paid_amount']:.2f} €"])
                remaining = doc_data['total_ttc'] - doc_data['paid_amount']
                totals_data.append(["Reste à payer:", f"{remaining:.2f} €"])
    
    totals_table = Table(totals_data, colWidths=[120*mm, 50*mm])
    
    # Highlight the final row
    final_row_idx = len(totals_data) - 1
    if doc_type == "invoice":
        # For invoice, highlight the TTC row (usually 3rd row if no payment)
        ttc_row_idx = 2 if not is_auto_entrepreneur else 0
    else:
        ttc_row_idx = final_row_idx
    
    table_style = [
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    
    # Find the TTC row for highlighting
    for i, row in enumerate(totals_data):
        if "TTC" in row[0] or (is_auto_entrepreneur and row[0] == "Total:"):
            table_style.extend([
                ('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'),
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#EA580C')),
                ('TEXTCOLOR', (0, i), (-1, i), colors.white),
            ])
            break
    
    totals_table.setStyle(TableStyle(table_style))
    elements.append(totals_table)
    
    # ========== BANK DETAILS (for invoices) ==========
    if doc_type == "invoice" and (company.iban or company.bic):
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("<b>Coordonnées bancaires:</b>", bold_style))
        if company.iban:
            elements.append(Paragraph(f"IBAN: {company.iban}", normal_style))
        if company.bic:
            elements.append(Paragraph(f"BIC: {company.bic}", normal_style))
    
    # ========== NOTES ==========
    if doc_data.get('notes'):
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("<b>Notes:</b>", bold_style))
        elements.append(Paragraph(doc_data['notes'], normal_style))
    
    # ========== LEGAL MENTIONS ==========
    elements.append(Spacer(1, 10*mm))
    
    if doc_type == "quote":
        # Quote legal mentions
        legal_lines = [
            f"Ce devis est valable jusqu'au {validity_date}.",
            "En signant ce devis, le client reconnaît avoir pris connaissance des conditions générales de vente.",
            "",
            "Signature du client précédée de la mention \"Bon pour accord\" et de la date:",
            "",
            "_" * 50,
        ]
        for line in legal_lines:
            elements.append(Paragraph(line, legal_style))
    else:
        # Invoice legal mentions (French legal requirements)
        payment_method_map = {
            "virement": "virement bancaire",
            "especes": "espèces", 
            "cheque": "chèque",
            "carte": "carte bancaire"
        }
        method = payment_method_map.get(doc_data.get('payment_method', 'virement'), 'virement bancaire')
        
        payment_due = doc_data.get('payment_due_date', '')
        if payment_due:
            due_date_str = payment_due[:10] if isinstance(payment_due, str) else payment_due.strftime('%Y-%m-%d')
        else:
            due_date_str = "30 jours"
        
        legal_lines = [
            f"<b>Mode de règlement:</b> {method}",
            f"<b>Date limite de paiement:</b> {due_date_str}",
            "",
            "<b>Conditions de paiement:</b>",
            f"En cas de retard de paiement, seront exigibles, conformément à l'article L 441-6 du code de commerce:",
            f"- Une indemnité calculée sur la base de trois fois le taux d'intérêt légal en vigueur",
            f"- Une indemnité forfaitaire pour frais de recouvrement de 40 euros",
        ]
        
        for line in legal_lines:
            elements.append(Paragraph(line, legal_style))
    
    # ========== FOOTER ==========
    elements.append(Spacer(1, 8*mm))
    footer_parts = []
    if company.company_name:
        footer_parts.append(company.company_name)
    if company.siret:
        footer_parts.append(f"SIRET: {company.siret}")
    if company.rcs_rm:
        footer_parts.append(company.rcs_rm)
    
    if footer_parts:
        elements.append(Paragraph(" - ".join(footer_parts), small_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
    buffer.seek(0)
    return buffer

@api_router.get("/quotes/{quote_id}/pdf")
async def generate_quote_pdf(quote_id: str, user: dict = Depends(get_current_user)):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    client = await db.clients.find_one({"id": quote["client_id"]}, {"_id": 0})
    if not client:
        client = {"name": quote["client_name"], "address": "", "email": ""}
    
    company = await get_company_settings()
    pdf_buffer = create_pdf("quote", quote, company, client)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=devis_{quote['quote_number']}.pdf"}
    )

@api_router.get("/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str, user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    client = await db.clients.find_one({"id": invoice["client_id"]}, {"_id": 0})
    if not client:
        client = {"name": invoice["client_name"], "address": "", "email": ""}
    
    company = await get_company_settings()
    pdf_buffer = create_pdf("invoice", invoice, company, client)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=facture_{invoice['invoice_number']}.pdf"}
    )

# ============== CLIENT SHARE LINKS (PUBLIC) ==============

import secrets

def generate_share_token():
    """Generate a secure random token for document sharing"""
    return secrets.token_urlsafe(32)

@api_router.post("/quotes/{quote_id}/share")
async def create_quote_share_link(quote_id: str, user: dict = Depends(get_current_user)):
    """Create or refresh share token for a quote"""
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    share_token = generate_share_token()
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"share_token": share_token}}
    )
    
    return {"share_token": share_token, "share_url": f"/client/devis/{share_token}"}

@api_router.delete("/quotes/{quote_id}/share")
async def revoke_quote_share_link(quote_id: str, user: dict = Depends(get_current_user)):
    """Revoke share link for a quote"""
    result = await db.quotes.update_one(
        {"id": quote_id},
        {"$unset": {"share_token": ""}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    return {"message": "Lien de partage révoqué"}

@api_router.post("/invoices/{invoice_id}/share")
async def create_invoice_share_link(invoice_id: str, user: dict = Depends(get_current_user)):
    """Create or refresh share token for an invoice"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    share_token = generate_share_token()
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"share_token": share_token}}
    )
    
    return {"share_token": share_token, "share_url": f"/client/facture/{share_token}"}

@api_router.delete("/invoices/{invoice_id}/share")
async def revoke_invoice_share_link(invoice_id: str, user: dict = Depends(get_current_user)):
    """Revoke share link for an invoice"""
    result = await db.invoices.update_one(
        {"id": invoice_id},
        {"$unset": {"share_token": ""}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return {"message": "Lien de partage révoqué"}

# Public endpoints (no auth required)
@api_router.get("/public/quote/{share_token}")
async def get_public_quote(share_token: str):
    """Get quote details via share link - NO AUTH REQUIRED"""
    quote = await db.quotes.find_one({"share_token": share_token}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Document non trouvé ou lien expiré")
    
    client = await db.clients.find_one({"id": quote["client_id"]}, {"_id": 0})
    company = await get_company_settings()
    
    # Return limited data for client view
    status_labels = {
        "brouillon": "Devis",
        "envoye": "Devis envoyé",
        "accepte": "Devis accepté",
        "refuse": "Devis refusé",
        "facture": "Facturé"
    }
    
    return {
        "type": "devis",
        "document_number": quote["quote_number"],
        "client_name": quote["client_name"],
        "issue_date": quote["issue_date"],
        "validity_date": quote["validity_date"],
        "items": quote["items"],
        "total_ht": quote["total_ht"],
        "total_vat": quote["total_vat"],
        "total_ttc": quote["total_ttc"],
        "status": quote["status"],
        "status_label": status_labels.get(quote["status"], quote["status"]),
        "notes": quote.get("notes", ""),
        "company": {
            "name": company.company_name,
            "address": company.address,
            "phone": company.phone,
            "email": company.email,
            "siret": company.siret,
            "vat_number": company.vat_number
        }
    }

@api_router.get("/public/quote/{share_token}/pdf")
async def get_public_quote_pdf(share_token: str):
    """Download quote PDF via share link - NO AUTH REQUIRED"""
    quote = await db.quotes.find_one({"share_token": share_token}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Document non trouvé ou lien expiré")
    
    client = await db.clients.find_one({"id": quote["client_id"]}, {"_id": 0})
    if not client:
        client = {"name": quote["client_name"], "address": "", "email": ""}
    
    company = await get_company_settings()
    pdf_buffer = create_pdf("quote", quote, company, client)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=devis_{quote['quote_number']}.pdf"}
    )

@api_router.get("/public/invoice/{share_token}")
async def get_public_invoice(share_token: str):
    """Get invoice details via share link - NO AUTH REQUIRED"""
    invoice = await db.invoices.find_one({"share_token": share_token}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Document non trouvé ou lien expiré")
    
    client = await db.clients.find_one({"id": invoice["client_id"]}, {"_id": 0})
    company = await get_company_settings()
    
    payment_status_labels = {
        "impaye": "En attente de paiement",
        "partiel": "Partiellement payé",
        "paye": "Payé"
    }
    
    return {
        "type": "facture",
        "document_number": invoice["invoice_number"],
        "client_name": invoice["client_name"],
        "issue_date": invoice["issue_date"],
        "items": invoice["items"],
        "total_ht": invoice["total_ht"],
        "total_vat": invoice["total_vat"],
        "total_ttc": invoice["total_ttc"],
        "payment_status": invoice["payment_status"],
        "payment_status_label": payment_status_labels.get(invoice["payment_status"], invoice["payment_status"]),
        "payment_method": invoice.get("payment_method", "virement"),
        "paid_amount": invoice.get("paid_amount", 0),
        "notes": invoice.get("notes", ""),
        "company": {
            "name": company.company_name,
            "address": company.address,
            "phone": company.phone,
            "email": company.email,
            "siret": company.siret,
            "vat_number": company.vat_number
        }
    }

@api_router.get("/public/invoice/{share_token}/pdf")
async def get_public_invoice_pdf(share_token: str):
    """Download invoice PDF via share link - NO AUTH REQUIRED"""
    invoice = await db.invoices.find_one({"share_token": share_token}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Document non trouvé ou lien expiré")
    
    client = await db.clients.find_one({"id": invoice["client_id"]}, {"_id": 0})
    if not client:
        client = {"name": invoice["client_name"], "address": "", "email": ""}
    
    company = await get_company_settings()
    pdf_buffer = create_pdf("invoice", invoice, company, client)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=facture_{invoice['invoice_number']}.pdf"}
    )

# ============== EMAIL SENDING ==============

class SendDocumentEmailRequest(BaseModel):
    recipient_email: EmailStr
    recipient_name: str = ""
    custom_message: str = ""

def generate_email_html(doc_type: str, doc_data: dict, company, client, share_url: str, custom_message: str = ""):
    """Generate professional French email HTML"""
    
    doc_label = "Devis" if doc_type == "quote" else "Facture"
    doc_number = doc_data.get("quote_number") if doc_type == "quote" else doc_data.get("invoice_number")
    
    email_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f97316; padding: 20px; text-align: center;">
            <h1 style="color: white; margin: 0;">{company.company_name}</h1>
        </div>
        
        <div style="padding: 30px; background-color: #ffffff;">
            <p>Bonjour{' ' + client.get('name', '') if client.get('name') else ''},</p>
            
            <p>Veuillez trouver ci-joint votre <strong>{doc_label.lower()} n° {doc_number}</strong>.</p>
            
            {f'<p>{custom_message}</p>' if custom_message else ''}
            
            <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
                <tr style="background-color: #f8fafc;">
                    <td style="padding: 15px; border: 1px solid #e2e8f0;"><strong>N° {doc_label}</strong></td>
                    <td style="padding: 15px; border: 1px solid #e2e8f0;">{doc_number}</td>
                </tr>
                <tr>
                    <td style="padding: 15px; border: 1px solid #e2e8f0;"><strong>Date</strong></td>
                    <td style="padding: 15px; border: 1px solid #e2e8f0;">{doc_data.get('issue_date', '')[:10]}</td>
                </tr>
                <tr style="background-color: #f8fafc;">
                    <td style="padding: 15px; border: 1px solid #e2e8f0;"><strong>Montant TTC</strong></td>
                    <td style="padding: 15px; border: 1px solid #e2e8f0; font-size: 18px; color: #f97316;"><strong>{doc_data.get('total_ttc', 0):.2f} €</strong></td>
                </tr>
            </table>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{share_url}" style="background-color: #f97316; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Consulter le {doc_label.lower()}
                </a>
            </div>
            
            <p>Vous pouvez également télécharger le PDF depuis ce lien.</p>
            
            <p>Cordialement,<br><strong>{company.company_name}</strong></p>
        </div>
        
        <div style="background-color: #1e293b; color: #94a3b8; padding: 20px; font-size: 12px; text-align: center;">
            <p style="margin: 5px 0;"><strong>{company.company_name}</strong></p>
            <p style="margin: 5px 0;">{company.address}</p>
            <p style="margin: 5px 0;">Tél: {company.phone} | Email: {company.email}</p>
            {f'<p style="margin: 5px 0;">SIRET: {company.siret}</p>' if company.siret else ''}
            {f'<p style="margin: 5px 0;">N° TVA: {company.vat_number}</p>' if company.vat_number else ''}
        </div>
    </body>
    </html>
    """
    return email_html

@api_router.post("/quotes/{quote_id}/send-email")
async def send_quote_email(quote_id: str, request: SendDocumentEmailRequest, user: dict = Depends(get_current_user)):
    """Send quote by email to client"""
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Service email non configuré. Ajoutez RESEND_API_KEY dans les paramètres.")
    
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    client = await db.clients.find_one({"id": quote["client_id"]}, {"_id": 0})
    company = await get_company_settings()
    
    # Generate or get share token
    share_token = quote.get("share_token")
    if not share_token:
        share_token = generate_share_token()
        await db.quotes.update_one({"id": quote_id}, {"$set": {"share_token": share_token}})
    
    # Get base URL from environment
    base_url = os.environ.get("FRONTEND_URL", "https://quoteinvoice-btp.preview.emergentagent.com")
    share_url = f"{base_url}/client/devis/{share_token}"
    
    # Generate email HTML
    email_html = generate_email_html("quote", quote, company, client or {}, share_url, request.custom_message)
    
    # Generate PDF attachment
    pdf_buffer = create_pdf("quote", quote, company, client or {"name": quote["client_name"], "address": ""})
    pdf_data = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [request.recipient_email],
            "subject": f"Devis n° {quote['quote_number']} - {company.company_name}",
            "html": email_html,
            "attachments": [
                {
                    "filename": f"devis_{quote['quote_number']}.pdf",
                    "content": pdf_data,
                }
            ]
        }
        
        # Send email asynchronously
        email_result = await asyncio.to_thread(resend.Emails.send, params)
        
        # Update quote status to sent
        await db.quotes.update_one({"id": quote_id}, {"$set": {"status": "envoye"}})
        
        return {
            "status": "success",
            "message": f"Devis envoyé à {request.recipient_email}",
            "email_id": email_result.get("id")
        }
    except Exception as e:
        logging.error(f"Email send error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi: {str(e)}")

@api_router.post("/invoices/{invoice_id}/send-email")
async def send_invoice_email(invoice_id: str, request: SendDocumentEmailRequest, user: dict = Depends(get_current_user)):
    """Send invoice by email to client"""
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Service email non configuré. Ajoutez RESEND_API_KEY dans les paramètres.")
    
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    client = await db.clients.find_one({"id": invoice["client_id"]}, {"_id": 0})
    company = await get_company_settings()
    
    # Generate or get share token
    share_token = invoice.get("share_token")
    if not share_token:
        share_token = generate_share_token()
        await db.invoices.update_one({"id": invoice_id}, {"$set": {"share_token": share_token}})
    
    # Get base URL from environment
    base_url = os.environ.get("FRONTEND_URL", "https://quoteinvoice-btp.preview.emergentagent.com")
    share_url = f"{base_url}/client/facture/{share_token}"
    
    # Generate email HTML
    email_html = generate_email_html("invoice", invoice, company, client or {}, share_url, request.custom_message)
    
    # Generate PDF attachment
    pdf_buffer = create_pdf("invoice", invoice, company, client or {"name": invoice["client_name"], "address": ""})
    pdf_data = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [request.recipient_email],
            "subject": f"Facture n° {invoice['invoice_number']} - {company.company_name}",
            "html": email_html,
            "attachments": [
                {
                    "filename": f"facture_{invoice['invoice_number']}.pdf",
                    "content": pdf_data,
                }
            ]
        }
        
        # Send email asynchronously
        email_result = await asyncio.to_thread(resend.Emails.send, params)
        
        return {
            "status": "success",
            "message": f"Facture envoyée à {request.recipient_email}",
            "email_id": email_result.get("id")
        }
    except Exception as e:
        logging.error(f"Email send error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi: {str(e)}")

@api_router.get("/email/status")
async def get_email_status(user: dict = Depends(get_current_user)):
    """Check if email service is configured"""
    return {
        "configured": bool(RESEND_API_KEY),
        "sender": SENDER_EMAIL if RESEND_API_KEY else None
    }

# ============== MAIN APP ==============

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
