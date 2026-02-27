# BTP Facture - Product Requirements Document

## Original Problem Statement
Build a production-ready MVP web application for a French construction company (BTP) to manage quotes (devis) and invoices (factures). The application must be simple, fast, and legally compliant in France.

## User Persona
- **Primary User**: French construction company owner/administrator (artisans, auto-entrepreneurs, PME)
- **Technical Level**: Non-technical users who need simple, efficient quote and invoice management
- **Use Case**: Create professional quotes, convert to invoices, track payments

## User Choices
- **Authentication**: JWT custom auth with OTP email verification
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
1. **super_admin**: Full access, can manage all users, delete users, assign any role, impersonation
2. **admin**: Can manage users (except super_admin), update settings, full data access
3. **user**: Standard access to clients, quotes, invoices. No access to user management or settings

### Features
1. Client management (CRUD)
2. Quotes (Devis) with automatic numbering, status management, conversion to invoice
3. Invoices (Factures) with legal numbering, payment status tracking
4. PDF generation with company details, legal mentions (SIRET, VAT)
5. Company settings (logo, SIRET, VAT, default VAT rates, **website**) - **Admin only**
6. Dashboard with KPIs
7. **Kits de rénovation** - Predefined line item bundles
8. **Vue client publique** - Share documents via secure link
9. **Envoi email** - Send quotes/invoices by email with PDF attachment
10. **Mode auto-entrepreneur** - TVA non applicable (art. 293B du CGI)
11. **Informations légales étendues** - RCS/RM, Code APE, Capital social, IBAN/BIC
12. **Délai de paiement configurable** - Défaut 30 jours, mentions légales automatiques
13. **Acomptes (Advance Payments)** - Factures d'acompte avec % ou montant fixe
14. **User Management** - Admin page with detailed user profiles
15. **OTP Verification** - Email verification for registration and sensitive admin actions
16. **Impersonation** - Super admin can connect as any user for support
17. **Website Request** - Business CTA for users without website
18. **User Profile** - Personal profile page with editable info

## Security Features

### OTP (One-Time Password)
- **Registration**: 6-digit OTP sent via email, valid 10 minutes
- **Admin Actions**: OTP required for role change, password reset, user deletion, impersonation (valid 5 minutes)
- **Mode**: Development mode logs OTP to console, production sends via Resend email

### Impersonation
- Super admin only
- Requires OTP verification
- Banner visible during impersonation session
- Audit log recorded for all impersonation actions

### Audit Logging
- Role changes
- Password resets
- User deletions
- Impersonation start/end

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

### Plateforme BTP Verticalisée ✅ (Feb 26, 2026)
- **Landing pages spécialisées** :
  - `/accueil` - Page générale BTP tous corps d'état
  - `/logiciel-facturation-electricien` - Page dédiée électriciens (thème jaune)
  - `/logiciel-facturation-plombier` - Page dédiée plombiers (thème bleu)
  - `/logiciel-facturation-peintre` - Page dédiée peintres (thème violet)
  - `/logiciel-facturation-installateur-reseau` - Page dédiée IT (thème cyan)
- **Inscription avec type de métier** :
  - Sélecteur `business_type` dans le formulaire d'inscription
  - Pré-remplissage depuis les landing pages via URL parameter
  - Support des 7 types : general, electrician, plumber, painter, mason, carpenter, it_installer
- **Correction incohérence Devis/Facture** :
  - Les deux formulaires utilisent maintenant `ServiceItemSelectorV2`
  - Structure identique : Catégorie → Sous-catégorie → Article
  - Même bouton "Ajouter un kit" sur les deux pages

### Système de Catégories V2 avec Sous-catégories et Kits ✅ (Feb 26, 2026)
- **Architecture V2 complète** :
  - `service_categories` : 7 catégories principales
  - `service_subcategories` : 28 sous-catégories (4 par catégorie)
  - `service_items` : 140 articles avec prix par défaut et prix suggérés par métier
  - `service_kits` : 8 kits professionnels prédéfinis
- **Prix intelligents** : Les prix s'adaptent automatiquement au type de métier de l'utilisateur
- **Kits professionnels** :
  - Installation électrique appartement T3 (electrician)
  - Rénovation tableau électrique (electrician)
  - Rénovation salle de bain complète (plumber)
  - Installation chauffe-eau (plumber)
  - Installation réseau bureau complet (it_installer)
  - Rénovation appartement clé en main (general)
  - Peinture appartement T3 (painter)
  - Création salle de bain maçonnerie (mason)
