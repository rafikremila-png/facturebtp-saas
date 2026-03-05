"""
SQLAlchemy Models for BTP Facture SaaS
Complete database schema for PostgreSQL/Supabase
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime, 
    ForeignKey, JSON, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# ============== ENUMS ==============

class UserRole:
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class QuoteStatus:
    DRAFT = "draft"
    SENT = "sent"
    SIGNED = "signed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

class InvoiceStatus:
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class ProjectStatus:
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentMethod:
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CASH = "cash"
    CARD = "card"
    STRIPE = "stripe"

class RecurringFrequency:
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

# ============== USER MODEL ==============

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(50))
    role = Column(String(20), default=UserRole.USER, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    email_verified = Column(Boolean, default=False)
    
    # Subscription
    subscription_plan = Column(String(50), default="free")
    subscription_status = Column(String(20), default="active")
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    
    # Security
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    last_login = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")
    work_items = relationship("WorkItem", back_populates="user", cascade="all, delete-orphan")

# ============== USER SETTINGS MODEL ==============

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Company Information
    company_name = Column(String(255))
    company_address = Column(Text)
    company_email = Column(String(255))
    company_phone = Column(String(50))
    company_website = Column(String(255))
    
    # Legal Information
    siret = Column(String(14))
    vat_number = Column(String(20))
    rcs = Column(String(100))
    capital = Column(String(50))
    legal_form = Column(String(100))
    
    # Banking Information
    iban = Column(String(34))
    bic = Column(String(11))
    bank_name = Column(String(100))
    
    # Logo
    logo_url = Column(String(500))
    logo_base64 = Column(Text)
    
    # Invoice Settings
    default_payment_days = Column(Integer, default=30)
    vat_rates = Column(JSON, default=[20.0, 10.0, 5.5, 2.1])
    retention_enabled = Column(Boolean, default=False)
    default_retention_rate = Column(Float, default=5.0)
    
    # Quote Settings
    quote_validity_days = Column(Integer, default=30)
    quote_prefix = Column(String(20), default="DEV")
    
    # Invoice Settings
    invoice_prefix = Column(String(20), default="FAC")
    invoice_notes = Column(Text)
    invoice_footer = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="settings")

# ============== CLIENT MODEL ==============

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    
    # Address
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="France")
    
    # Legal Information (for companies)
    company_name = Column(String(255))
    siret = Column(String(14))
    vat_number = Column(String(20))
    
    # Client Type
    client_type = Column(String(20), default="individual")  # individual, company
    
    # Notes
    notes = Column(Text)
    
    # Portal Access Token
    access_token = Column(String(255))
    token_expires_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="clients")
    projects = relationship("Project", back_populates="client", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="client", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")

# ============== PROJECT MODEL ==============

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), index=True)
    
    # Project Information
    project_name = Column(String(255), nullable=False)
    project_number = Column(String(50), index=True)
    description = Column(Text)
    
    # Location
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(20))
    
    # Status & Timeline
    status = Column(String(20), default=ProjectStatus.PLANNING, index=True)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    estimated_duration_days = Column(Integer)
    
    # Budget & Financials
    budget = Column(Float, default=0)
    estimated_cost = Column(Float, default=0)
    actual_cost = Column(Float, default=0)
    total_invoiced = Column(Float, default=0)
    total_paid = Column(Float, default=0)
    
    # BTP Specific
    permit_number = Column(String(100))
    insurance_number = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    client = relationship("Client", back_populates="projects")
    quotes = relationship("Quote", back_populates="project")
    invoices = relationship("Invoice", back_populates="project")
    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")

# ============== PROJECT TASK MODEL ==============

class ProjectTask(Base):
    __tablename__ = "project_tasks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Task Information
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Status & Timeline
    status = Column(String(20), default="pending")  # pending, in_progress, completed
    priority = Column(String(20), default="medium")  # low, medium, high
    start_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Assignment
    assigned_to = Column(String(255))
    
    # Progress
    progress_percentage = Column(Integer, default=0)
    
    # Order
    sort_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")

# ============== WORK ITEM MODEL (Bibliothèque d'ouvrages) ==============

class WorkItem(Base):
    __tablename__ = "work_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Item Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)
    
    # Pricing
    unit = Column(String(50), default="u")  # u, m², m³, ml, h, forfait
    unit_price = Column(Float, nullable=False)
    vat_rate = Column(Float, default=20.0)
    
    # Labor & Materials breakdown
    labor_cost = Column(Float, default=0)
    material_cost = Column(Float, default=0)
    
    # Reference
    reference = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="work_items")

# ============== QUOTE MODEL ==============

class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    
    # Quote Information
    quote_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255))
    description = Column(Text)
    
    # Status
    status = Column(String(20), default=QuoteStatus.DRAFT, index=True)
    
    # Dates
    quote_date = Column(DateTime(timezone=True), default=utc_now)
    validity_date = Column(DateTime(timezone=True))
    
    # Items (JSON for flexibility)
    items = Column(JSON, default=[])
    
    # Totals
    subtotal_ht = Column(Float, default=0)
    total_vat = Column(Float, default=0)
    total_ttc = Column(Float, default=0)
    
    # Discount
    discount_type = Column(String(20))  # percentage, fixed
    discount_value = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    
    # BTP Specific
    retention_rate = Column(Float, default=0)
    retention_amount = Column(Float, default=0)
    
    # Notes
    notes = Column(Text)
    terms = Column(Text)
    
    # PDF
    pdf_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="quotes")
    client = relationship("Client", back_populates="quotes")
    project = relationship("Project", back_populates="quotes")
    signature = relationship("QuoteSignature", back_populates="quote", uselist=False, cascade="all, delete-orphan")

# ============== QUOTE SIGNATURE MODEL ==============

class QuoteSignature(Base):
    __tablename__ = "quote_signatures"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Signer Information
    signer_name = Column(String(255), nullable=False)
    signer_email = Column(String(255), nullable=False)
    signer_title = Column(String(100))
    
    # Signature Data
    signature_data = Column(Text)  # Base64 encoded signature image
    
    # Legal Information
    ip_address = Column(String(50))
    user_agent = Column(Text)
    signed_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Certificate
    certificate_pdf_url = Column(String(500))
    certificate_hash = Column(String(64))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Relationships
    quote = relationship("Quote", back_populates="signature")

# ============== INVOICE MODEL ==============

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="SET NULL"), index=True)
    
    # Invoice Information
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255))
    description = Column(Text)
    
    # Status
    status = Column(String(20), default=InvoiceStatus.DRAFT, index=True)
    
    # Dates
    invoice_date = Column(DateTime(timezone=True), default=utc_now)
    due_date = Column(DateTime(timezone=True))
    paid_date = Column(DateTime(timezone=True))
    
    # Items (JSON for flexibility)
    items = Column(JSON, default=[])
    
    # Totals
    subtotal_ht = Column(Float, default=0)
    total_vat = Column(Float, default=0)
    total_ttc = Column(Float, default=0)
    
    # Discount
    discount_type = Column(String(20))
    discount_value = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    
    # BTP Progress Invoicing (Situation)
    invoice_type = Column(String(20), default="standard")  # standard, situation, final
    situation_number = Column(Integer)
    progress_percentage = Column(Float, default=100)
    previous_invoiced = Column(Float, default=0)
    current_amount = Column(Float, default=0)
    
    # Retention
    retention_rate = Column(Float, default=0)
    retention_amount = Column(Float, default=0)
    retention_released = Column(Boolean, default=False)
    
    # Payment
    amount_paid = Column(Float, default=0)
    amount_due = Column(Float, default=0)
    
    # Stripe
    stripe_payment_id = Column(String(255))
    stripe_checkout_session_id = Column(String(255))
    
    # Notes
    notes = Column(Text)
    payment_terms = Column(Text)
    
    # PDF
    pdf_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    client = relationship("Client", back_populates="invoices")
    project = relationship("Project", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    reminders = relationship("InvoiceReminder", back_populates="invoice", cascade="all, delete-orphan")

# ============== PAYMENT MODEL ==============

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Payment Information
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), default=utc_now)
    payment_method = Column(String(20), default=PaymentMethod.BANK_TRANSFER)
    
    # Reference
    reference = Column(String(100))
    transaction_id = Column(String(255))
    
    # Stripe
    stripe_payment_intent_id = Column(String(255))
    stripe_charge_id = Column(String(255))
    
    # Notes
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")

# ============== RECURRING INVOICE MODEL ==============

class RecurringInvoice(Base):
    __tablename__ = "recurring_invoices"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Template
    title = Column(String(255), nullable=False)
    description = Column(Text)
    items = Column(JSON, default=[])
    
    # Totals
    subtotal_ht = Column(Float, default=0)
    total_vat = Column(Float, default=0)
    total_ttc = Column(Float, default=0)
    
    # Schedule
    frequency = Column(String(20), default=RecurringFrequency.MONTHLY)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True))
    next_invoice_date = Column(DateTime(timezone=True), nullable=False, index=True)
    last_invoice_date = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(20), default="active", index=True)  # active, paused, completed
    invoices_generated = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

# ============== INVOICE REMINDER MODEL ==============

class InvoiceReminder(Base):
    __tablename__ = "invoice_reminders"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Reminder Information
    reminder_type = Column(String(20), nullable=False)  # before_due, on_due, after_due_7, after_due_14
    reminder_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, sent, cancelled
    sent_at = Column(DateTime(timezone=True))
    
    # Email
    email_subject = Column(String(255))
    email_body = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="reminders")

# ============== MARKETING NOTIFICATION MODEL ==============

class MarketingNotification(Base):
    __tablename__ = "marketing_notifications"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    # Notification Information
    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Targeting
    target_audience = Column(String(50))  # all, free_users, trial_users, etc.
    
    # Schedule
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(20), default="pending")  # pending, sent, read, dismissed
    read_at = Column(DateTime(timezone=True))
    
    # Action
    action_url = Column(String(500))
    action_label = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)

# ============== AUDIT LOG MODEL ==============

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    
    # Action Information
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), index=True)
    entity_id = Column(String(36))
    
    # Details
    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

# ============== OTP MODEL ==============

class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), nullable=False, index=True)
    
    # OTP Information
    code = Column(String(10), nullable=False)
    otp_type = Column(String(50), nullable=False)
    
    # Target
    target_user_id = Column(String(36))
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)

# ============== INDEXES ==============

# Composite indexes for common queries
Index('idx_quotes_user_status', Quote.user_id, Quote.status)
Index('idx_invoices_user_status', Invoice.user_id, Invoice.status)
Index('idx_invoices_user_due_date', Invoice.user_id, Invoice.due_date)
Index('idx_projects_user_status', Project.user_id, Project.status)
Index('idx_reminders_date_status', InvoiceReminder.reminder_date, InvoiceReminder.status)
