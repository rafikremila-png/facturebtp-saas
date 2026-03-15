"""
BTP Facture - Backend API
Handles email sending and automatic reminders.
All data operations are handled by Supabase directly from the frontend.
"""
import os
import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional

import email_service

# Load .env
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Supabase client for server-side operations
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

_supabase = None

def get_supabase():
    global _supabase
    if _supabase is None:
        from supabase import create_client
        _supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase


# === Auth helper ===
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, "Non authentifié")
    token = authorization.replace('Bearer ', '')
    try:
        sb = get_supabase()
        user_resp = sb.auth.get_user(token)
        return user_resp.user
    except Exception:
        raise HTTPException(401, "Token invalide")


# === Pydantic models ===
class SendInvoiceEmailRequest(BaseModel):
    invoice_id: str
    client_email: EmailStr

class SendReminderRequest(BaseModel):
    invoice_id: str

class SendWelcomeRequest(BaseModel):
    email: EmailStr

class SendOtpRequest(BaseModel):
    email: EmailStr
    code: str


# === Background reminder task ===
async def check_and_send_reminders():
    """Check for overdue invoices and send automatic reminders"""
    try:
        sb = get_supabase()
        now = datetime.now(timezone.utc)

        # Get unpaid invoices with due dates
        res = sb.from_('invoices').select(
            'id, invoice_number, client_name, client_id, total_ttc, due_date, payment_status, user_id, reminder_count, last_reminder_at'
        ).in_('payment_status', ['unpaid', 'impaye', 'en_attente']).not_.is_('due_date', 'null').execute()

        invoices = res.data or []
        sent = 0

        for inv in invoices:
            due_date_str = inv.get('due_date')
            if not due_date_str:
                continue

            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                continue

            days_overdue = (now - due_date).days
            if days_overdue < 7:
                continue

            reminder_count = inv.get('reminder_count') or 0
            last_reminder = inv.get('last_reminder_at')

            # Determine reminder level
            if days_overdue >= 30 and reminder_count < 3:
                level = 3
            elif days_overdue >= 14 and reminder_count < 2:
                level = 2
            elif days_overdue >= 7 and reminder_count < 1:
                level = 1
            else:
                continue

            # Skip if last reminder was sent less than 5 days ago
            if last_reminder:
                try:
                    last_dt = datetime.fromisoformat(last_reminder.replace('Z', '+00:00'))
                    if (now - last_dt).days < 5:
                        continue
                except (ValueError, TypeError):
                    pass

            # Get client email
            client_id = inv.get('client_id')
            client_email = None
            if client_id:
                client_res = sb.from_('clients').select('email').eq('id', client_id).limit(1).execute()
                if client_res.data and client_res.data[0].get('email'):
                    client_email = client_res.data[0]['email']

            if not client_email:
                continue

            # Get company name from settings
            user_id = inv.get('user_id')
            company_name = 'BTP Facture'
            if user_id:
                settings_res = sb.from_('settings').select('company_name').eq('user_id', user_id).limit(1).execute()
                if settings_res.data and settings_res.data[0].get('company_name'):
                    company_name = settings_res.data[0]['company_name']

            # Send reminder
            try:
                due_formatted = due_date.strftime('%d/%m/%Y')
                total = f"{float(inv.get('total_ttc') or 0):,.2f}".replace(',', ' ')

                await email_service.send_reminder(
                    client_email=client_email,
                    client_name=inv.get('client_name', ''),
                    invoice_number=inv.get('invoice_number', ''),
                    total_ttc=total,
                    due_date=due_formatted,
                    company_name=company_name,
                    reminder_level=level,
                )

                # Update reminder tracking
                sb.from_('invoices').update({
                    'reminder_count': level,
                    'last_reminder_at': now.isoformat(),
                }).eq('id', inv['id']).execute()

                sent += 1
                logger.info(f"Reminder level {level} sent for invoice {inv.get('invoice_number')} to {client_email}")
            except Exception as e:
                logger.error(f"Failed to send reminder for {inv.get('invoice_number')}: {e}")

        logger.info(f"Reminder check complete: {sent} reminders sent out of {len(invoices)} unpaid invoices")
    except Exception as e:
        logger.error(f"Reminder check failed: {e}")


async def reminder_scheduler():
    """Run reminder check every 6 hours"""
    while True:
        await asyncio.sleep(6 * 3600)  # 6 hours
        await check_and_send_reminders()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background reminder scheduler
    task = asyncio.create_task(reminder_scheduler())
    logger.info("Automatic reminder scheduler started (every 6 hours)")
    yield
    task.cancel()


