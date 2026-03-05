# BTP Facture - Product Requirements Document

## Project Overview
BTP Facture is a complete SaaS platform for construction companies (BTP - Bâtiment et Travaux Publics) to manage quotes, invoices, projects, and clients.

## Current Status: Phase 1 - Architecture Migration (In Progress)

### Completed (December 2025)

#### Phase 1.1 - Database Setup ✅
- **Supabase PostgreSQL Connection**: Successfully connected to Supabase PostgreSQL 17.6
- **Database Schema Created**: All 16 tables created via Alembic migration
  - users, user_settings, clients, projects, project_tasks
  - quotes, quote_signatures, invoices, payments
  - work_items, recurring_invoices, invoice_reminders
  - marketing_notifications, audit_logs, otps
- **Data Migration**: 53 users migrated from MongoDB to PostgreSQL
- **Super Admin Created**: admin@btpfacture.com initialized in PostgreSQL

#### Phase 1.2 - New Modular Architecture ✅
- **Services Layer** (PostgreSQL/SQLAlchemy):
  - `user_service.py` - Complete user CRUD with settings
  - `client_service.py` - Client management with portal tokens
  - `project_service.py` - Projects (chantiers) with tasks and margins
  - `quote_service.py` - Quotes with electronic signatures
  - `invoice_service.py` - Invoices with progress billing and retentions

- **API Routes** (FastAPI):
  - `/api/auth/*` - Authentication routes
  - `/api/clients/*` - Client management
  - `/api/projects/*` - Project/Chantier management
  - `/api/quotes/*` - Quote management
  - `/api/invoices/*` - Invoice management

- **Core Configuration**:
  - `database.py` - Async PostgreSQL with NullPool for Supabase Transaction Pooler
  - `config.py` - Centralized settings management
  - `security.py` - JWT tokens and password hashing

### In Progress
- Integration of new PostgreSQL routes with existing frontend
- Gradual replacement of MongoDB queries

### Pending Phases

#### Phase 2 - BTP Core Features
- [ ] Project Management (Chantiers) - UI integration
- [ ] Construction Site Planning - Timeline view
- [ ] Margin Tracking - Financial calculations
- [ ] Progress Invoicing (Facturation Situation) - Per-line billing
- [ ] Work Library (Bibliothèque d'ouvrages) - Reusable items

#### Phase 3 - Financial Tools
- [ ] Financial Dashboard - Analytics and reports
- [ ] Recurring Invoices - Automated generation
- [ ] Automatic Reminders - Email scheduling
- [ ] Accounting Export - CSV/Excel generation

#### Phase 4 - Advanced Features
- [ ] AI PDF Analysis (Gemini 3 Flash) - Document extraction
- [ ] Electronic Signatures - Legal compliance
- [ ] Client Portal - Token-based access
- [ ] Stripe Payments - Online payment button

#### Phase 5 - Admin & Marketing
- [ ] Global Admin Dashboard - Platform metrics
- [ ] Marketing Automation - Email campaigns

## Technical Architecture

### Current (Hybrid)
- **Backend**: FastAPI with MongoDB (server.py - active)
- **New Backend**: FastAPI with PostgreSQL/Supabase (app/main.py - ready)
- **Frontend**: React with Tailwind CSS, Shadcn/UI
- **Database**: 
  - MongoDB (active for current operations)
  - PostgreSQL/Supabase (ready, 53 users migrated)

### Target Architecture
- **Backend**: Modular FastAPI with PostgreSQL/Supabase
- **Frontend**: React (unchanged)
- **Database**: PostgreSQL via Supabase
- **AI**: Gemini 3 Flash via Emergent LLM Key
- **Payments**: Stripe (keys configured)
- **Email**: Mailtrap SMTP (sandbox)

## Database Connection
```
DATABASE_URL=postgresql://postgres.zrpbrukjitrcshmflzbx:[PASSWORD]@aws-1-eu-central-1.pooler.supabase.com:6543/postgres
```

## Key Credentials
- **Admin**: admin@btpfacture.com / Admin123!
- **Test User**: rafik.remila@gmail.com / Zeralda@0676

## Files Structure
```
/app/backend/
├── server.py              # Current active backend (MongoDB)
├── app/
│   ├── main.py            # New modular backend (PostgreSQL)
│   ├── core/
│   │   ├── database.py    # PostgreSQL connection
│   │   ├── config.py      # Settings
│   │   └── security.py    # Auth utilities
│   ├── models/
│   │   └── models.py      # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py     # Pydantic schemas
│   ├── services/          # Business logic
│   │   ├── user_service.py
│   │   ├── client_service.py
│   │   ├── project_service.py
│   │   ├── quote_service.py
│   │   └── invoice_service.py
│   └── api/routes/        # API endpoints
│       ├── auth.py
│       ├── clients.py
│       ├── projects.py
│       ├── quotes.py
│       └── invoices.py
├── alembic/               # Database migrations
└── migrate_to_postgres.py # Data migration script

/app/frontend/src/
├── components/
├── pages/
└── App.js
```

## Next Steps (Immediate Priority)
1. Test new PostgreSQL API endpoints independently
2. Create adapter layer to switch frontend to new backend
3. Implement remaining BTP-specific features
4. Complete frontend integration

## Known Issues
- MongoDB data has orphan records (clients/quotes/invoices without user_id)
- Old MongoDB backend still active (by design during transition)

---
Last Updated: December 2025
