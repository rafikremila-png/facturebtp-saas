# BTP Facture - PRD

## Architecture
```
Vercel (React) + Supabase (Auth + PostgreSQL) + FastAPI (Email API uniquement)
```

## Utilisateurs
- **Super Admin**: rafik.remila@gmail.com
- **Admin**: admin@btpfacture.com / Admin123!

## Fonctionnalités Implémentées

### Authentification
- Login email/mot de passe (Supabase Auth)
- Inscription avec vérification OTP 6 chiffres
- Gestion d'erreurs complète

### Core (Supabase direct)
- Dashboard, CRUD Clients/Devis/Factures
- Paramètres entreprise, Bibliothèque d'ouvrages
- Finances, Abonnements

### Documents
- PDF (jsPDF côté client), CSV export

### Email (Resend)
- Email de bienvenue à l'inscription
- Code OTP par email
- Envoi de facture au client (avec lien de consultation)
- Rappel de paiement (manuel via bouton "Rappel")
- Rappels automatiques : J+7, J+14, J+30 (scheduler backend)
- Notification de paiement reçu
- Templates HTML professionnels
- **RESEND_API_KEY** : clé de test configurée, à remplacer par vraie clé en production

### Stubs restants
- IA Gemini, Stripe

## Fichiers Clés
- `/app/backend/server.py` - API email (POST /api/email/*)
- `/app/backend/email_service.py` - Service Resend
- `/app/backend/email_templates.py` - Templates HTML
- `/app/frontend/src/lib/api.js` - Couche API
- `/app/frontend/src/pages/InvoiceViewPage.jsx` - Boutons email/rappel

## Historique
- 13 Mars 2026: Migration Supabase-only
- 13 Mars 2026: PDF + CSV + nettoyage comptes + OTP
- 15 Mars 2026: Intégration Resend (6 flux email + rappels auto)

## Backlog
- **P1**: Factures récurrentes
- **P1**: Intégration Stripe abonnements
- **P2**: Analyse PDF avec Gemini IA
- **P2**: Bibliothèque travaux → formulaire devis

## Configuration Production
- `RESEND_API_KEY` : Clé API Resend (production)
- Domaine `facturebtp.fr` doit être vérifié dans Resend Dashboard
- Template email Supabase : ajouter `{{ .Token }}` pour le code OTP
