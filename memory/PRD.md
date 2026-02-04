# BTP Facture - Product Requirements Document

## Original Problem Statement
Build a production-ready MVP web application for a French construction company (BTP) to manage quotes (devis) and invoices (factures). The application must be simple, fast, and legally compliant in France.

## User Persona
- **Primary User**: French construction company owner/administrator (artisans, auto-entrepreneurs, PME)
- **Technical Level**: Non-technical users who need simple, efficient quote and invoice management
- **Use Case**: Create professional quotes, convert to invoices, track payments

## User Choices
- **Authentication**: JWT custom auth (email/password)
- **PDF Generation**: ReportLab
- **Design Theme**: Construction/BTP (orange/industrial tones), sober and professional
- **Language**: French interface
- **Logo**: Placeholder with optional upload

## Core Requirements (Static)

### Scope
- Single company
- Single admin user
- No public signup

### Features
1. Client management (CRUD)
2. Quotes (Devis) with automatic numbering, status management, conversion to invoice
3. Invoices (Factures) with legal numbering, payment status tracking
4. PDF generation with company details, legal mentions (SIRET, VAT)
5. Company settings (logo, SIRET, VAT, default VAT rates)
6. Dashboard with KPIs
7. **Kits de rénovation** - Predefined line item bundles
8. **Vue client publique** - Share documents via secure link
9. **Envoi email** - Send quotes/invoices by email with PDF attachment
10. **Mode auto-entrepreneur** - TVA non applicable (art. 293B du CGI)
11. **Informations légales étendues** - RCS/RM, Code APE, Capital social, IBAN/BIC
12. **Délai de paiement configurable** - Défaut 30 jours, mentions légales automatiques
13. **Acomptes (Advance Payments)** - Factures d'acompte avec % ou montant fixe

## Architecture

### Backend (FastAPI)
- `/app/backend/server.py` - Main API with all endpoints
- MongoDB for data persistence
- JWT authentication
- ReportLab for PDF generation
- Resend for email sending (MOCKED - needs real API key)

### Frontend (React)
- `/app/frontend/src/` - React application
- Shadcn UI components
- Industrial Pro theme (orange/slate colors)
- Barlow Condensed + Manrope fonts

