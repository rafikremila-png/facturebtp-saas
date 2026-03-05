# BTP Facture - Product Requirements Document

## Project Overview
BTP Facture is a complete SaaS platform for construction companies (BTP) to manage quotes, invoices, projects, and clients.

## Status: Phases 1-5 BACKEND COMPLETE ✅ | Frontend Integration IN PROGRESS

### Completed Features

#### Phase 1 - Database Migration ✅
- **Supabase PostgreSQL 17.6** connected
- **16 tables created** with Alembic migrations
- **Row Level Security (RLS)** enabled
- **53 users migrated** from MongoDB
- **Multi-tenant architecture** with user_id filtering

#### Phase 2 - BTP Core Features ✅
- **Projects Service** - Chantiers with tasks, timeline, margins
- **Work Item Library** - 13 BTP categories, 10 units
- **Quote Service** - VAT calculations, signatures
- **Invoice Service** - Progress invoicing, retentions

#### Phase 3 - Financial Tools ✅
- **Recurring Invoices** - Weekly/monthly/quarterly/yearly
- **Invoice Reminders** - Automatic scheduling
- **Accounting Export** - CSV exports (invoices, payments, VAT)
- **Admin Dashboard** - User stats, profile completion metrics

#### Phase 4 - Advanced Features ✅
- **AI PDF Analysis** (Gemini 3 Flash) - Extract quote items from plans
- **Electronic Signatures** - Legal compliance with audit trail
- **Client Portal** - Token-based access (no client account needed)
- **Stripe Payments** - Invoice payment via Checkout

#### Phase 5 - Admin & Marketing ✅
- **Admin Analytics Dashboard** - LIVE with PostgreSQL data
  - User statistics
  - Profile completion rates (4 categories, 11 fields)
  - Distribution charts
  - Missing info alerts
- Marketing automation - BACKEND READY (routes created)

### Frontend Pages Created
- `/admin/analytics` - Admin Analytics Dashboard ✅ WORKING

### API Routes Summary

| Route | Description | Status |
|-------|-------------|--------|
| `/api/admin/dashboard` | Admin analytics | ✅ Live |
| `/api/admin/users/statistics` | User stats | ✅ Live |
| `/api/admin/profile-completion` | Completion rates | ✅ Live |
| `/api/work-items/*` | Work item library | ✅ Live |
| `/api/financial/recurring` | Recurring invoices | ✅ Live |
| `/api/financial/reminders` | Payment reminders | ✅ Live |
| `/api/financial/export/*` | CSV exports | ✅ Live |
| `/api/ai/analyze-pdf` | PDF analysis | ✅ Live |
| `/api/ai/extract-quote-items` | Quote extraction | ✅ Live |
| `/api/portal/*` | Client portal | ✅ Live |
| `/api/payments/*` | Stripe payments | ✅ Live |

### Profile Completion Fields (11 total)
Tracked for each user:
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

### Key Stats from PostgreSQL
- **53 Total Users**
- **23 Active Users** (19 email verified)
- **42.4% Average Completion**
- **0 Complete Profiles** (opportunities for improvement!)

## Technical Stack

### Backend
- FastAPI (Hybrid MongoDB + PostgreSQL)
- SQLAlchemy + Alembic
- Motor (MongoDB)
- Stripe SDK
- Emergent Integrations (Gemini 3 Flash)

### Frontend
- React 18
- Tailwind CSS
- Shadcn/UI
- React Router v6

### Database
- MongoDB (legacy, still active)
- PostgreSQL via Supabase (new features)

## Key Credentials
- **Admin**: admin@btpfacture.com / Admin123!
- **Preview URL**: https://batiment-facture-1.preview.emergentagent.com

## Pending Frontend Work
- [ ] Work Item Library UI
- [ ] Project Timeline view
- [ ] Recurring Invoices management
- [ ] Client Portal pages
- [ ] Stripe payment flow UI
- [ ] PDF Upload for AI analysis

## Files Structure
```
/app/backend/
├── server.py                    # Main hybrid server
├── app/
│   ├── services/
│   │   ├── admin_dashboard_service.py     ✅
│   │   ├── work_item_library_service.py   ✅
│   │   ├── recurring_reminder_service.py  ✅
│   │   ├── accounting_export_service.py   ✅
│   │   ├── pdf_analysis_service.py        ✅
│   │   ├── client_portal_service.py       ✅
│   │   └── stripe_payment_service.py      ✅
│   └── api/routes/
│       ├── admin.py       ✅
│       ├── work_items.py  ✅
│       ├── financial.py   ✅
│       ├── ai.py          ✅
│       ├── portal.py      ✅
│       └── payments.py    ✅

/app/frontend/src/pages/
├── AdminAnalyticsPage.jsx  ✅ NEW
└── ... (existing pages)
```

---
Last Updated: December 2025
Status: Phases 1-5 Backend Complete, Frontend Integration In Progress