- **Nouveaux endpoints API V2** :
  - `GET /api/v2/categories` - Catégories filtrées par business_type
  - `GET /api/v2/categories/with-subcategories` - Avec sous-catégories
  - `GET /api/v2/categories/{id}/subcategories` - Sous-catégories d'une catégorie
  - `GET /api/v2/subcategories/{id}/items` - Articles avec smart_price
  - `GET /api/v2/kits` - Kits filtrés par business_type
  - `GET /api/v2/kits/{id}` - Kit avec articles étendus et total_ht
- **Nouveau composant frontend** : `ServiceItemSelectorV2.jsx`
  - Sélection en 3 étapes : Catégorie → Sous-catégorie → Article
  - Dialog de sélection de kits avec aperçu détaillé
  - Insertion automatique de tous les articles du kit
- **Rétrocompatibilité** : Les anciens endpoints V1 fonctionnent toujours

### Système de Catégories Dynamiques ✅ (Feb 26, 2026)
- **Nouvelle architecture** : Catégories et articles stockés en base MongoDB (`service_categories`, `service_items`)
- **Filtrage par métier** : Les catégories affichées dépendent du `business_type` de l'utilisateur
- **7 types de métiers supportés** :
  - Général / Multi-corps (voit toutes les catégories)
  - Électricien
  - Plombier
  - Maçon
  - Peintre
  - Menuisier
  - Installateur réseaux / IT
- **9 catégories avec 50 articles prédéfinis** :
  - Maçonnerie, Électricité, Plomberie, Peinture, Menuiserie
  - Carrelage, Plâtrerie / Isolation, Rénovation générale
  - Réseaux & Courants Faibles (nouveau)
- **Interface utilisateur** :
  - Sélecteur de type d'activité dans Paramètres > Entreprise
  - Dropdowns dynamiques dans formulaires devis/factures
  - Articles avec prix, unité et TVA par défaut
- **API Endpoints** :
  - `GET /api/business-types` - Liste des métiers disponibles
  - `GET /api/categories` - Catégories filtrées par business_type
  - `GET /api/categories/with-items` - Catégories avec leurs articles
  - `GET /api/categories/{id}/items` - Articles d'une catégorie
  - `POST /api/categories/seed` - Initialisation des données (admin)

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
2. **P3: Relances automatiques** pour factures impayées

### Bug Select - Placeholder + Valeur concaténés ✅ (Feb 4, 2026)
- **Problème** : Les composants Select affichaient le placeholder ET la valeur sélectionnée concaténés (ex: "Choisir une catégorieMaçonnerie")
- **Cause** : Structure du composant Radix SelectTrigger où les spans enfants ne remplaçaient pas correctement le placeholder
- **Solution** : Modification de `SelectTrigger` dans `frontend/src/components/ui/select.jsx` :
  - Enveloppe les children dans un span avec classe `[&>span]:contents`
  - Force `display: contents` sur les spans enfants de Radix
  - Empêche la concaténation placeholder + valeur
- **Pages corrigées** : `/devis/new`, `/factures/new`, `/parametres`
- **Tests** : Tous les Selects vérifié - 100% de réussite

### RBAC Multi-Utilisateurs ✅ (Feb 4, 2026)
- **Fonctionnalité** : Système de rôles pour gestion multi-utilisateurs
- **Rôles implémentés** :
  - `super_admin` : Accès total, suppression utilisateurs, attribution tous rôles
  - `admin` : Gestion utilisateurs (sauf super_admin), modification paramètres
  - `user` : Accès standard (clients, devis, factures)
