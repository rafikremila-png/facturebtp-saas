# BTP Facture - PRD (Product Requirements Document)

## Problem Statement
Application de gestion de devis et factures pour les professionnels du BTP (Bâtiment et Travaux Publics).

## Architecture Cible (ATTEINTE)
```
Vercel (React frontend) + Supabase (Auth + PostgreSQL + Storage)
```
- **Pas de backend serveur** - toutes les opérations de données passent directement par Supabase
- **Auth**: Supabase Auth
- **Base de données**: Supabase PostgreSQL avec RLS (Row Level Security)
- **Frontend**: React avec Shadcn UI

## Utilisateurs
- **Super Admin**: rafik.remila@gmail.com (gestion complète)
- **Utilisateur Trial**: test.trial@btpfacture.com (accès limité)
- 53 comptes utilisateurs au total dans la base

## Fonctionnalités Implémentées

### Core (100% Supabase)
- Tableau de bord avec statistiques
- CRUD Clients (17 clients migrés)
- CRUD Devis (11 devis migrés)
- CRUD Factures (21 factures migrées)
- Paramètres entreprise
- Bibliothèque d'ouvrages (67 articles prédéfinis)
- Page Finances avec rapports
- Gestion des abonnements (page Abonnement)
- Navigation complète avec sidebar
- Authentification Supabase Auth

### Stubs (Nécessitent Edge Functions ou service externe)
- Génération PDF
- Envoi d'emails
- Export CSV
- Assistant IA (Gemini)
- Paiement Stripe

## Fichiers Clés
- `/app/frontend/src/lib/api.js` - Couche API (wraps supabaseService.js)
- `/app/frontend/src/lib/supabaseService.js` - Requêtes directes Supabase
- `/app/frontend/src/context/AuthContext.js` - Auth Supabase
- `/app/frontend/src/supabaseClient.js` - Client Supabase
- `/app/backend/server.py` - Stub minimal (health check uniquement)

## Migration Complétée (13 Mars 2026)
- [x] Migration données MongoDB → Supabase PostgreSQL (113/116 records)
- [x] Frontend basculé en mode Supabase-only
- [x] Backend FastAPI décommissionné
- [x] RLS policies appliquées
- [x] Toutes les pages principales fonctionnelles

## Backlog (P0-P2)
- **P0**: Génération PDF (client-side avec jsPDF ou Supabase Edge Function)
- **P1**: Export CSV (client-side)
- **P1**: Nettoyage des 53 comptes de test
- **P2**: Factures récurrentes
- **P2**: Analyse PDF avec Gemini IA
- **P2**: Bibliothèque de travaux connectée aux devis
- **P2**: Système d'email (vérification et rappels)
- **P2**: Intégration Stripe pour abonnements payants
