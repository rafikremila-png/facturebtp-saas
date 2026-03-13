# BTP Facture - PRD (Product Requirements Document)

## Problème Initial
Application de gestion de devis et factures pour les professionnels du BTP (Bâtiment et Travaux Publics).

## Architecture (ATTEINTE)
```
Vercel (React frontend) + Supabase (Auth + PostgreSQL + Storage)
```
- Pas de backend serveur - toutes les opérations passent directement par Supabase
- Auth: Supabase Auth
- Base de données: Supabase PostgreSQL avec RLS (Row Level Security)
- Frontend: React avec Shadcn UI
- PDF: Génération côté client avec jsPDF
- CSV: Export côté client

## Utilisateurs
- **Super Admin**: rafik.remila@gmail.com
- **Admin système**: admin@btpfacture.com
- 52 comptes de test supprimés le 13 mars 2026

## Fonctionnalités Implémentées

### Core (100% Supabase)
- Tableau de bord avec statistiques
- CRUD Clients (17 clients)
- CRUD Devis (11 devis)
- CRUD Factures (21 factures)
- Paramètres entreprise
- Bibliothèque d'ouvrages (67 articles prédéfinis)
- Page Finances avec rapports financiers
- Gestion des abonnements (page Abonnement)
- Navigation complète avec sidebar
- Authentification Supabase Auth
- **Génération PDF** (jsPDF côté client) - devis et factures
- **Export CSV** - clients, devis, factures

### Stubs (Nécessitent Edge Functions ou service externe)
- Envoi d'emails
- Assistant IA (Gemini)
- Paiement Stripe

## Fichiers Clés
- `/app/frontend/src/lib/api.js` - Couche API (wraps supabaseService)
- `/app/frontend/src/lib/supabaseService.js` - Requêtes directes Supabase
- `/app/frontend/src/lib/pdfGenerator.js` - Génération PDF jsPDF
- `/app/frontend/src/lib/csvExport.js` - Export CSV côté client
- `/app/frontend/src/context/AuthContext.js` - Auth Supabase
- `/app/frontend/src/supabaseClient.js` - Client Supabase

## Historique des Migrations
- 13 Mars 2026: Migration complète MongoDB → Supabase (113/116 records)
- 13 Mars 2026: Frontend basculé en mode Supabase-only
- 13 Mars 2026: Backend FastAPI décommissionné
- 13 Mars 2026: Génération PDF côté client (jsPDF) ajoutée
- 13 Mars 2026: Export CSV côté client ajouté
- 13 Mars 2026: 52 comptes de test supprimés

## Backlog (P0-P2)
- **P1**: Nettoyage comptes auth.users Supabase (les 52 comptes de test existent encore dans auth.users)
- **P2**: Factures récurrentes
- **P2**: Analyse PDF avec Gemini IA
- **P2**: Bibliothèque de travaux connectée aux devis
- **P2**: Système d'email (vérification et rappels)
- **P2**: Intégration Stripe pour abonnements payants