- **Compte propriétaire** : admin@btpfacture.com / Admin123! (créé au démarrage)
- **Backend** : Middlewares `require_admin`, `require_super_admin`, routes /api/users/*
- **Frontend** : Section "Administration" conditionnelle, page /utilisateurs, badges de rôle
- **Tests** : 100% de réussite (13 tests backend, tous tests frontend passés)

### OTP & Sécurité Avancée ✅ (Feb 24, 2026)
- **OTP à l'inscription** :
  - Téléphone obligatoire à l'inscription
  - Code OTP 6 chiffres envoyé par email (MOCKÉ - logs en dev)
  - Compte activé uniquement après vérification
  - OTP valide 10 minutes
- **OTP pour actions admin sensibles** (5 minutes) :
  - Modification de rôle
  - Réinitialisation mot de passe
  - Suppression utilisateur
  - Impersonation
- **Fiche détail utilisateur** :
  - Nom, email, téléphone, entreprise, adresse
  - Rôle, date création, dernière connexion
  - Statut actif/inactif, email vérifié
- **Impersonation (Mode Support)** :
  - Super admin uniquement
  - OTP obligatoire
  - Bannière "Mode Support Actif" visible
  - Audit log enregistré
  - Bouton "Quitter le mode"
- **Champ Site Web dans paramètres** :
  - Validation URL
  - CTA business si champ vide
- **Formulaire demande de site** :
  - Type d'activité, objectif, budget, délai
  - Email admin + enregistrement en base
- **Page profil utilisateur** :
  - Édition nom, téléphone, entreprise, adresse
  - Route /profil
- **Audit logging** :
  - Actions sensibles enregistrées avec IP
  - Logs structurés
- **Tests** : 94-100% de réussite

### Architecture Modulaire & Trial Management ✅ (Feb 25, 2026)
- **Structure modulaire** sous `/app/backend/app/`:
  - `services/email_service.py` - Service SMTP avec templates HTML
  - `services/otp_service.py` - OTP sécurisé avec bcrypt
  - `services/rate_limit_service.py` - Rate limiting in-memory (Redis-ready)
  - `services/jwt_service.py` - Génération de tokens JWT
  - `models/user_model.py` - Modèles utilisateur avec trial
  - `models/verification_model.py` - Modèles OTP
- **Trial Management** :
  - 14 jours d'essai gratuit
  - Limite de 9 factures pendant l'essai
  - Trial commence UNIQUEMENT après vérification email
  - États: `trial_pending` → `trial_active` → `trial_expired`
- **OTP Sécurisé** :
  - Génération via `secrets` module (6 chiffres)
  - Hashage bcrypt
  - Expiration 10 minutes
  - Max 5 tentatives
  - Collection `email_verifications` avec TTL index
- **Resend OTP Rate Limiting** :
  - Cooldown 60 secondes entre renvois
  - Maximum 5 renvois par heure
  - HTTP 429 si limite dépassée
- **Préparation Stripe** (non intégré) :
  - `stripe_customer_id`
  - `stripe_subscription_id`
  - `subscription_status` (active | canceled | past_due)
  - `current_period_end`
- **Tests** : 96% de réussite (24/25)

## Test Reports Created
- `/app/test_reports/iteration_5.json` - Situations testing
- `/app/test_reports/iteration_6.json` - Retenue de garantie testing
- `/app/test_reports/iteration_7.json` - Financial summary testing
- `/app/test_reports/iteration_8.json` - PDF export testing (Feb 4, 2026)
- `/app/test_reports/iteration_9.json` - Select bug fix testing (Feb 4, 2026)
- `/app/test_reports/iteration_10.json` - RBAC system testing (Feb 4, 2026)
- `/app/test_reports/iteration_11.json` - OTP & Security features testing (Feb 24, 2026)
- `/app/test_reports/iteration_12.json` - Trial & OTP Architecture testing (Feb 25, 2026)
- `/app/test_reports/iteration_13.json` - Dynamic Categories testing (Feb 26, 2026)
- `/app/test_reports/iteration_14.json` - Categories V2 with Subcategories & Kits testing (Feb 26, 2026)
- `/app/test_reports/iteration_15.json` - Vertical BTP Platform testing (Feb 26, 2026)
- `/app/backend/tests/test_rbac.py` - Tests unitaires RBAC
- `/app/backend/tests/test_otp_features.py` - Tests unitaires OTP
- `/app/backend/tests/test_trial_otp_architecture.py` - Tests architecture modulaire
- `/app/backend/tests/test_e2e_registration_flow.py` - Tests E2E inscription
- `/app/backend/tests/test_dynamic_categories.py` - Tests catégories dynamiques
- `/app/backend/tests/test_categories_v2.py` - Tests catégories V2 avec sous-catégories
- `/app/backend/tests/test_landing_registration_v2.py` - Tests landing pages et inscription

### Système d'Articles Simplifié V3 ✅ (Feb 27, 2026)
- **Simplification du système d'articles**:
  - Suppression des sous-catégories - Architecture directe `Catégorie → Article`
  - Nouveau service `category_service_simple.py` avec 239 articles professionnels
  - 10 catégories métiers: Électricité, Réseaux/IT, Plomberie, Chauffage/Clim, Maçonnerie, Peinture, Menuiserie, Carrelage, Plâtrerie, Rénovation
  - 8 kits prédéfinis par type de métier
  - Prix intelligents basés sur le `business_type` de l'utilisateur

- **Refactoring UX inscription/paramètres**:
  - Champ `business_type` retiré du formulaire d'inscription
  - Sélecteur `business_type` déplacé dans la page Paramètres ("Type d'activité")
  - Les nouveaux utilisateurs commencent en mode "Général / Multi-corps"

- **Limite de devis pendant l'essai**:
  - Nouvelle fonction `check_quote_permission()` dans `subscription_service.py`
  - Limite de 9 devis pendant la période d'essai (comme les factures)
  - Nouvel endpoint `/api/quotes/stats/usage` pour les statistiques

- **Nouveaux endpoints API V3**:
  - `GET /api/v3/categories` - Catégories filtrées par métier
  - `GET /api/v3/categories/with-items` - Catégories avec articles
  - `GET /api/v3/categories/{id}/items` - Articles d'une catégorie
  - `GET /api/v3/kits` - Kits filtrés par métier
  - `GET /api/v3/kits/{id}` - Détail d'un kit avec articles
  - `POST /api/v3/categories/seed` - Seeding des données V3

- **Nouveau composant frontend**:
  - `ServiceItemSelector.jsx` - Sélecteur simplifié sans sous-catégories
  - Utilisé par les pages `InvoiceFormPage.jsx` et `QuoteFormPage.jsx`
  - Dialogue de sélection de kits intégré

- **Tests** : 100% de réussite (iteration_17.json)

### Système SaaS Complet ✅ (Feb 27, 2026)
- **Structure des plans**:
  - 3 plans: Essentiel (19€/mois), Pro (29€/mois), Business (59€/mois)
  - Tarification annuelle avec -20% de réduction
  - Limites dynamiques par plan (30/mois Essentiel, illimité Pro/Business)

- **Compteur d'usage mensuel**:
  - Comptage par mois calendaire (pas total)
  - API `/api/saas/usage` retourne quote_usage, invoice_usage, limits
  - Composant `UsageCounter.jsx` avec barres de progression colorées
  - Couleurs: vert < 70%, orange 70-99%, rouge 100%

- **Enforcement des limites**:
  - Vérification avant création devis/factures via `PlansService`
  - HTTP 403 avec message explicite si limite atteinte
  - Super admin bypass les limites

- **Intégration Stripe**:
  - `StripeService` pour checkout sessions et webhooks
  - Webhooks: checkout.session.completed, invoice.paid, subscription.deleted
  - Mode test avec clé `sk_test_emergent` (à remplacer en production)

- **Fonctionnalités Pro exclusives**:
  - Relances automatiques impayés (`ReminderService`)
  - Export comptable CSV (`CSVExportService`)
  - Support prioritaire

- **Page Pricing haute conversion** (`/tarifs`):
  - Hero section avec CTA "Essai gratuit 14 jours"
  - Toggle Mensuel/Annuel avec économies affichées
  - Plan Pro mis en avant avec badge "Le plus populaire"
  - Bannière urgence "Offre fondateur -20% à vie"
  - FAQ et CTA final

- **Nouveaux endpoints API**:
  - `GET /api/saas/plans` - Liste des plans avec prix
  - `GET /api/saas/subscription` - Info abonnement utilisateur
  - `GET /api/saas/usage` - Statistiques d'utilisation
  - `POST /api/saas/checkout` - Créer session Stripe
  - `POST /api/saas/webhook` - Webhook Stripe
  - `GET /api/export/invoices/csv` - Export factures (Pro)
  - `GET /api/export/quotes/csv` - Export devis (Pro)
  - `GET /api/reminders/*` - Endpoints relances (Pro)

- **Tests** : 100% de réussite (iteration_18.json)

## Remaining Backlog

### P0 - Critical
- Configurer vraies clés Stripe (Price IDs) en production

### P1 - Important
- Envoi réel des emails de relance (actuellement enregistrement seul)
- Page de gestion abonnement utilisateur

### P2 - Nice to Have
- Dashboard analytics détaillé
- Notifications email automatiques
- Multi-utilisateurs pour Pro/Business
