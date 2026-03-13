# 🚀 Guide de Migration vers Supabase - FactureBTP

## Étape 1 : Exécuter les migrations SQL

### Option A : Via Supabase Dashboard (Recommandé)

1. Allez sur [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Sélectionnez votre projet
3. Cliquez sur **SQL Editor** dans le menu de gauche
4. Copiez le contenu du fichier `/app/backend/database/migrations/002_complete_schema.sql`
5. Collez-le dans l'éditeur SQL
6. Cliquez sur **Run**

### Option B : Via Supabase CLI

```bash
# Installer Supabase CLI
npm install -g supabase

# Se connecter
supabase login

# Exécuter la migration
supabase db push --db-url "postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres"
```

---

## Étape 2 : Configurer les Variables d'Environnement Vercel

Allez dans votre projet Vercel → Settings → Environment Variables

Ajoutez ces variables :

```
REACT_APP_SUPABASE_URL=https://[VOTRE-PROJECT-ID].supabase.co
REACT_APP_SUPABASE_ANON_KEY=[VOTRE-CLE-ANON-PUBLIQUE]
```

**IMPORTANT** : Ne PAS ajouter `REACT_APP_BACKEND_URL` - cela forcera le mode Supabase direct.

---

## Étape 3 : Migrer les Données MongoDB vers PostgreSQL

### Script de Migration (à exécuter localement)

```python
import os
from pymongo import MongoClient
from supabase import create_client

# Connexion MongoDB
mongo_client = MongoClient(os.getenv('MONGO_URL'))
mongo_db = mongo_client['btp_invoice']

# Connexion Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

# Migrer les clients
print("Migration des clients...")
clients = list(mongo_db.clients.find())
for client in clients:
    supabase.from_('clients').upsert({
        'id': client.get('id'),
        'user_id': client.get('owner_id'),
        'company_name': client.get('company_name'),
        'contact_name': client.get('contact_name'),
        'email': client.get('email'),
        'phone': client.get('phone'),
        'address': client.get('address'),
        'city': client.get('city'),
        'postal_code': client.get('postal_code'),
        'siret': client.get('siret'),
        'tva_number': client.get('tva_number'),
    }).execute()

# Migrer les devis
print("Migration des devis...")
quotes = list(mongo_db.quotes.find())
for quote in quotes:
    supabase.from_('quotes').upsert({
        'id': quote.get('id'),
        'user_id': quote.get('owner_id'),
        'client_id': quote.get('client_id'),
        'quote_number': quote.get('quote_number'),
        'client_name': quote.get('client_name'),
        'client_email': quote.get('client_email'),
        'items': quote.get('items', []),
        'total_ht': quote.get('total_ht', 0),
        'total_tva': quote.get('total_tva', 0),
        'total_ttc': quote.get('total_ttc', 0),
        'status': quote.get('status', 'draft'),
        'notes': quote.get('notes'),
    }).execute()

# Migrer les factures
print("Migration des factures...")
invoices = list(mongo_db.invoices.find())
for invoice in invoices:
    supabase.from_('invoices').upsert({
        'id': invoice.get('id'),
        'user_id': invoice.get('owner_id'),
        'client_id': invoice.get('client_id'),
        'invoice_number': invoice.get('invoice_number'),
        'client_name': invoice.get('client_name'),
        'items': invoice.get('items', []),
        'total_ht': invoice.get('total_ht', 0),
        'total_tva': invoice.get('total_tva', 0),
        'total_ttc': invoice.get('total_ttc', 0),
        'payment_status': invoice.get('payment_status', 'unpaid'),
        'paid_amount': invoice.get('paid_amount', 0),
    }).execute()

print("Migration terminée!")
```

---

## Étape 4 : Redéployer sur Vercel

```bash
# Dans le dossier frontend
vercel --prod
```

Ou utilisez le bouton "Deploy" dans Vercel Dashboard.

---

## Architecture Finale

```
┌──────────────────────┐
│   facturebtp.fr      │
│   (Vercel Frontend)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      Supabase        │
├──────────────────────┤
│ • Auth (JWT)         │
│ • PostgreSQL (Data)  │
│ • Storage (Logos)    │
│ • RLS (Security)     │
└──────────────────────┘
```

**Avantages :**
- ✅ Un seul backend
- ✅ Pas de serveur à gérer
- ✅ Scaling automatique
- ✅ Sécurité RLS intégrée
- ✅ Coût réduit

---

## Vérification Post-Migration

1. **Tester l'authentification** : Login/Logout
2. **Tester les clients** : CRUD complet
3. **Tester les devis** : Création, conversion en facture
4. **Tester les factures** : Création, marquage payé
5. **Tester les limites trial** : Vérifier les compteurs

---

## Support

En cas de problème :
- Vérifiez les logs Supabase Dashboard → Logs
- Vérifiez les erreurs console du navigateur (F12)
- Vérifiez les politiques RLS dans Supabase → Authentication → Policies
