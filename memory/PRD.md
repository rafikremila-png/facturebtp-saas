# BTP Facture - PRD (Product Requirements Document)

## Problem Statement
Application SaaS de facturation pour le secteur BTP (Bâtiment et Travaux Publics). Permet aux artisans et entreprises de créer des devis, factures, gérer les clients et suivre les paiements.

## Architecture
- **Frontend:** React + Supabase JS + Shadcn/UI + TailwindCSS
- **Backend:** FastAPI minimal (email only via Resend)
- **Database:** Supabase PostgreSQL with RLS
- **Auth:** Supabase Auth (email/password + OTP)
- **Emails:** Resend API (transactional emails)
- **PDF:** Client-side jsPDF generation
- **CSV:** Client-side export

## Users
- **Super Admin:** rafik.remila@gmail.com, admin@btpfacture.com (role: super_admin)
- Super Admins bypass all RLS policies via `is_super_admin()` function

## Core Features (Implemented)
- User authentication (login/signup with OTP verification)
- Client management (CRUD)
- Quote management (CRUD, PDF generation, sharing)
- Invoice management (CRUD, PDF generation, payment tracking)
- Work Library (predefined items catalog - 67+ BTP items)
- Dashboard with financial stats
- Settings (company info, legal, document appearance)
- CSV export for clients/quotes/invoices
- Automatic payment reminders (background scheduler)
- Share links for quotes/invoices
- Trial/subscription system (limits on free plan)

## Completed Fixes (March 15, 2026 - Session 2)
1. **Trial Banner restored:** Fixed field mapping between trialService and TrialBanner component, removed super_admin exclusion. Reset user to trial mode with 7 days and 9 quote/invoice limits.
2. **10 BTP Categories seeded:** Added 7 missing categories (Chauffage, Menuiserie, Peinture, Plomberie, Rénovation, Réseaux, Électricité) with 180 new items. Renamed existing categories (Carrelage → Carrelage & Sols, Plâtrerie / Isolation → Plâtrerie & Isolation). Total: 247 items across 10 categories.
3. **3 Kits created:** Installation cuisine, Rénovation salle de bain, Rénovation électrique complète.
4. **Category field mapping fixed:** getDynamicCategoriesWithItems now maps description→name and default_price→smart_price for ServiceItemSelector.
5. **Kit expansion fixed:** getKitV3 now computes expanded_items with totals from raw kit items JSON.
1. **RLS Super Admin bypass:** Created `is_super_admin()` function, updated 62 RLS policies
2. **CRUD Operations:** Added `gen_random_uuid()::text` defaults to clients/quotes/invoices id columns
3. **Counters upsert:** Added `onConflict: 'user_id,counter_type,year'` to quote/invoice number generation
4. **Work Library mapping:** Fixed field mapping (name↔description, unit_price↔default_price) in api.js proxy
5. **Email sender:** Fixed to read SENDER_EMAIL from environment variable

## Known Limitations
- **Email:** RESEND_API_KEY is a test placeholder (`re_123_test`). User needs to provide a real Resend key for production email sending.
- **Stripe:** Integration exists in codebase but not actively implemented
- **AI PDF Analysis:** Not yet implemented

## Upcoming Tasks (P1)
- Implement recurring invoices
- Integrate Stripe for payments/subscriptions
- Set up real Resend API key for production emails

## Future Tasks (P2)
- AI PDF analysis with Gemini
- Deeper Work Library integration into quote creation
- Multi-user company accounts
