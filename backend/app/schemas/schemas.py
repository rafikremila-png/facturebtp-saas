"""
Pydantic Schemas for BTP Facture SaaS
Request/Response validation models
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum

# ============== ENUMS ==============

class UserRoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class QuoteStatusEnum(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    SIGNED = "signed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

class InvoiceStatusEnum(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class ProjectStatusEnum(str, Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentMethodEnum(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CASH = "cash"
    CARD = "card"
    STRIPE = "stripe"

class RecurringFrequencyEnum(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

# ============== BASE SCHEMAS ==============

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        populate_by_name = True

# ============== AUTH SCHEMAS ==============

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)
    phone: Optional[str] = None
    company_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

# ============== USER SCHEMAS ==============

class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(BaseSchema):
    id: str
    email: str
    name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    email_verified: bool
    subscription_plan: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

class UserListResponse(BaseSchema):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    email_verified: bool
    created_at: datetime

# ============== USER SETTINGS SCHEMAS ==============

class UserSettingsBase(BaseModel):
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_email: Optional[EmailStr] = None
    company_phone: Optional[str] = None
    company_website: Optional[str] = None
    siret: Optional[str] = Field(None, max_length=14)
    vat_number: Optional[str] = None
    rcs: Optional[str] = None
    capital: Optional[str] = None
    legal_form: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    bank_name: Optional[str] = None
    default_payment_days: Optional[int] = 30
    vat_rates: Optional[List[float]] = [20.0, 10.0, 5.5, 2.1]
    retention_enabled: Optional[bool] = False
    default_retention_rate: Optional[float] = 5.0
    quote_validity_days: Optional[int] = 30
    quote_prefix: Optional[str] = "DEV"
    invoice_prefix: Optional[str] = "FAC"
    invoice_notes: Optional[str] = None
    invoice_footer: Optional[str] = None

class UserSettingsUpdate(UserSettingsBase):
    pass

class UserSettingsResponse(UserSettingsBase, BaseSchema):
    id: str
    user_id: str
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# ============== CLIENT SCHEMAS ==============

class ClientBase(BaseModel):
    name: str = Field(..., min_length=2)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "France"
    company_name: Optional[str] = None
    siret: Optional[str] = None
    vat_number: Optional[str] = None
    client_type: Optional[str] = "individual"
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    company_name: Optional[str] = None
    siret: Optional[str] = None
    vat_number: Optional[str] = None
    client_type: Optional[str] = None
    notes: Optional[str] = None

class ClientResponse(ClientBase, BaseSchema):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

# ============== PROJECT SCHEMAS ==============

class ProjectBase(BaseModel):
    project_name: str = Field(..., min_length=2)
    client_id: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    status: Optional[str] = "planning"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    estimated_duration_days: Optional[int] = None
    budget: Optional[float] = 0
    estimated_cost: Optional[float] = 0
    permit_number: Optional[str] = None
    insurance_number: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    client_id: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    estimated_duration_days: Optional[int] = None
    budget: Optional[float] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    permit_number: Optional[str] = None
    insurance_number: Optional[str] = None

class ProjectResponse(ProjectBase, BaseSchema):
    id: str
    user_id: str
    project_number: Optional[str] = None
    actual_cost: Optional[float] = 0
    total_invoiced: Optional[float] = 0
    total_paid: Optional[float] = 0
    created_at: datetime
    updated_at: datetime
    client: Optional[ClientResponse] = None

class ProjectMarginResponse(BaseModel):
    id: str
    project_name: str
    budget: float
    actual_cost: float
    total_invoiced: float
    total_paid: float
    margin: float
    margin_percentage: float

# ============== PROJECT TASK SCHEMAS ==============

class ProjectTaskBase(BaseModel):
    title: str = Field(..., min_length=2)
    description: Optional[str] = None
    status: Optional[str] = "pending"
    priority: Optional[str] = "medium"
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    progress_percentage: Optional[int] = 0

class ProjectTaskCreate(ProjectTaskBase):
    project_id: str

class ProjectTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    progress_percentage: Optional[int] = None

class ProjectTaskResponse(ProjectTaskBase, BaseSchema):
    id: str
    project_id: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

# ============== WORK ITEM SCHEMAS ==============

class WorkItemBase(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = "u"
    unit_price: float = Field(..., ge=0)
    vat_rate: Optional[float] = 20.0
    labor_cost: Optional[float] = 0
    material_cost: Optional[float] = 0
    reference: Optional[str] = None

class WorkItemCreate(WorkItemBase):
    pass

class WorkItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    vat_rate: Optional[float] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    reference: Optional[str] = None

class WorkItemResponse(WorkItemBase, BaseSchema):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

# ============== QUOTE ITEM SCHEMA ==============

class QuoteItem(BaseModel):
    description: str
    quantity: float = Field(..., ge=0)
    unit: str = "u"
    unit_price: float = Field(..., ge=0)
    vat_rate: float = 20.0
    total_ht: Optional[float] = None
    work_item_id: Optional[str] = None

    @validator('total_ht', always=True)
    def calculate_total(cls, v, values):
        if v is None:
            return values.get('quantity', 0) * values.get('unit_price', 0)
        return v

# ============== QUOTE SCHEMAS ==============

class QuoteBase(BaseModel):
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    items: List[QuoteItem] = []
    validity_date: Optional[datetime] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = 0
    retention_rate: Optional[float] = 0
    notes: Optional[str] = None
    terms: Optional[str] = None

class QuoteCreate(QuoteBase):
    pass

class QuoteUpdate(BaseModel):
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[QuoteItem]] = None
    status: Optional[str] = None
    validity_date: Optional[datetime] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    retention_rate: Optional[float] = None
    notes: Optional[str] = None
    terms: Optional[str] = None

class QuoteResponse(QuoteBase, BaseSchema):
    id: str
    user_id: str
    quote_number: str
    status: str
    quote_date: datetime
    subtotal_ht: float
    total_vat: float
    total_ttc: float
    discount_amount: Optional[float] = 0
    retention_amount: Optional[float] = 0
    pdf_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    client: Optional[ClientResponse] = None
    project: Optional[ProjectResponse] = None

# ============== QUOTE SIGNATURE SCHEMAS ==============

class QuoteSignatureCreate(BaseModel):
    signer_name: str = Field(..., min_length=2)
    signer_email: EmailStr
    signer_title: Optional[str] = None
    signature_data: str  # Base64 encoded signature

class QuoteSignatureResponse(BaseSchema):
    id: str
    quote_id: str
    signer_name: str
    signer_email: str
    signer_title: Optional[str] = None
    signed_at: datetime
    certificate_pdf_url: Optional[str] = None

# ============== INVOICE ITEM SCHEMA ==============

class InvoiceItem(BaseModel):
    description: str
    quantity: float = Field(..., ge=0)
    unit: str = "u"
    unit_price: float = Field(..., ge=0)
    vat_rate: float = 20.0
    total_ht: Optional[float] = None

    @validator('total_ht', always=True)
    def calculate_total(cls, v, values):
        if v is None:
            return values.get('quantity', 0) * values.get('unit_price', 0)
        return v

# ============== INVOICE SCHEMAS ==============

class InvoiceBase(BaseModel):
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    quote_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    items: List[InvoiceItem] = []
    due_date: Optional[datetime] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = 0
    invoice_type: Optional[str] = "standard"
    situation_number: Optional[int] = None
    progress_percentage: Optional[float] = 100
    retention_rate: Optional[float] = 0
    notes: Optional[str] = None
    payment_terms: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[InvoiceItem]] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    invoice_type: Optional[str] = None
    progress_percentage: Optional[float] = None
    retention_rate: Optional[float] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None

class InvoiceResponse(InvoiceBase, BaseSchema):
    id: str
    user_id: str
    invoice_number: str
    status: str
    invoice_date: datetime
    subtotal_ht: float
    total_vat: float
    total_ttc: float
    discount_amount: Optional[float] = 0
    previous_invoiced: Optional[float] = 0
    current_amount: Optional[float] = 0
    retention_amount: Optional[float] = 0
    amount_paid: float
    amount_due: float
    pdf_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    client: Optional[ClientResponse] = None
    project: Optional[ProjectResponse] = None

# ============== PAYMENT SCHEMAS ==============

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float = Field(..., gt=0)
    payment_date: Optional[datetime] = None
    payment_method: Optional[str] = "bank_transfer"
    reference: Optional[str] = None
    notes: Optional[str] = None

class PaymentResponse(BaseSchema):
    id: str
    invoice_id: str
    amount: float
    payment_date: datetime
    payment_method: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

# ============== RECURRING INVOICE SCHEMAS ==============

class RecurringInvoiceBase(BaseModel):
    client_id: str
    title: str
    description: Optional[str] = None
    items: List[InvoiceItem] = []
    frequency: str = "monthly"
    start_date: datetime
    end_date: Optional[datetime] = None

class RecurringInvoiceCreate(RecurringInvoiceBase):
    pass

class RecurringInvoiceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[InvoiceItem]] = None
    frequency: Optional[str] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None

class RecurringInvoiceResponse(RecurringInvoiceBase, BaseSchema):
    id: str
    user_id: str
    status: str
    next_invoice_date: datetime
    last_invoice_date: Optional[datetime] = None
    invoices_generated: int
    subtotal_ht: float
    total_vat: float
    total_ttc: float
    created_at: datetime
    updated_at: datetime

# ============== INVOICE REMINDER SCHEMAS ==============

class InvoiceReminderCreate(BaseModel):
    invoice_id: str
    reminder_type: str
    reminder_date: datetime

class InvoiceReminderResponse(BaseSchema):
    id: str
    invoice_id: str
    reminder_type: str
    reminder_date: datetime
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime

# ============== FINANCIAL DASHBOARD SCHEMAS ==============

class FinancialSummary(BaseModel):
    total_revenue: float
    total_unpaid: float
    total_overdue: float
    average_payment_delay: float
    total_vat_collected: float
    monthly_revenue: List[Dict[str, Any]]
    invoice_status_breakdown: Dict[str, int]
    top_clients: List[Dict[str, Any]]

class CashflowData(BaseModel):
    month: str
    income: float
    expenses: float
    net: float

# ============== AI ANALYSIS SCHEMAS ==============

class AIDocumentAnalysisRequest(BaseModel):
    file_path: Optional[str] = None
    analysis_type: str = "invoice"  # invoice, quote, contract

class AIDocumentAnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None

class AIQuoteGenerationRequest(BaseModel):
    project_description: str
    project_type: Optional[str] = None
    surface_area: Optional[float] = None
    location: Optional[str] = None

class AIQuoteGenerationResponse(BaseModel):
    success: bool
    suggested_items: List[Dict[str, Any]] = []
    estimated_total: Optional[float] = None
    notes: Optional[str] = None

# ============== ACCOUNTING EXPORT SCHEMAS ==============

class AccountingExportRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    export_type: str = "all"  # all, invoices, payments, vat
    format: str = "csv"  # csv, excel

class AccountingExportResponse(BaseModel):
    success: bool
    file_url: Optional[str] = None
    filename: Optional[str] = None
    records_count: int = 0

# ============== ADMIN SCHEMAS ==============

class AdminMetrics(BaseModel):
    total_users: int
    active_users: int
    new_users_this_month: int
    users_by_plan: Dict[str, int]
    total_revenue: float
    average_profile_completion: float

class UserProfileCompletion(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    completion_percentage: int
    completed_count: int
    total_count: int
    items: List[Dict[str, Any]]
    summary: Dict[str, int]

# ============== CLIENT PORTAL SCHEMAS ==============

class ClientPortalAccess(BaseModel):
    token: str
    client_id: str
    expires_at: datetime

class ClientPortalQuoteView(BaseModel):
    quote: QuoteResponse
    can_sign: bool
    signature: Optional[QuoteSignatureResponse] = None

class ClientPortalInvoiceView(BaseModel):
    invoice: InvoiceResponse
    can_pay: bool
    payments: List[PaymentResponse] = []
    payment_url: Optional[str] = None

# Update forward references
TokenResponse.model_rebuild()
