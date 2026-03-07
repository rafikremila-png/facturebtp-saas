# AI Development Rules

This file defines how the AI developer (Emergent) must generate code for this project.

The goal is to ensure the platform remains stable, scalable, and maintainable.

---

# Development Responsibility

Emergent is responsible for:

* feature implementation
* bug fixes
* code refactoring
* test creation

Emergent must NOT deploy directly to production.

---

# Git Workflow

Branches:

main → production
dev → staging
ai-dev → AI generated development

Workflow:

Emergent creates code in ai-dev

ai-dev → merged into dev after tests

dev → merged into main for production release

---

# Code Standards

All generated code must follow these rules:

• modular architecture
• reusable components
• small files
• TypeScript when possible
• clean naming conventions

Avoid:

• monolithic files
• duplicated logic
• hardcoded secrets

---

# Database Rules

All business tables must include:

user_id

Example tables:

clients
projects
quotes
invoices
payments

All queries must filter by user_id.

Example:

SELECT * FROM invoices WHERE user_id = auth.uid()

---

# Security Rules

Never expose:

• Supabase service role key
• API secrets
• private environment variables

Always use environment variables.

---

# Feature Development Process

When creating a new feature:

1 Analyze architecture impact
2 Create database schema changes if required
3 Implement backend logic
4 Implement frontend UI
5 Add basic tests

---

# Final Goal

Build a stable SaaS platform for construction companies capable of scaling to thousands of users.
