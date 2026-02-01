from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from io import BytesIO
import base64

# ReportLab imports for PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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

class InvoiceCreate(BaseModel):
    client_id: str
    quote_id: Optional[str] = None
    items: List[LineItem]
    notes: str = ""
    payment_method: str = "virement"

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
    items: List[dict]
    total_ht: float
    total_vat: float
    total_ttc: float
    payment_status: str
    payment_method: str
    paid_amount: float
    notes: str
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

class DashboardStats(BaseModel):
    total_turnover: float
    unpaid_invoices_count: int
    unpaid_invoices_amount: float
    pending_quotes_count: int
    total_clients: int
    total_quotes: int
    total_invoices: int

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
    
    invoice_id = str(uuid.uuid4())
    invoice_number = await get_next_invoice_number()
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "client_id": quote["client_id"],
        "client_name": quote["client_name"],
        "quote_id": quote_id,
        "issue_date": datetime.now(timezone.utc).isoformat(),
        "items": quote["items"],
        "total_ht": quote["total_ht"],
        "total_vat": quote["total_vat"],
        "total_ttc": quote["total_ttc"],
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
    
    invoice_id = str(uuid.uuid4())
    invoice_number = await get_next_invoice_number()
    
    items = [item.model_dump() for item in invoice_data.items]
    total_ht, total_vat, total_ttc = calculate_totals(items)
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "client_id": invoice_data.client_id,
        "client_name": client["name"],
        "quote_id": invoice_data.quote_id,
        "issue_date": datetime.now(timezone.utc).isoformat(),
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
    return [InvoiceResponse(**i) for i in invoices]

@api_router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
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

# ============== PDF GENERATION ==============

async def get_company_settings():
    settings = await db.settings.find_one({"type": "company"}, {"_id": 0})
    if not settings:
        return CompanySettings()
    return CompanySettings(**{k: v for k, v in settings.items() if k != "type"})

def create_pdf(doc_type: str, doc_data: dict, company: CompanySettings, client: dict):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#EA580C'), spaceAfter=12)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#475569'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10)
    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#64748B'))
    
    elements = []
    
    # Header with company info
    company_name = company.company_name or "Votre Entreprise BTP"
    elements.append(Paragraph(company_name, title_style))
    
    if company.address:
        elements.append(Paragraph(company.address, header_style))
    if company.phone:
        elements.append(Paragraph(f"Tél: {company.phone}", header_style))
    if company.email:
        elements.append(Paragraph(f"Email: {company.email}", header_style))
    if company.siret:
        elements.append(Paragraph(f"SIRET: {company.siret}", header_style))
    if company.vat_number:
        elements.append(Paragraph(f"N° TVA: {company.vat_number}", header_style))
    
    elements.append(Spacer(1, 15*mm))
    
    # Document title
    if doc_type == "quote":
        doc_title = f"DEVIS N° {doc_data['quote_number']}"
    else:
        doc_title = f"FACTURE N° {doc_data['invoice_number']}"
    
    elements.append(Paragraph(doc_title, ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0F172A'))))
    elements.append(Spacer(1, 5*mm))
    
    # Date and client info table
    issue_date = doc_data['issue_date'][:10] if isinstance(doc_data['issue_date'], str) else doc_data['issue_date'].strftime('%Y-%m-%d')
    
    info_data = [
        [Paragraph(f"<b>Date d'émission:</b> {issue_date}", normal_style), Paragraph("<b>Client:</b>", normal_style)],
    ]
    
    if doc_type == "quote":
        validity_date = doc_data['validity_date'][:10] if isinstance(doc_data['validity_date'], str) else doc_data['validity_date'].strftime('%Y-%m-%d')
        info_data.append([Paragraph(f"<b>Validité:</b> {validity_date}", normal_style), Paragraph(client.get('name', ''), bold_style)])
    else:
        info_data.append([Paragraph("", normal_style), Paragraph(client.get('name', ''), bold_style)])
    
    info_data.append([Paragraph("", normal_style), Paragraph(client.get('address', ''), normal_style)])
    info_data.append([Paragraph("", normal_style), Paragraph(client.get('email', ''), normal_style)])
    
    info_table = Table(info_data, colWidths=[90*mm, 80*mm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10*mm))
    
    # Items table
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
    
    items_table = Table(table_data, colWidths=[70*mm, 20*mm, 30*mm, 20*mm, 30*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 8*mm))
    
    # Totals
    totals_data = [
        ["Total HT:", f"{doc_data['total_ht']:.2f} €"],
        ["Total TVA:", f"{doc_data['total_vat']:.2f} €"],
        ["Total TTC:", f"{doc_data['total_ttc']:.2f} €"],
    ]
    
    if doc_type == "invoice":
        payment_status_map = {"impaye": "Impayé", "paye": "Payé", "partiel": "Partiellement payé"}
        totals_data.append(["Statut:", payment_status_map.get(doc_data['payment_status'], doc_data['payment_status'])])
        if doc_data.get('paid_amount', 0) > 0:
            totals_data.append(["Montant payé:", f"{doc_data['paid_amount']:.2f} €"])
            remaining = doc_data['total_ttc'] - doc_data['paid_amount']
            totals_data.append(["Reste à payer:", f"{remaining:.2f} €"])
    
    totals_table = Table(totals_data, colWidths=[120*mm, 50*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EA580C')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(totals_table)
    
    # Notes
    if doc_data.get('notes'):
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("<b>Notes:</b>", bold_style))
        elements.append(Paragraph(doc_data['notes'], normal_style))
    
    # Legal mentions
    elements.append(Spacer(1, 15*mm))
    if doc_type == "quote":
        legal_text = "Ce devis est valable pour la durée indiquée ci-dessus. Signature précédée de la mention 'Bon pour accord'."
    else:
        payment_method_map = {"virement": "virement bancaire", "especes": "espèces", "cheque": "chèque"}
        method = payment_method_map.get(doc_data.get('payment_method', 'virement'), 'virement bancaire')
        legal_text = f"En cas de retard de paiement, une pénalité de 3 fois le taux d'intérêt légal sera appliquée. Mode de paiement: {method}."
    
    elements.append(Paragraph(legal_text, small_style))
    
    if company.siret:
        elements.append(Paragraph(f"SIRET: {company.siret} - TVA: {company.vat_number or 'N/A'}", small_style))
    
    doc.build(elements)
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
