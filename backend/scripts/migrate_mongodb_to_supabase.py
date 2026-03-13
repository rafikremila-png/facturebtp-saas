#!/usr/bin/env python3
"""
Script de migration des données MongoDB vers Supabase PostgreSQL
Exécutez ce script depuis le serveur qui a accès à MongoDB

Usage:
    python migrate_mongodb_to_supabase.py
"""

import os
import sys
from datetime import datetime
import json

# Configuration
MONGO_URL = os.environ.get('MONGO_URL')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

def check_config():
    """Vérifier que toutes les variables sont configurées"""
    missing = []
    if not MONGO_URL:
        missing.append('MONGO_URL')
    if not SUPABASE_URL:
        missing.append('SUPABASE_URL')
    if not SUPABASE_SERVICE_KEY:
        missing.append('SUPABASE_SERVICE_KEY')
    
    if missing:
        print(f"❌ Variables d'environnement manquantes: {', '.join(missing)}")
        print("\nConfigurez-les avec:")
        print("  export MONGO_URL='mongodb://...'")
        print("  export SUPABASE_URL='https://xxx.supabase.co'")
        print("  export SUPABASE_SERVICE_KEY='eyJhbG...'")
        sys.exit(1)

def main():
    check_config()
    
    # Import après vérification
    from pymongo import MongoClient
    from supabase import create_client
    
    # Connexions
    print("🔌 Connexion à MongoDB...")
    mongo_client = MongoClient(MONGO_URL)
    mongo_db = mongo_client['btp_invoice']
    
    print("🔌 Connexion à Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Stats
    stats = {
        'clients': {'total': 0, 'migrated': 0, 'errors': 0},
        'quotes': {'total': 0, 'migrated': 0, 'errors': 0},
        'invoices': {'total': 0, 'migrated': 0, 'errors': 0},
        'settings': {'total': 0, 'migrated': 0, 'errors': 0}
    }
    
    # ============== MIGRATION DES CLIENTS ==============
    print("\n📦 Migration des clients...")
    clients = list(mongo_db.clients.find())
    stats['clients']['total'] = len(clients)
    
    for client in clients:
        try:
            # Mapper les champs MongoDB vers PostgreSQL
            pg_client = {
                'user_id': client.get('owner_id'),
                'company_name': client.get('company_name') or client.get('name', ''),
                'contact_name': client.get('contact_name') or client.get('contact', ''),
                'email': client.get('email'),
                'phone': client.get('phone'),
                'address': client.get('address'),
                'city': client.get('city'),
                'postal_code': client.get('postal_code') or client.get('zip_code'),
                'country': client.get('country', 'France'),
                'siret': client.get('siret'),
                'tva_number': client.get('tva_number') or client.get('vat_number'),
                'notes': client.get('notes'),
            }
            
            # Supprimer les valeurs None
            pg_client = {k: v for k, v in pg_client.items() if v is not None}
            
            # Ajouter l'ID MongoDB comme référence
            if client.get('id'):
                pg_client['id'] = client['id']
            
            result = supabase.from_('clients').upsert(pg_client).execute()
            stats['clients']['migrated'] += 1
            print(f"  ✅ Client: {pg_client.get('company_name', pg_client.get('contact_name', 'N/A'))}")
            
        except Exception as e:
            stats['clients']['errors'] += 1
            print(f"  ❌ Erreur client: {e}")
    
    # ============== MIGRATION DES DEVIS ==============
    print("\n📄 Migration des devis...")
    quotes = list(mongo_db.quotes.find())
    stats['quotes']['total'] = len(quotes)
    
    for quote in quotes:
        try:
            # Mapper les champs
            pg_quote = {
                'user_id': quote.get('owner_id'),
                'client_id': quote.get('client_id'),
                'quote_number': quote.get('quote_number') or quote.get('number'),
                'client_name': quote.get('client_name'),
                'client_email': quote.get('client_email'),
                'client_address': quote.get('client_address'),
                'items': json.dumps(quote.get('items', [])) if isinstance(quote.get('items'), list) else quote.get('items', '[]'),
                'total_ht': float(quote.get('total_ht', 0)),
                'total_tva': float(quote.get('total_tva', 0)),
                'total_ttc': float(quote.get('total_ttc', 0)),
                'status': quote.get('status', 'draft'),
                'validity_days': quote.get('validity_days', 30),
                'notes': quote.get('notes'),
                'share_token': quote.get('share_token'),
            }
            
            # Gérer les dates
            if quote.get('signed_at'):
                pg_quote['signed_at'] = quote['signed_at'].isoformat() if hasattr(quote['signed_at'], 'isoformat') else str(quote['signed_at'])
            
            # Supprimer les valeurs None
            pg_quote = {k: v for k, v in pg_quote.items() if v is not None}
            
            if quote.get('id'):
                pg_quote['id'] = quote['id']
            
            result = supabase.from_('quotes').upsert(pg_quote).execute()
            stats['quotes']['migrated'] += 1
            print(f"  ✅ Devis: {pg_quote.get('quote_number', 'N/A')}")
            
        except Exception as e:
            stats['quotes']['errors'] += 1
            print(f"  ❌ Erreur devis: {e}")
    
    # ============== MIGRATION DES FACTURES ==============
    print("\n🧾 Migration des factures...")
    invoices = list(mongo_db.invoices.find())
    stats['invoices']['total'] = len(invoices)
    
    for invoice in invoices:
        try:
            # Mapper le statut de paiement
            payment_status_map = {
                'impaye': 'unpaid',
                'paye': 'paid',
                'partiel': 'partial',
                'unpaid': 'unpaid',
                'paid': 'paid',
                'partial': 'partial'
            }
            
            pg_invoice = {
                'user_id': invoice.get('owner_id'),
                'client_id': invoice.get('client_id'),
                'quote_id': invoice.get('quote_id'),
                'invoice_number': invoice.get('invoice_number') or invoice.get('number'),
                'client_name': invoice.get('client_name'),
                'client_email': invoice.get('client_email'),
                'client_address': invoice.get('client_address'),
                'items': json.dumps(invoice.get('items', [])) if isinstance(invoice.get('items'), list) else invoice.get('items', '[]'),
                'total_ht': float(invoice.get('total_ht', 0)),
                'total_tva': float(invoice.get('total_tva', 0)),
                'total_ttc': float(invoice.get('total_ttc', 0)),
                'payment_status': payment_status_map.get(invoice.get('payment_status', 'unpaid'), 'unpaid'),
                'paid_amount': float(invoice.get('paid_amount', 0)),
                'notes': invoice.get('notes'),
                'share_token': invoice.get('share_token'),
            }
            
            # Gérer les dates
            if invoice.get('paid_at'):
                pg_invoice['paid_at'] = invoice['paid_at'].isoformat() if hasattr(invoice['paid_at'], 'isoformat') else str(invoice['paid_at'])
            if invoice.get('due_date'):
                pg_invoice['due_date'] = invoice['due_date'].isoformat() if hasattr(invoice['due_date'], 'isoformat') else str(invoice['due_date'])
            
            # Supprimer les valeurs None
            pg_invoice = {k: v for k, v in pg_invoice.items() if v is not None}
            
            if invoice.get('id'):
                pg_invoice['id'] = invoice['id']
            
            result = supabase.from_('invoices').upsert(pg_invoice).execute()
            stats['invoices']['migrated'] += 1
            print(f"  ✅ Facture: {pg_invoice.get('invoice_number', 'N/A')}")
            
        except Exception as e:
            stats['invoices']['errors'] += 1
            print(f"  ❌ Erreur facture: {e}")
    
    # ============== MIGRATION DES PARAMÈTRES ==============
    print("\n⚙️ Migration des paramètres...")
    settings_list = list(mongo_db.settings.find())
    stats['settings']['total'] = len(settings_list)
    
    for setting in settings_list:
        try:
            pg_setting = {
                'user_id': setting.get('user_id') or setting.get('owner_id'),
                'company_name': setting.get('company_name'),
                'company_address': setting.get('company_address') or setting.get('address'),
                'company_phone': setting.get('company_phone') or setting.get('phone'),
                'company_email': setting.get('company_email') or setting.get('email'),
                'company_siret': setting.get('company_siret') or setting.get('siret'),
                'company_tva': setting.get('company_tva') or setting.get('tva_number'),
                'company_logo_url': setting.get('company_logo_url') or setting.get('logo_url'),
                'bank_name': setting.get('bank_name'),
                'bank_iban': setting.get('bank_iban') or setting.get('iban'),
                'bank_bic': setting.get('bank_bic') or setting.get('bic'),
                'default_vat_rate': float(setting.get('default_vat_rate', 20)),
                'default_payment_terms': int(setting.get('default_payment_terms', 30)),
                'quote_prefix': setting.get('quote_prefix', 'DEV'),
                'invoice_prefix': setting.get('invoice_prefix', 'FAC'),
                'legal_mentions': setting.get('legal_mentions'),
            }
            
            # Supprimer les valeurs None
            pg_setting = {k: v for k, v in pg_setting.items() if v is not None}
            
            if pg_setting.get('user_id'):
                result = supabase.from_('settings').upsert(pg_setting).execute()
                stats['settings']['migrated'] += 1
                print(f"  ✅ Paramètres pour: {pg_setting.get('company_name', 'N/A')}")
            
        except Exception as e:
            stats['settings']['errors'] += 1
            print(f"  ❌ Erreur paramètres: {e}")
    
    # ============== RÉSUMÉ ==============
    print("\n" + "="*50)
    print("📊 RÉSUMÉ DE LA MIGRATION")
    print("="*50)
    
    for table, data in stats.items():
        status = "✅" if data['errors'] == 0 else "⚠️"
        print(f"{status} {table.upper()}: {data['migrated']}/{data['total']} migrés ({data['errors']} erreurs)")
    
    total_migrated = sum(d['migrated'] for d in stats.values())
    total_errors = sum(d['errors'] for d in stats.values())
    total_items = sum(d['total'] for d in stats.values())
    
    print("-"*50)
    print(f"TOTAL: {total_migrated}/{total_items} éléments migrés")
    if total_errors > 0:
        print(f"⚠️  {total_errors} erreurs à vérifier")
    else:
        print("🎉 Migration terminée sans erreurs!")
    
    # Fermer connexions
    mongo_client.close()

if __name__ == '__main__':
    main()
