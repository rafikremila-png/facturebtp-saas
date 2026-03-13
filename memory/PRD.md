# BTP Facture - PRD (Product Requirements Document)

## Problème Initial
Application de gestion de devis et factures pour les professionnels du BTP.

## Architecture
```
Vercel (React frontend) + Supabase (Auth + PostgreSQL + Storage)
```

## Utilisateurs
- **Super Admin**: rafik.remila@gmail.com
- **Admin**: admin@btpfacture.com

## Fonctionnalités Implémentées

### Authentification
- Login email/mot de passe (Supabase Auth)
- Inscription avec vérification OTP 6 chiffres par email
- Formulaire OTP avec auto-focus, paste, renvoi de code
- Gestion d'erreurs (email invalide, rate limit, etc.)

### Core (100% Supabase)
- Tableau de bord avec statistiques
- CRUD Clients, Devis, Factures
- Paramètres entreprise
- Bibliothèque d'ouvrages (67 articles)
- Page Finances avec rapports
- Gestion abonnements

### Documents
- Génération PDF (jsPDF côté client)
- Export CSV (clients, devis, factures)

### Stubs
- Envoi d'emails, IA Gemini, Stripe

## Fichiers Clés
- `/app/frontend/src/pages/LoginPage.jsx` - Login + inscription + OTP
- `/app/frontend/src/context/AuthContext.js` - Auth (login, register, verifyOtp, resendVerification)
- `/app/frontend/src/lib/api.js` - Couche API Supabase
- `/app/frontend/src/lib/supabaseService.js` - Requêtes Supabase
- `/app/frontend/src/lib/pdfGenerator.js` - PDF jsPDF
- `/app/frontend/src/lib/csvExport.js` - Export CSV

## Historique
- 13 Mars 2026: Migration MongoDB → Supabase
- 13 Mars 2026: PDF + CSV + nettoyage comptes
- 13 Mars 2026: Système OTP remplace confirmation par lien

## Backlog
- **P1**: Factures récurrentes
- **P1**: Système d'email (notifications, rappels)
- **P2**: Intégration Stripe abonnements
- **P2**: Analyse PDF avec Gemini IA
- **P2**: Bibliothèque travaux → formulaire devis

## Note importante
Pour que le code OTP à 6 chiffres s'affiche dans l'email de confirmation Supabase, vérifiez que le template email dans Supabase Dashboard (Authentication > Email Templates > Confirm signup) inclut `{{ .Token }}`.