# === FastAPI app ===
app = FastAPI(title="BTP Facture - Email API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    configured = bool(os.environ.get('RESEND_API_KEY'))
    return {"status": "ok", "mode": "supabase-only", "email_configured": configured}


# === Email endpoints ===

@app.post("/api/email/welcome")
async def api_send_welcome(req: SendWelcomeRequest):
    try:
        email_id = await email_service.send_welcome(req.email)
        return {"status": "sent", "email_id": email_id}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/email/otp")
async def api_send_otp(req: SendOtpRequest):
    try:
        email_id = await email_service.send_otp(req.email, req.code)
        return {"status": "sent", "email_id": email_id}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/email/invoice")
async def api_send_invoice_email(req: SendInvoiceEmailRequest, authorization: str = Header(None)):
    user = await get_current_user(authorization)

    sb = get_supabase()
    inv_res = sb.from_('invoices').select('*').eq('id', req.invoice_id).single().execute()
    invoice = inv_res.data
    if not invoice:
        raise HTTPException(404, "Facture non trouvée")

    # Get company settings
    company_name = 'BTP Facture'
    settings_res = sb.from_('settings').select('company_name').eq('user_id', user.id).limit(1).execute()
    if settings_res.data and settings_res.data[0].get('company_name'):
        company_name = settings_res.data[0]['company_name']

    # Build invoice link
    share_token = invoice.get('share_token')
    if not share_token:
        import uuid
        share_token = str(uuid.uuid4())
        sb.from_('invoices').update({'share_token': share_token}).eq('id', req.invoice_id).execute()
    invoice_link = f"https://facturebtp.fr/public/invoice/{share_token}"

    # Format values
    total_ttc = f"{float(invoice.get('total_ttc') or 0):,.2f}".replace(',', ' ')
    due_date = '-'
    if invoice.get('due_date'):
        try:
            dt = datetime.fromisoformat(str(invoice['due_date']).replace('Z', '+00:00'))
            due_date = dt.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            pass

    try:
        email_id = await email_service.send_invoice(
            client_email=req.client_email,
            client_name=invoice.get('client_name', ''),
            invoice_number=invoice.get('invoice_number', ''),
            total_ttc=total_ttc,
            due_date=due_date,
            invoice_link=invoice_link,
            company_name=company_name,
        )
        return {"status": "sent", "email_id": email_id}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/email/reminder")
async def api_send_reminder(req: SendReminderRequest, authorization: str = Header(None)):
    user = await get_current_user(authorization)

    sb = get_supabase()
    inv_res = sb.from_('invoices').select('*').eq('id', req.invoice_id).single().execute()
    invoice = inv_res.data
    if not invoice:
        raise HTTPException(404, "Facture non trouvée")

    # Get client email
    client_id = invoice.get('client_id')
    client_email = None
    if client_id:
        client_res = sb.from_('clients').select('email').eq('id', client_id).limit(1).execute()
        if client_res.data and client_res.data[0].get('email'):
            client_email = client_res.data[0]['email']

    if not client_email:
        raise HTTPException(400, "Le client n'a pas d'adresse email")

    company_name = 'BTP Facture'
    settings_res = sb.from_('settings').select('company_name').eq('user_id', user.id).limit(1).execute()
    if settings_res.data and settings_res.data[0].get('company_name'):
        company_name = settings_res.data[0]['company_name']

    total_ttc = f"{float(invoice.get('total_ttc') or 0):,.2f}".replace(',', ' ')
    due_date = '-'
    if invoice.get('due_date'):
        try:
            dt = datetime.fromisoformat(str(invoice['due_date']).replace('Z', '+00:00'))
            due_date = dt.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            pass

    reminder_count = (invoice.get('reminder_count') or 0) + 1

    try:
        email_id = await email_service.send_reminder(
            client_email=client_email,
            client_name=invoice.get('client_name', ''),
            invoice_number=invoice.get('invoice_number', ''),
            total_ttc=total_ttc,
            due_date=due_date,
            company_name=company_name,
            reminder_level=min(reminder_count, 3),
        )

        # Track reminder
        sb.from_('invoices').update({
            'reminder_count': reminder_count,
            'last_reminder_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', req.invoice_id).execute()

        return {"status": "sent", "email_id": email_id, "reminder_level": min(reminder_count, 3)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/email/payment-confirmation")
async def api_send_payment_confirmation(req: SendReminderRequest, authorization: str = Header(None)):
    user = await get_current_user(authorization)

    sb = get_supabase()
    inv_res = sb.from_('invoices').select('*').eq('id', req.invoice_id).single().execute()
    invoice = inv_res.data
    if not invoice:
        raise HTTPException(404, "Facture non trouvée")

    # Get owner email
    owner_res = sb.from_('users').select('email').eq('id', user.id).limit(1).execute()
    owner_email = owner_res.data[0]['email'] if owner_res.data else user.email

    company_name = 'BTP Facture'
    settings_res = sb.from_('settings').select('company_name').eq('user_id', user.id).limit(1).execute()
    if settings_res.data and settings_res.data[0].get('company_name'):
        company_name = settings_res.data[0]['company_name']

    total_ttc = f"{float(invoice.get('total_ttc') or 0):,.2f}".replace(',', ' ')

    try:
        email_id = await email_service.send_payment_confirmation(
            owner_email=owner_email,
            client_name=invoice.get('client_name', ''),
            invoice_number=invoice.get('invoice_number', ''),
            total_ttc=total_ttc,
            company_name=company_name,
        )
        return {"status": "sent", "email_id": email_id}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/email/check-reminders")
async def api_check_reminders(authorization: str = Header(None)):
    """Manually trigger reminder check"""
    await get_current_user(authorization)
    await check_and_send_reminders()
    return {"status": "ok", "message": "Vérification des rappels effectuée"}


@app.get("/api/email/status")
async def api_email_status():
    configured = bool(os.environ.get('RESEND_API_KEY'))
    return {
        "configured": configured,
        "provider": "resend" if configured else "none",
        "sender": "facturation@facturebtp.fr" if configured else None,
    }


# Catch-all for legacy endpoints
@app.get("/api/{path:path}")
def catch_all_get(path: str):
    return {"error": "Endpoint non disponible", "mode": "supabase-only"}

@app.post("/api/{path:path}")
def catch_all_post(path: str):
    return {"error": "Endpoint non disponible", "mode": "supabase-only"}
