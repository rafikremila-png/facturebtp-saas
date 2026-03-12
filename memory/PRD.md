# FactureBTP - SaaS Platform for Construction Companies

## Original Problem Statement
Transform the FactureBTP project into a complete, production-ready SaaS platform for construction companies with multi-tenant architecture using FastAPI/PostgreSQL (Supabase).

## Current Architecture
- **Backend**: FastAPI with PostgreSQL (Supabase) + MongoDB (legacy)
- **Frontend**: React with Shadcn/UI, Tailwind CSS
- **Database**: PostgreSQL via Supabase (multi-tenant with user_id) + MongoDB (legacy data)
- **Authentication**: Supabase Auth (migrated from JWT)

---

## Implemented Features (Dec 2025)

### Core Features ✅
- [x] User authentication and authorization (Supabase Auth)
- [x] Client management
- [x] Quote creation and management
- [x] Invoice creation and management
- [x] Project (Chantier) management
- [x] Work Library (Bibliothèque d'ouvrages)
- [x] Profile completion indicator

### SaaS/Trial System ✅ (NEW - Dec 2025)
- [x] **7-day Free Trial** - Auto-starts on registration
- [x] **Usage Limits** - 5 quotes/invoices during trial
- [x] **Super Admin Role** - Unlimited access, no restrictions
- [x] **Subscription Plans** - Essentiel (19€), Pro (29€), Business (59€)
- [x] **UI Banners** - Trial status and usage counters on dashboard
- [x] **Stripe Integration** - Checkout sessions configured

### Service Features ✅
- [x] Service Categories (6 pre-filled categories)
- [x] Service Requests with category selection
- [x] Status badges (pending=orange, in_progress=blue, completed=green, cancelled=red)
- [x] Filters by status and category

### Financial Dashboard ✅
- [x] Revenue tracking (total, paid, pending, overdue)
- [x] Monthly revenue chart
- [x] Invoices by status breakdown
- [x] Recent payments list
- [x] CSV Export
- [x] Excel Export

### Electronic Signatures ✅ (NEW!)
- [x] **Client Portal** - Secure access via token
- [x] **Signature Canvas** - Draw signature with mouse or touch
- [x] **Legal Compliance** - IP address, user agent, timestamp recorded
- [x] **Pre-filled Forms** - Client info auto-filled
- [x] **Visual Confirmation** - Signed badge and details shown
- [x] **Table**: `quote_signatures` with full audit trail

---

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Current user
- `GET /api/profile/completion` - Profile completion status

### Client Portal & Signatures (MongoDB-based)
- `POST /api/clients/{client_id}/portal-token` - Generate portal access token ✅
- `GET /api/portal/{token}` - Get portal data (quotes, invoices) ✅
- `POST /api/portal/{token}/quotes/{quote_id}/sign` - Sign a quote ✅

**UI Entry Point**: Clients page → Action menu → "Portail & Signature" → Modal with link

### Service Requests
- `GET /api/service-categories` - List categories
- `POST /api/service-requests` - Create request
- `GET /api/service-requests/me` - User's requests
- `PUT /api/service-requests/{id}/status` - Update status

### Financial Reports
- `GET /api/reports/financial` - Dashboard stats
- `GET /api/reports/financial/export/csv` - CSV export
- `GET /api/reports/financial/export/excel` - Excel export

---

## Electronic Signature Flow

1. **Generate Token** - Admin generates portal link for client
2. **Client Access** - Client opens `/portal/{token}` (no login required)
3. **View Quotes** - Client sees pending quotes with "Signer" button
4. **Sign Quote** - Modal opens with:
   - Pre-filled name and email
   - Optional title/function
   - Signature canvas
   - Legal disclaimer
5. **Submit** - Signature data, IP, timestamp saved
6. **Confirmation** - Green badge shows "Signé par X le DATE"

### Signature Data Stored
- `signer_name` - Full name
- `signer_email` - Email address
- `signer_title` - Optional function
- `signature_data` - Base64 PNG image
- `ip_address` - Client IP
- `user_agent` - Browser info
- `signed_at` - Timestamp

---

## Pre-filled Service Categories

1. **Site Web** - Website creation, redesign, e-commerce
2. **SEO** - SEO optimization, audit, Google Business
3. **Marketing Digital** - Google Ads, Facebook Ads, Email
4. **Automatisation / IA** - Workflows, Chatbots, Analytics
5. **CRM** - Setup, training, data migration
6. **Design** - Landing pages, branding, business cards

---

## Upcoming Tasks (P1)

- [ ] **Full PostgreSQL Migration** - Remove MongoDB, migrate server.py routes to Supabase
- [ ] **Recurring Invoices** - Automatic invoice generation with cron job
- [ ] **AI PDF Analysis** - Gemini Vision for construction plan analysis UI
- [ ] **Work Library in Quotes** - Quick add items from library to quotes

---

## Recently Fixed (Mar 2026)

- [x] **Renamed "Facturation" → "Abonnement"** in sidebar menu
- [x] **Fixed BillingPage** - Now correctly loads subscription plans
- [x] **Updated routes** - `/facturation` redirects to `/abonnement`
- [x] **Fixed Stripe URLs** - Checkout success/cancel redirects to `/abonnement`
- [x] **Fixed Admin Pages Auth** - AdminMetricsPage, AdminAnalyticsPage now use Supabase Auth properly
- [x] **Fixed deps.py** - Updated to use Supabase Auth instead of legacy JWT
- [x] **Fixed API interceptor** - Prevents unnecessary sign-out on 401 errors during init
- [x] **Verified Trial Banner** - Shows correctly for trial users with countdown and limits

### Audit Bugs Fixed (Mar 2026)
- [x] **CRITICAL: User Auto-Sync** - Users in Supabase Auth now auto-create in PostgreSQL users table
- [x] **CRITICAL: Financial Dashboard** - New MongoDB-based route `/reports/financial` working
- [x] **HIGH: Plans Unified** - `/trial/plans` now matches `/subscription/plans` structure
- [x] **MEDIUM: CORS Restricted** - Production domains whitelisted, no more `*` wildcard
- [x] **Rate Limiting** - Already configured on auth routes (5/min login, 5/hour register)

---

## Architecture Note (Current State)

The application currently operates in **hybrid mode**:
- **MongoDB (test_database)**: Authentication, clients, quotes, invoices - active data
- **PostgreSQL (Supabase)**: New features (service requests, financial reports, user sync)

A user synchronization service (`user_sync_service.py`) bridges the two databases.

**Target State**: Full PostgreSQL/Supabase architecture (migration in progress).

---

## Test Credentials
- **Super Admin**: rafik.remila@gmail.com / Zeralda@0676
- **Trial User**: test.trial@btpfacture.com / TestTrial123!
- **Admin Legacy**: admin@btpfacture.com / Admin123!

## Preview URL
https://construction-billing-3.preview.emergentagent.com

## Key Routes
- `/abonnement` - Subscription/billing page (renamed from /facturation)
- `/devis` - Quotes
- `/factures` - Invoices
- `/clients` - Clients
- `/portal/{token}` - Client signature portal

## Test Portal Token (7 days validity)
`/portal/WQIBtLIGFfMwM8p1S-pyXaEp7fxY6e8koe6lAlnnxsp0TbKb32nVjJ9uyCsGtXIt`
