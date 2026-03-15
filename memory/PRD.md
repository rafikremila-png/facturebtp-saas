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

## Completed Fixes (March 2026)
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
