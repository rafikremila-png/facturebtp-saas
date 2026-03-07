# FactureBTP SaaS Architecture

## Overview

FactureBTP is a cloud SaaS platform designed for construction companies to manage:

* quotes
* invoices
* projects (construction sites)
* payments
* accounting exports
* financial dashboards

The system must support multi-company usage with strong data isolation and secure authentication.

---

# System Architecture

The platform follows a modern SaaS architecture.

User
↓
Cloudflare (DNS + Security)
↓
Vercel (Application Hosting)
↓
SaaS Application
↓
Supabase Backend

Supabase services:

* Authentication
* PostgreSQL Database
* File Storage

Development pipeline:

Emergent → GitHub → Staging → Production

---

# Technology Stack

Frontend / Application

* Next.js
* React
* TypeScript

Backend

* API routes inside the application
* Supabase client libraries

Infrastructure

* Vercel for deployment
* Supabase for backend services
* Cloudflare for DNS and security
* GitHub for version control

Payments

* Stripe

Emails

* SMTP provider or transactional email service

---

# Development Workflow

Emergent is responsible for **development only**.

Emergent must not deploy directly to production.

All code must be committed through GitHub.

Branch strategy:

main → production
dev → staging
ai-dev → AI generated development

Workflow:

1. Emergent generates code in ai-dev branch
2. Features are tested in dev environment
3. Validated code is merged into main
4. Production deploy happens from main branch

---

# Environment Structure

Production

[www.facturebtp.fr](http://www.facturebtp.fr)

Staging

staging.facturebtp.fr

Development

dev.facturebtp.fr

---

# Multi-Tenant Architecture

The application supports multiple companies.

Every business table must include:

user_id

Example tables:

* clients
* invoices
* quotes
* projects
* payments

All database queries must filter by user_id.

Example:

SELECT * FROM invoices WHERE user_id = auth.uid()

Supabase Row Level Security must always be enabled.

---

# Core Modules

Main modules include:

Quotes
Invoice management
Project management
Electronic quote signature
Online invoice payments
Automatic invoice reminders
Accounting export
Financial dashboard
Client portal

---

# Security

The platform must enforce:

Supabase Row Level Security
secure authentication
API validation
environment variables for secrets
no secrets exposed in frontend

---

# AI Development Rules

Emergent must follow these rules:

* Always create modular code
* Avoid monolithic files
* Use reusable components
* Maintain a clean folder structure
* Ensure maintainability and scalability

Before implementing a feature:

1. Analyze architecture impact
2. Follow the existing project structure
3. Ensure compatibility with Supabase backend

---

# Final Objective

Build a stable and scalable SaaS platform for construction companies capable of supporting thousands of users.

Focus on:

* maintainability
* performance
* security
* clean architecture
