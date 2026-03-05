# BTP Facture - Product Requirements Document

## Project Overview
BTP Facture is a complete SaaS platform for construction companies (BTP - Bâtiment et Travaux Publics) to manage quotes, invoices, projects, and clients.

## Current Status: Phases 1-3 Backend Complete ✅

### Completed (December 2025)

#### Phase 1 - Database Migration ✅
- **Supabase PostgreSQL 17.6** connected via Transaction Pooler
- **16 tables created** with Alembic migrations
- **Row Level Security (RLS)** enabled on all business tables
- **53 users migrated** from MongoDB
- **Multi-tenant architecture** with user_id filtering

#### Phase 2 - BTP Core Features Backend ✅
- **Projects Service** (`project_service.py`)
  - Full CRUD for projects (chantiers)
  - Task management with status tracking
  - Timeline data generation
  - Margin calculation per project
  
- **Work Item Library** (`work_item_library_service.py`)
  - 13 BTP categories (gros œuvre, électricité, plomberie, etc.)
  - 10 standard units (m², m³, h, forfait, etc.)
  - Template support for reusable items
  - Import/export capabilities

- **Quote Service** (`quote_service.py`)
  - Full CRUD with BTP VAT calculations
  - Multiple VAT rates (20%, 10%, 5.5%, 2.1%)
  - Electronic signature support
  - Quote duplication

- **Invoice Service** (`invoice_service.py`)
  - Progress invoicing (factures de situation)
  - Retenue de garantie (retention management)
  - Payment tracking
  - Project financial updates

#### Phase 3 - Financial Tools Backend ✅
- **Recurring Invoices** (`recurring_reminder_service.py`)
  - Weekly, monthly, quarterly, yearly frequencies
  - Automatic generation scheduling
  - Active/inactive toggle

- **Invoice Reminders** (`recurring_reminder_service.py`)
  - First, second, final reminder types
  - Scheduled date management
  - Bulk scheduling for invoices

- **Accounting Export** (`accounting_export_service.py`)
  - CSV export for invoices
  - CSV export for payments
  - VAT summary reports
  - Client balance reports
  - Financial period summaries

- **Admin Dashboard** (`admin_dashboard_service.py`)
  - User statistics (total, active, by plan, by role)
  - Profile completion metrics (4 categories, 11 fields)
  - Business metrics (invoices, quotes, clients, projects)
  - Alerts for missing information

### API Routes Active

#### PostgreSQL Routes (New)
- `/api/admin/*` - Admin analytics dashboard
- `/api/work-items/*` - Work item library
- `/api/financial/*` - Recurring invoices, reminders, exports
- `/api/projects/*` - Project management with tasks

#### MongoDB Routes (Legacy - still active)
- `/api/auth/*` - Authentication
- `/api/clients/*` - Client management
- `/api/quotes/*` - Quote management
- `/api/invoices/*` - Invoice management
- `/api/dashboard/*` - User dashboard

### Pending Implementation

#### Phase 4 - Advanced Features
- [ ] AI PDF Analysis (Gemini 3 Flash integration)
- [ ] Electronic Signatures UI
- [ ] Client Portal (token-based access)
- [ ] Stripe Payment integration

#### Phase 5 - Admin & Marketing
- [ ] Marketing Automation system
- [ ] Email campaign management
- [ ] Frontend integration for admin dashboard

### Frontend Integration Needed
- Connect new PostgreSQL routes to React components
- Create UI for:
  - Work Item Library management
  - Project timeline view
  - Recurring invoices
  - Admin dashboard
  - Profile completion indicator

## Technical Architecture

### Current (Hybrid)
- **Backend**: FastAPI with MongoDB + PostgreSQL
- **Frontend**: React with Tailwind CSS, Shadcn/UI
- **Database**: 
  - MongoDB (authentication, existing features)
  - PostgreSQL/Supabase (new features, migrated data)

### Database Connection
```
PostgreSQL: postgresql://postgres.zrpbrukjitrcshmflzbx:[PASSWORD]@aws-1-eu-central-1.pooler.supabase.com:6543/postgres
MongoDB: Running locally
```

### Key Services Created
```
/app/backend/app/services/
├── user_service.py              # User CRUD (PostgreSQL)
├── client_service.py            # Client management
├── project_service.py           # Projects & tasks
├── quote_service.py             # Quotes & signatures
├── invoice_service.py           # Invoices & payments
├── work_item_library_service.py # Work item library
├── recurring_reminder_service.py # Recurring invoices & reminders
├── accounting_export_service.py  # CSV exports
├── admin_dashboard_service.py    # Admin analytics
```

### API Routes Structure
```
/app/backend/app/api/routes/
├── auth.py       # Authentication
├── clients.py    # Client CRUD
├── projects.py   # Project management
├── quotes.py     # Quote management
├── invoices.py   # Invoice management
├── work_items.py # Work item library
├── financial.py  # Recurring & exports
├── admin.py      # Admin dashboard
```

## Key Credentials
- **Admin**: admin@btpfacture.com / Admin123!
- **Test User**: rafik.remila@gmail.com / Zeralda@0676

## Profile Completion Fields (11 total)
1. Logo uploaded
2. Company name
3. Company address
4. Company email
5. Company phone
6. SIRET
7. Legal form
8. VAT number
9. IBAN
10. BIC
11. Invoice footer (legal mentions)

## BTP-Specific Features Implemented
- Multiple VAT rates (20%, 10%, 5.5%, 2.1%)
- Retenue de garantie (5% default)
- Progress invoicing (factures de situation)
- 13 work categories
- 10 units of measurement

---
Last Updated: December 2025