### API Endpoints
- Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`
- Clients: `/api/clients` (CRUD)
- Quotes: `/api/quotes` (CRUD), `/api/quotes/{id}/convert`, `/api/quotes/{id}/pdf`, `/api/quotes/{id}/share`, `/api/quotes/{id}/send-email`
- Invoices: `/api/invoices` (CRUD), `/api/invoices/{id}/pdf`, `/api/invoices/{id}/share`, `/api/invoices/{id}/send-email`
- Settings: `/api/settings`, `/api/settings/logo`
- Dashboard: `/api/dashboard`
- Kits: `/api/kits` (CRUD), `/api/kits/from-quote/{id}`, `/api/kits/reset`
- Public: `/api/public/quote/{token}`, `/api/public/invoice/{token}` (no auth required)

## What's Been Implemented (Feb 2026)

### Backend ✅
- [x] JWT Authentication (register, login, token validation)
- [x] Client CRUD API
- [x] Quote CRUD with line items, automatic numbering (DEV-YYYY-XXXX)
- [x] Quote status management (brouillon, envoyé, accepté, refusé, facturé)
- [x] Quote to Invoice conversion
- [x] Invoice CRUD with payment status (impayé, payé, partiel)
- [x] Invoice automatic numbering (FAC-YYYY-XXXX)
- [x] PDF generation for quotes and invoices
- [x] Company settings with logo upload
- [x] Dashboard statistics
- [x] **Predefined Items System** (NEW)
  - 8 BTP categories: Menuiserie, Plomberie, Électricité, Peinture, Maçonnerie, Carrelage, Plâtrerie/Isolation, Rénovation générale
  - ~50 default items with description, unit, default price
  - CRUD API for custom items management
  - Auto-initialization on first use

### Frontend ✅
- [x] Login/Register page with BTP theme
- [x] Dashboard with KPIs and quick actions
- [x] Client management (list, create, edit, delete)
- [x] Quote management (list, create, view, status change, PDF download)
- [x] Invoice management (list, create, view, payment tracking, PDF download)
- [x] Settings page (company info, logo, VAT rates)
- [x] Dark sidebar navigation
- [x] French interface
- [x] Responsive design
- [x] **Predefined Items Selector** (NEW)
  - Category dropdown in quote/invoice forms
  - Item dropdown with price/unit preview
  - Auto-populate line items on selection
  - Manual entry option preserved
- [x] **Items Management in Settings** (NEW)
  - Add/Edit/Delete custom items
  - Category tabs with item count
  - Reset to defaults option

## Prioritized Backlog

### P0 (Critical) - All Complete ✅
- User authentication
- Client management
- Quote/Invoice creation with calculations
- PDF generation
- Dashboard

### P1 (Important) - Complete ✅
- Quote to invoice conversion
- Payment status tracking
- Company settings
- **Kits de rénovation** (Feb 2026)
- **Vue client publique** (Feb 2026)
- **Envoi email** (Feb 2026 - MOCKED, needs real Resend API key)
- **Mode auto-entrepreneur** (Feb 2026)
- **Informations légales étendues** (Feb 2026)
- **Coordonnées bancaires IBAN/BIC** (Feb 2026)
- **Délai de paiement configurable** (Feb 2026)

### P2 (Nice to Have) - Pending
- Multi-user support with roles (Admin, Commercial, Comptable)
- Attestations TVA réduite (10%/5.5%) - formulaire guidé
- Accounting export
- Online payments

## Out of Scope
- Accounting export (deferred)
- Online payments (deferred)

## Bug Fixes Log (Feb 2026)

### ResizeObserver / removeChild Error - FIXED ✅
- **Problem**: "ResizeObserver loop completed with undelivered notifications" and "removeChild" errors when using dropdown menus
- **Root cause**: Radix UI Select component triggers rapid ResizeObserver callbacks that exceed the browser's rendering frame budget
- **Solution**: Patched the native `ResizeObserver` in `frontend/src/index.js` to use `requestAnimationFrame` for batching observations

## Changelog (Feb 2026)

### Tableau de Bord Financier du Projet ✅ (NEW - Feb 4, 2026)
- **Dashboard complet** accessible depuis la page de détail du devis
- **Double accès** :
  - Admin : Bouton "Récapitulatif financier" avec liens cliquables
  - Client : Onglet "Récapitulatif projet" sur la vue publique (lecture seule)
- **Données affichées** :
  - Montant total du projet (HT, TVA, TTC)
  - Barre de progression des paiements
  - 4 cartes de synthèse : Facturé, Encaissé, Reste à payer, Reste à facturer
  - Détail par catégorie : Acomptes, Situations, Retenue de garantie
  - Historique des factures avec statut de paiement
- **API** :
  - `GET /api/quotes/{id}/financial-summary` (authentifié)
  - `GET /api/public/quote/{token}/financial-summary` (public)
- **But** : Clarté absolue pour l'artisan ET le client

### Retenue de Garantie (Retention Guarantee) ✅ (Feb 4, 2026)
- **Conformité légale** : Loi n°75-1334 du 31 décembre 1975
- **Taux maximum** : 5% du montant TTC (validation automatique)
- **Durée de garantie** : 6, 12 ou 24 mois (défaut: 12 mois)
- **Interface utilisateur** :
  - Bouton "Appliquer" sur les factures sans retenue
  - Modal avec slider (0.5%-5%) et aperçu des calculs
  - Section dédiée sur la page de facture avec :
    - Montant retenu et date de libération
    - Indicateur visuel (retenue active = ambre, libérée = vert)
    - Bouton "Libérer la retenue" quand applicable
- **Calculs automatiques** :
  - Montant de la retenue = TTC × taux
  - Net à payer = TTC - retenue
  - Date de libération basée sur la durée de garantie
- **PDF** : Mention légale automatique + ligne de déduction
- **Paramètres entreprise** : Configuration par défaut (toggle, taux, durée)

### Factures de Situation (Progressive Billing) ✅ (Feb 4, 2026)
- **Mode Global** : Appliquer un % d'avancement identique sur l'ensemble du devis
- **Mode Par Ligne** : Définir un % d'avancement différent pour chaque poste
- **Interface utilisateur** :
  - Bouton "Situation" (vert émeraude) sur la page de détail du devis
  - Modal avec onglets pour choisir le mode (Global / Par ligne)
  - Slider et input numérique pour le pourcentage
  - Boutons rapides (25%, 50%, 75%, 100%)
  - Aperçu des montants calculés en temps réel
- **Section "Situations de travaux"** sur la page de détail :
  - Barre de progression de l'avancement du chantier
  - Liste des situations avec numéro, cumul %, type, montant, statut
  - Total facturé et reste à facturer
  - Bouton "Nouvelle situation" et "Décompte final"
- **Calculs automatiques** :
  - Cumul des % précédents
  - Montants HT/TVA/TTC par situation
  - Reste à facturer
- **Validations** :
  - Le % doit être > cumul précédent
  - Le % ne peut pas dépasser 100%
  - Le devis doit être accepté ou envoyé
- **Génération PDF** : Documents "Situation de travaux" avec tableau % par ligne
- **Décompte final** : Récapitulatif de toutes les situations + solde à payer

### Système d'Acomptes (Advance Payments) ✅
- Création d'acomptes depuis un devis accepté ou envoyé
- **Type d'acompte** : Pourcentage (%) ou Montant fixe (€)
- **Facture d'acompte** : Numéro unique, mention "Facture d'acompte"
- **Progression visuelle** : Barre de progression + liste des acomptes
- **Récapitulatif** : Total facturé, total payé, solde restant
- **Facture de solde** : Déduit automatiquement les acomptes payés
- ✅ Compatible avec le mode auto-entrepreneur (sans TVA)

### Mode Auto-entrepreneur ✅ (Enhanced - Feb 4, 2026)
- Toggle dans Paramètres > Entreprise
- Quand activé : mention légale "TVA non applicable, art. 293B du CGI" sur tous les documents
- **Adaptation automatique complète** :
  - Devis : TVA = 0, items vat_rate = 0
  - Acomptes : TVA = 0, calculs proportionnels HT uniquement
  - Situations : TVA = 0, facturation progressive sans TVA
  - Factures : TVA = 0, items vat_rate = 0
  - Retenue de garantie : Compatible (calculée sur TTC = HT)
- **Interface adaptée** :
  - Masquage automatique des colonnes TVA dans les tableaux
  - Affichage "Total" au lieu de "Total HT / TVA / TTC"
  - Mention légale automatique en pied de totaux
- PDFs adaptés avec mention légale

### Informations légales étendues ✅
- Champs ajoutés : RCS/RM, Code APE/NAF, Capital social
- Coordonnées bancaires : IBAN + BIC/SWIFT
- Affichage sur tous les PDFs conformément aux exigences françaises

### Délai de paiement configurable ✅
- Paramètre par défaut : 30 jours (configurable)
- Date d'échéance calculée automatiquement sur les factures
- Mentions légales automatiques sur les factures :
  - Pénalités de retard (3x taux d'intérêt légal)
  - Indemnité forfaitaire de recouvrement de 40€

### Kits de rénovation ✅
- 3 kits par défaut : Rénovation salle de bain (~3466€), Installation cuisine (~2780€), Rénovation électrique (~3675€)
- Ajout rapide via boutons dans le formulaire de devis
- Modal de sélection de kit complet
- Bouton "Sauvegarder comme kit" pour créer des kits personnalisés
- Gestion des kits dans Paramètres > Kits

### Vue client publique ✅
- Lien sécurisé unique par document (share_token)
- Accès sans authentification via `/client/devis/{token}` ou `/client/facture/{token}`
- Affichage des détails, statut, totaux
- Téléchargement du PDF
- Informations légales de l'entreprise en pied de page

### Envoi email ✅ (MOCKED)
- Bouton "Envoyer par email" sur devis et factures
- Modal avec champ email et message personnalisé
- PDF en pièce jointe
- Lien de consultation en ligne
- **NOTE**: Utilise une clé test Resend (re_123_test). Pour activer l'envoi réel, remplacer par une vraie clé Resend dans backend/.env

## Next Action Items
1. **P1: Attestations TVA réduite (10%/5.5%)** - formulaire guidé avec conditions
2. Configurer une vraie clé API Resend pour l'envoi d'email en production
3. **P2: Multi-utilisateurs** avec rôles (Admin, Commercial, Comptable)
4. **P3: Relances automatiques** pour factures impayées
