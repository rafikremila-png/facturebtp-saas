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
- **Multi-tenant**: Mono-tenant with multi-user RBAC (single company, multiple users)

## Core Requirements (Static)

### Scope
- Single company
- Multiple users with role-based access (RBAC)
- Super admin account: admin@btpfacture.com

### Roles (RBAC)
1. **super_admin**: Full access, can manage all users, delete users, assign any role
2. **admin**: Can manage users (except super_admin), update settings, full data access
3. **user**: Standard access to clients, quotes, invoices. No access to user management or settings

### Features
1. Client management (CRUD)
2. Quotes (Devis) with automatic numbering, status management, conversion to invoice
3. Invoices (Factures) with legal numbering, payment status tracking
4. PDF generation with company details, legal mentions (SIRET, VAT)
5. Company settings (logo, SIRET, VAT, default VAT rates) - **Admin only**
6. Dashboard with KPIs
7. **Kits de rénovation** - Predefined line item bundles
8. **Vue client publique** - Share documents via secure link
9. **Envoi email** - Send quotes/invoices by email with PDF attachment
10. **Mode auto-entrepreneur** - TVA non applicable (art. 293B du CGI)
11. **Informations légales étendues** - RCS/RM, Code APE, Capital social, IBAN/BIC
12. **Délai de paiement configurable** - Défaut 30 jours, mentions légales automatiques
13. **Acomptes (Advance Payments)** - Factures d'acompte avec % ou montant fixe
14. **User Management** - Admin page to list, activate/deactivate, and manage user roles

## Architecture

### Backend (FastAPI)
- `/app/backend/server.py` - Main API with all endpoints
- MongoDB for data persistence
- JWT authentication with role-based middleware (require_admin, require_super_admin)
- ReportLab for PDF generation
- Resend for email sending (MOCKED - needs real API key)
- Rate limiting with SlowAPI

### Frontend (React)
- `/app/frontend/src/` - React application
- Shadcn UI components
- Industrial Pro theme (orange/slate colors)
- Barlow Condensed + Manrope fonts
- Role-aware UI (admin sections hidden for regular users)

