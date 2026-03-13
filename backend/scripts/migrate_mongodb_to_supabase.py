#!/usr/bin/env python3
"""
Script de migration MongoDB → Supabase PostgreSQL
Migre les données de test_database vers les tables Supabase existantes.
"""

import os
import sys
import json

# Configuration
MONGO_URL = os.environ.get('MONGO_URL')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

# Default owner for records without owner_id
# This is rafik.remila@gmail.com's Supabase Auth UUID
DEFAULT_OWNER_ID = 'c4b63af1-22a9-4cb0-881e-5ebde48fdcc4'

def load_env():
    """Load env vars from backend/.env if not already set"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    if not os.environ.get(key):
                        os.environ[key] = val

def check_config():
    global MONGO_URL, SUPABASE_URL, SUPABASE_SERVICE_KEY
    load_env()
    MONGO_URL = os.environ.get('MONGO_URL')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

    missing = []
    if not MONGO_URL: missing.append('MONGO_URL')
    if not SUPABASE_URL: missing.append('SUPABASE_URL')
    if not SUPABASE_SERVICE_KEY: missing.append('SUPABASE_SERVICE_KEY')
    if missing:
        print(f"Variables manquantes: {', '.join(missing)}")
        sys.exit(1)


def build_user_mapping(mongo_db, supabase):
    """Build mapping: MongoDB user_id -> Supabase Auth user_id (by email)"""
    mapping = {}

    # Get Supabase Auth users
    auth_users = supabase.auth.admin.list_users()
    auth_by_email = {u.email: u.id for u in auth_users}

    # Get MongoDB users
    mongo_users = list(mongo_db.users.find({}, {'_id': 0, 'id': 1, 'email': 1}))
    for mu in mongo_users:
        mongo_id = mu.get('id')
        email = mu.get('email')
        if mongo_id and email and email in auth_by_email:
            mapping[mongo_id] = auth_by_email[email]

    print(f"  Mapping utilisateurs: {len(mapping)} correspondances trouvees")
    for mongo_id, auth_id in mapping.items():
        print(f"    {mongo_id} -> {auth_id}")

    return mapping


def resolve_user_id(owner_id, user_mapping):
    """Resolve a MongoDB owner_id to a Supabase Auth user_id"""
    if not owner_id:
        return DEFAULT_OWNER_ID
    if owner_id in user_mapping:
        return user_mapping[owner_id]
    # Unknown owner - assign to default
    return DEFAULT_OWNER_ID


def safe_float(val, default=0):
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def safe_str(val):
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)


def migrate_clients(mongo_db, supabase, user_mapping):
    print("\n--- Migration des clients ---")
    clients = list(mongo_db.clients.find({}, {'_id': 0}))
    stats = {'total': len(clients), 'ok': 0, 'err': 0}

    for c in clients:
        try:
            pg = {
                'id': c['id'],
                'user_id': resolve_user_id(c.get('owner_id'), user_mapping),
                'name': c.get('name', ''),
                'email': c.get('email'),
                'phone': c.get('phone'),
                'address': c.get('address'),
                'city': c.get('city'),
                'postal_code': c.get('postal_code'),
                'country': c.get('country', 'France'),
                'company_name': c.get('company_name'),
                'siret': c.get('siret'),
                'contact_name': c.get('contact_name'),
                'notes': c.get('notes'),
                'created_at': safe_str(c.get('created_at')),
                'updated_at': safe_str(c.get('updated_at')),
            }
            pg = {k: v for k, v in pg.items() if v is not None}
            supabase.from_('clients').upsert(pg).execute()
            stats['ok'] += 1
            print(f"  OK: {pg.get('name')}")
        except Exception as e:
            stats['err'] += 1
            print(f"  ERREUR client {c.get('name')}: {e}")

    return stats


def migrate_quotes(mongo_db, supabase, user_mapping):
    print("\n--- Migration des devis ---")
    quotes = list(mongo_db.quotes.find({}, {'_id': 0}))
    stats = {'total': len(quotes), 'ok': 0, 'err': 0}

    for q in quotes:
        try:
            items = q.get('items', [])
            if isinstance(items, list):
                items_json = json.dumps(items)
            else:
                items_json = items

            pg = {
                'id': q['id'],
                'user_id': resolve_user_id(q.get('owner_id'), user_mapping),
                'client_id': q.get('client_id'),
                'quote_number': q.get('quote_number', ''),
                'client_name': q.get('client_name'),
                'status': q.get('status', 'draft'),
                'quote_date': safe_str(q.get('issue_date')),
                'validity_date': safe_str(q.get('validity_date')),
                'items': items_json,
                'total_ht': safe_float(q.get('total_ht')),
                'total_vat': safe_float(q.get('total_vat')),
                'total_ttc': safe_float(q.get('total_ttc')),
                'notes': q.get('notes'),
                'share_token': q.get('share_token'),
                'created_at': safe_str(q.get('created_at')),
            }
            pg = {k: v for k, v in pg.items() if v is not None}
            supabase.from_('quotes').upsert(pg).execute()
            stats['ok'] += 1
            print(f"  OK: {pg.get('quote_number')}")
        except Exception as e:
            stats['err'] += 1
            print(f"  ERREUR devis {q.get('quote_number')}: {e}")

    return stats


def migrate_invoices(mongo_db, supabase, user_mapping):
    print("\n--- Migration des factures ---")
    invoices = list(mongo_db.invoices.find({}, {'_id': 0}))
    stats = {'total': len(invoices), 'ok': 0, 'err': 0}

    for inv in invoices:
        try:
            items = inv.get('items', [])
            if isinstance(items, list):
                items_json = json.dumps(items)
            else:
                items_json = items

            pg = {
                'id': inv['id'],
                'user_id': resolve_user_id(inv.get('owner_id'), user_mapping),
                'client_id': inv.get('client_id'),
                'invoice_number': inv.get('invoice_number', ''),
                'client_name': inv.get('client_name'),
                'invoice_date': safe_str(inv.get('issue_date')),
                'due_date': safe_str(inv.get('payment_due_date')),
                'items': items_json,
                'total_ht': safe_float(inv.get('total_ht')),
                'total_vat': safe_float(inv.get('total_vat')),
                'total_ttc': safe_float(inv.get('total_ttc')),
                'payment_status': inv.get('payment_status', 'unpaid'),
                'paid_amount': safe_float(inv.get('paid_amount')),
                'notes': inv.get('notes'),
                'share_token': inv.get('share_token'),
                'created_at': safe_str(inv.get('created_at')),
            }
            # Map paid_at if payment is marked as paid
            if inv.get('payment_status') in ('paye', 'paid') and inv.get('created_at'):
                pg['paid_at'] = safe_str(inv.get('created_at'))

            pg = {k: v for k, v in pg.items() if v is not None}
            supabase.from_('invoices').upsert(pg).execute()
            stats['ok'] += 1
            print(f"  OK: {pg.get('invoice_number')}")
        except Exception as e:
            stats['err'] += 1
            print(f"  ERREUR facture {inv.get('invoice_number')}: {e}")

    return stats


def migrate_settings(mongo_db, supabase):
    """Migrate company settings to Supabase settings table (UUID user_id)"""
    print("\n--- Migration des parametres ---")
    settings_list = list(mongo_db.settings.find({}, {'_id': 0}))
    stats = {'total': len(settings_list), 'ok': 0, 'err': 0}

    for s in settings_list:
        try:
            pg = {
                'user_id': DEFAULT_OWNER_ID,  # Must be a valid auth.users UUID
                'company_name': s.get('company_name'),
                'company_address': s.get('address'),
                'company_phone': s.get('phone'),
                'company_email': s.get('email'),
                'company_siret': s.get('siret'),
                'company_tva': s.get('tva_number'),
                'bank_name': s.get('bank_name'),
                'bank_iban': s.get('iban') or s.get('bic'),
                'bank_bic': s.get('bic'),
                'legal_mentions': s.get('auto_entrepreneur_mention'),
            }
            # Handle logo - skip base64 data (too large for direct insert)
            # The logo should be uploaded to Supabase Storage separately

            pg = {k: v for k, v in pg.items() if v is not None}
            if pg.get('user_id'):
                supabase.from_('settings').upsert(pg, on_conflict='user_id').execute()
                stats['ok'] += 1
                print(f"  OK: {pg.get('company_name')}")
        except Exception as e:
            stats['err'] += 1
            print(f"  ERREUR settings: {e}")

    return stats


def migrate_predefined_items(mongo_db, supabase):
    """Migrate predefined items (global catalog)"""
    print("\n--- Migration des articles predefinis ---")
    items = list(mongo_db.predefined_items.find({}, {'_id': 0}))
    stats = {'total': len(items), 'ok': 0, 'err': 0}

    for item in items:
        try:
            pg = {
                'id': item['id'],
                'category': item.get('category', ''),
                'description': item.get('description', ''),
                'unit': item.get('unit', 'u'),
                'default_price': safe_float(item.get('default_price')),
                'default_vat_rate': safe_float(item.get('default_vat_rate'), 20.0),
                'is_global': True,  # These are shared catalog items
            }
            pg = {k: v for k, v in pg.items() if v is not None}
            supabase.from_('predefined_items').upsert(pg).execute()
            stats['ok'] += 1
        except Exception as e:
            stats['err'] += 1
            if stats['err'] <= 3:  # Show first 3 errors only
                print(f"  ERREUR item: {e}")

    print(f"  {stats['ok']}/{stats['total']} articles migres")
    return stats


def main():
    check_config()

    from pymongo import MongoClient
    from supabase import create_client

    # Connect to MongoDB - use test_database
    print("Connexion a MongoDB (test_database)...")
    mongo_client = MongoClient(MONGO_URL)
    mongo_db = mongo_client['test_database']

    # Verify connection
    collections = mongo_db.list_collection_names()
    print(f"  Collections trouvees: {len(collections)}")

    # Connect to Supabase
    print("Connexion a Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Build user ID mapping
    print("\nConstruction du mapping utilisateurs...")
    user_mapping = build_user_mapping(mongo_db, supabase)

    # Run migrations
    all_stats = {}
    all_stats['clients'] = migrate_clients(mongo_db, supabase, user_mapping)
    all_stats['quotes'] = migrate_quotes(mongo_db, supabase, user_mapping)
    all_stats['invoices'] = migrate_invoices(mongo_db, supabase, user_mapping)
    all_stats['settings'] = migrate_settings(mongo_db, supabase)
    all_stats['predefined_items'] = migrate_predefined_items(mongo_db, supabase)

    # Summary
    print("\n" + "=" * 50)
    print("RESUME DE LA MIGRATION")
    print("=" * 50)
    total_ok = 0
    total_err = 0
    for table, s in all_stats.items():
        icon = "OK" if s['err'] == 0 else "!!"
        print(f"  [{icon}] {table}: {s['ok']}/{s['total']} migres ({s['err']} erreurs)")
        total_ok += s['ok']
        total_err += s['err']

    print("-" * 50)
    print(f"  TOTAL: {total_ok} migres, {total_err} erreurs")
    if total_err == 0:
        print("  Migration terminee sans erreurs!")
    else:
        print(f"  {total_err} erreurs a verifier")

    mongo_client.close()


if __name__ == '__main__':
    main()
