"""
Data Migration Script: MongoDB to PostgreSQL
Migrates all data from MongoDB to Supabase PostgreSQL
"""
import asyncio
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent / '.env')

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import AsyncSessionLocal, engine
from app.models.models import (
    Base, User, UserSettings, Client, Project, ProjectTask,
    Quote, QuoteSignature, Invoice, Payment, WorkItem,
    RecurringInvoice, InvoiceReminder, OTP, AuditLog
)
from app.core.security import generate_uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "test_database")


async def get_mongodb():
    """Get MongoDB database"""
    client = AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME]


async def migrate_users(mongo_db, pg_session):
    """Migrate users from MongoDB to PostgreSQL"""
    logger.info("Migrating users...")
    
    mongo_users = await mongo_db.users.find({}).to_list(length=10000)
    count = 0
    
    for mu in mongo_users:
        # Check if user already exists
        from sqlalchemy import select
        result = await pg_session.execute(
            select(User).where(User.email == mu.get('email', '').lower())
        )
        if result.scalar_one_or_none():
            logger.info(f"  User {mu.get('email')} already exists, skipping")
            continue
        
        user = User(
            id=mu.get('id', generate_uuid()),
            email=mu.get('email', '').lower(),
            password=mu.get('password', ''),
            name=mu.get('name', 'Unknown'),
            phone=mu.get('phone'),
            role=mu.get('role', 'user'),
            is_active=mu.get('is_active', True),
            email_verified=mu.get('email_verified', False),
            subscription_plan=mu.get('plan', 'free'),
            login_attempts=mu.get('login_attempts', 0),
            created_at=parse_datetime(mu.get('created_at')),
            updated_at=parse_datetime(mu.get('updated_at')) or datetime.now(timezone.utc),
            last_login=parse_datetime(mu.get('last_login'))
        )
        pg_session.add(user)
        
        # Migrate user settings
        mongo_settings = await mongo_db.user_settings.find_one({'user_id': mu.get('id')})
        if mongo_settings:
            settings = UserSettings(
                id=generate_uuid(),
                user_id=user.id,
                company_name=mongo_settings.get('company_name'),
                company_address=mongo_settings.get('address'),
                company_email=mongo_settings.get('email'),
                company_phone=mongo_settings.get('phone'),
                siret=mongo_settings.get('siret'),
                vat_number=mongo_settings.get('vat_number'),
                rcs=mongo_settings.get('rcs_rm'),
                capital=mongo_settings.get('capital_social'),
                iban=mongo_settings.get('iban'),
                bic=mongo_settings.get('bic'),
                logo_base64=mongo_settings.get('logo_base64'),
                default_payment_days=mongo_settings.get('default_payment_delay_days', 30),
                vat_rates=mongo_settings.get('default_vat_rates', [20.0, 10.0, 5.5, 2.1]),
                retention_enabled=mongo_settings.get('default_retenue_garantie_enabled', False),
                default_retention_rate=mongo_settings.get('default_retenue_garantie_rate', 5.0),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            pg_session.add(settings)
        
        count += 1
    
    await pg_session.flush()
    logger.info(f"  Migrated {count} users")
    return count


async def migrate_clients(mongo_db, pg_session):
    """Migrate clients from MongoDB to PostgreSQL"""
    logger.info("Migrating clients...")
    
    mongo_clients = await mongo_db.clients.find({}).to_list(length=50000)
    count = 0
    
    for mc in mongo_clients:
        client = Client(
            id=mc.get('id', generate_uuid()),
            user_id=mc.get('user_id'),
            name=mc.get('name', 'Unknown'),
            email=mc.get('email'),
            phone=mc.get('phone'),
            address=mc.get('address'),
            client_type='company' if mc.get('company_name') else 'individual',
            company_name=mc.get('company_name'),
            notes=mc.get('notes'),
            created_at=parse_datetime(mc.get('created_at')),
            updated_at=parse_datetime(mc.get('updated_at')) or datetime.now(timezone.utc)
        )
        pg_session.add(client)
        count += 1
    
    await pg_session.flush()
    logger.info(f"  Migrated {count} clients")
    return count


async def migrate_quotes(mongo_db, pg_session):
    """Migrate quotes from MongoDB to PostgreSQL"""
    logger.info("Migrating quotes...")
    
    mongo_quotes = await mongo_db.quotes.find({}).to_list(length=50000)
    count = 0
    
    for mq in mongo_quotes:
        # Map old status to new status
        status_map = {
            'brouillon': 'draft',
            'envoye': 'sent',
            'accepte': 'accepted',
            'refuse': 'rejected',
            'facture': 'accepted'
        }
        
        quote = Quote(
            id=mq.get('id', generate_uuid()),
            user_id=mq.get('user_id'),
            client_id=mq.get('client_id'),
            quote_number=mq.get('quote_number', f"DEV-{count:04d}"),
            title=mq.get('title'),
            description=mq.get('notes'),
            status=status_map.get(mq.get('status', 'brouillon'), 'draft'),
            quote_date=parse_datetime(mq.get('issue_date')),
            validity_date=parse_datetime(mq.get('validity_date')),
            items=mq.get('items', []),
            subtotal_ht=mq.get('total_ht', 0),
            total_vat=mq.get('total_vat', 0),
            total_ttc=mq.get('total_ttc', 0),
            notes=mq.get('notes'),
            created_at=parse_datetime(mq.get('created_at')),
            updated_at=parse_datetime(mq.get('updated_at')) or datetime.now(timezone.utc)
        )
        pg_session.add(quote)
        count += 1
    
    await pg_session.flush()
    logger.info(f"  Migrated {count} quotes")
    return count


async def migrate_invoices(mongo_db, pg_session):
    """Migrate invoices from MongoDB to PostgreSQL"""
    logger.info("Migrating invoices...")
    
    mongo_invoices = await mongo_db.invoices.find({}).to_list(length=50000)
    count = 0
    
    for mi in mongo_invoices:
        # Map old status to new status
        status_map = {
            'impaye': 'sent',
            'partiel': 'partial',
            'paye': 'paid'
        }
        
        invoice = Invoice(
            id=mi.get('id', generate_uuid()),
            user_id=mi.get('user_id'),
            client_id=mi.get('client_id'),
            quote_id=mi.get('quote_id'),
            invoice_number=mi.get('invoice_number', f"FAC-{count:04d}"),
            title=mi.get('title'),
            status=status_map.get(mi.get('payment_status', 'impaye'), 'draft'),
            invoice_date=parse_datetime(mi.get('issue_date')),
            due_date=parse_datetime(mi.get('payment_due_date')),
            items=mi.get('items', []),
            subtotal_ht=mi.get('total_ht', 0),
            total_vat=mi.get('total_vat', 0),
            total_ttc=mi.get('total_ttc', 0),
            amount_paid=mi.get('paid_amount', 0),
            amount_due=mi.get('total_ttc', 0) - mi.get('paid_amount', 0),
            invoice_type='situation' if mi.get('is_situation') else 'standard',
            situation_number=mi.get('situation_number'),
            progress_percentage=mi.get('situation_percentage', 100),
            retention_rate=mi.get('retenue_garantie_rate', 0),
            retention_amount=mi.get('retenue_garantie_amount', 0),
            retention_released=mi.get('retenue_garantie_released', False),
            notes=mi.get('notes'),
            created_at=parse_datetime(mi.get('created_at')),
            updated_at=parse_datetime(mi.get('updated_at')) or datetime.now(timezone.utc)
        )
        pg_session.add(invoice)
        count += 1
    
    await pg_session.flush()
    logger.info(f"  Migrated {count} invoices")
    return count


async def migrate_work_items(mongo_db, pg_session):
    """Migrate predefined items/kits to work items"""
    logger.info("Migrating work items...")
    
    mongo_items = await mongo_db.predefined_items.find({}).to_list(length=50000)
    count = 0
    
    for mi in mongo_items:
        work_item = WorkItem(
            id=mi.get('id', generate_uuid()),
            user_id=mi.get('user_id'),
            name=mi.get('description', 'Unknown'),
            description=mi.get('description'),
            category=mi.get('category'),
            unit=mi.get('unit', 'u'),
            unit_price=mi.get('default_price', 0),
            vat_rate=mi.get('default_vat_rate', 20),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        pg_session.add(work_item)
        count += 1
    
    await pg_session.flush()
    logger.info(f"  Migrated {count} work items")
    return count


def parse_datetime(value):
    """Parse datetime from various formats"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # Try ISO format
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            pass
    return datetime.now(timezone.utc)


async def run_migration():
    """Run the complete migration"""
    logger.info("=" * 60)
    logger.info("Starting MongoDB to PostgreSQL migration")
    logger.info("=" * 60)
    
    # Get MongoDB connection
    mongo_db = await get_mongodb()
    
    # Get PostgreSQL session
    async with AsyncSessionLocal() as pg_session:
        try:
            # Migrate in order (respecting foreign keys)
            user_count = await migrate_users(mongo_db, pg_session)
            client_count = await migrate_clients(mongo_db, pg_session)
            quote_count = await migrate_quotes(mongo_db, pg_session)
            invoice_count = await migrate_invoices(mongo_db, pg_session)
            work_item_count = await migrate_work_items(mongo_db, pg_session)
            
            # Commit all changes
            await pg_session.commit()
            
            logger.info("=" * 60)
            logger.info("Migration completed successfully!")
            logger.info(f"  Users: {user_count}")
            logger.info(f"  Clients: {client_count}")
            logger.info(f"  Quotes: {quote_count}")
            logger.info(f"  Invoices: {invoice_count}")
            logger.info(f"  Work Items: {work_item_count}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await pg_session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(run_migration())