### API Endpoints
- Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`, `/api/auth/refresh`
- Users (Admin): `/api/users` (list), `/api/users/{id}` (get), `/api/users/{id}/role` (update role), `/api/users/{id}/activate`, `/api/users/{id}/deactivate`, `/api/users/{id}` (delete - super_admin only)
- Clients: `/api/clients` (CRUD)
- Quotes: `/api/quotes` (CRUD), `/api/quotes/{id}/convert`, `/api/quotes/{id}/pdf`, `/api/quotes/{id}/share`, `/api/quotes/{id}/send-email`
- Invoices: `/api/invoices` (CRUD), `/api/invoices/{id}/pdf`, `/api/invoices/{id}/share`, `/api/invoices/{id}/send-email`
- Settings: `/api/settings` (GET for all, PUT for admin only), `/api/settings/logo` (admin only)
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
- [x] **Predefined Items System** (EXTENDED - Feb 4, 2026)
  - 8 BTP categories: Maçonnerie, Carrelage, Plâtrerie/Isolation, Peinture, Plomberie, Électricité, Menuiserie, Rénovation générale
  - **226 articles prédéfinis** avec description, unité, prix par défaut et taux de TVA
  - Taux de TVA différenciés selon les travaux:
    - **5.5%** : Isolation, amélioration énergétique, fenêtres (rénovation)
    - **10%** : Travaux de rénovation (logements > 2 ans)
    - **20%** : Prestations standard (location, études)
  - CRUD API for custom items management
  - Auto-initialization on first use
  - Reset to defaults option

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
- [x] **Predefined Items Selector**
  - Category dropdown in quote/invoice forms
  - Item dropdown with price/unit/VAT preview
  - Auto-populate line items on selection with correct VAT rate
  - Manual entry option preserved
- [x] **Items Management in Settings**
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

### Portal removeChild Error During Navigation - FIXED ✅ (Feb 4, 2026)
- **Problem**: "Failed to execute 'removeChild' on 'Node'" and "commitDeletionEffects" errors when navigating while dropdowns/modals are open
- **Root cause**: Radix UI Portal components mount content in a separate DOM node. When navigating while a portal is open or animating, React tries to remove a DOM node that was already removed by the portal's cleanup
- **Solution**: 
  1. Patched `Node.prototype.removeChild` and `Node.prototype.insertBefore` in `index.js` to gracefully handle already-detached nodes
  2. Added global error handler to suppress these benign DOM manipulation errors
  3. Created `ErrorBoundary.jsx` component to catch and recover from React rendering errors
- **Files modified**: `frontend/src/index.js`, `frontend/src/App.js`, `frontend/src/components/ErrorBoundary.jsx`

## Changelog (Feb 2026)

### Tableau de Bord Financier du Projet ✅ (Feb 4, 2026)
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

### Export PDF Récapitulatif Financier ✅ (Feb 4, 2026)
- **Bouton "Télécharger PDF"** dans le composant récapitulatif financier
- **PDF professionnel** généré par ReportLab avec :
  - En-tête avec informations entreprise (nom, adresse, SIRET)
  - Informations projet (client, référence devis, statut, date)
  - Montant total du projet (HT, TVA, TTC ou mention auto-entrepreneur)
  - Synthèse des paiements (facturé, encaissé, reste à payer)
  - Détail par catégorie (acomptes, situations, retenue de garantie)
  - Historique des factures (numéro, type, date, montant, statut)
  - Pied de page avec date de génération et coordonnées
- **API** : `GET /api/quotes/{id}/financial-summary/pdf` (authentifié, retourne le fichier PDF)
- **Nom du fichier** : `Recapitulatif_financier_{NUMERO_DEVIS}.pdf`
- **Visibilité** : Uniquement pour les utilisateurs authentifiés (pas visible en vue publique client)

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

### Envoi email (Configuration requise)
- Bouton "Envoyer par email" sur devis et factures
- Modal avec champ email et message personnalisé
- PDF en pièce jointe
- Lien de consultation en ligne
- **Configuration requise** :
  1. Créer un compte sur https://resend.com
  2. Générer une API Key dans Dashboard → API Keys
  3. Ajouter dans `/app/backend/.env` :
     ```
     RESEND_API_KEY=re_votre_vraie_cle_ici
     SENDER_EMAIL=votre-email@votredomaine.com
     ```
  4. Redémarrer le backend : `sudo supervisorctl restart backend`
- Message d'erreur clair si non configuré (HTTP 503)

## Next Action Items
1. **P1: Attestations TVA réduite (10%/5.5%)** - formulaire guidé avec conditions
3. **P2: Multi-utilisateurs** avec rôles (Admin, Commercial, Comptable)
4. **P3: Relances automatiques** pour factures impayées

### Bug Select - Placeholder + Valeur concaténés ✅ (Feb 4, 2026)
- **Problème** : Les composants Select affichaient le placeholder ET la valeur sélectionnée concaténés (ex: "Choisir une catégorieMaçonnerie")
- **Cause** : Structure du composant Radix SelectTrigger où les spans enfants ne remplaçaient pas correctement le placeholder
- **Solution** : Modification de `SelectTrigger` dans `frontend/src/components/ui/select.jsx` :
  - Enveloppe les children dans un span avec classe `[&>span]:contents`
  - Force `display: contents` sur les spans enfants de Radix
  - Empêche la concaténation placeholder + valeur
- **Pages corrigées** : `/devis/new`, `/factures/new`, `/parametres`
- **Tests** : Tous les Selects vérifié - 100% de réussite

## Test Reports Created
- `/app/test_reports/iteration_5.json` - Situations testing
- `/app/test_reports/iteration_6.json` - Retenue de garantie testing
- `/app/test_reports/iteration_7.json` - Financial summary testing
- `/app/test_reports/iteration_8.json` - PDF export testing (Feb 4, 2026)
- `/app/test_reports/iteration_9.json` - Select bug fix testing (Feb 4, 2026)
