"""
Email service using Resend API
Handles all transactional email sending for BTP Facture
"""

import os
import asyncio
import logging
import base64
import resend

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'BTP Facture <facturation@facturebtp.fr>')


def _init():
    key = os.environ.get('RESEND_API_KEY')
    if key:
        resend.api_key = key
        return True
    logger.error("RESEND_API_KEY not configured")
    return False


async def send_email(to, subject, html, attachments=None):
    """Send an email via Resend. Returns email_id or raises."""
    if not _init():
        raise ValueError("Service email non configuré (RESEND_API_KEY manquant)")

    params = {
        "from": SENDER_EMAIL,
        "to": [to] if isinstance(to, str) else to,
        "subject": subject,
        "html": html,
    }

    if attachments:
        params["attachments"] = attachments

    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        email_id = result.get("id") if isinstance(result, dict) else getattr(result, 'id', None)
        logger.info(f"Email sent to {to}: {email_id}")
        return email_id
    except Exception as e:
        logger.error(f"Email send failed to {to}: {e}")
        raise


async def send_welcome(email):
    from email_templates import welcome_email
    return await send_email(
        to=email,
        subject="Bienvenue sur BTP Facture",
        html=welcome_email(),
    )


async def send_otp(email, code):
    from email_templates import otp_email
    return await send_email(
        to=email,
        subject="Votre code de vérification BTP Facture",
        html=otp_email(code),
    )


async def send_invoice(client_email, client_name, invoice_number, total_ttc, due_date, invoice_link, company_name, pdf_bytes=None):
    from email_templates import invoice_email
    attachments = None
    if pdf_bytes:
        attachments = [{
            "filename": f"{invoice_number}.pdf",
            "content": base64.b64encode(pdf_bytes).decode('utf-8'),
            "type": "application/pdf",
        }]

    return await send_email(
        to=client_email,
        subject=f"Votre facture {invoice_number}",
        html=invoice_email(client_name, invoice_number, total_ttc, due_date, invoice_link, company_name),
        attachments=attachments,
    )


async def send_reminder(client_email, client_name, invoice_number, total_ttc, due_date, company_name, reminder_level=1):
    from email_templates import reminder_email
    return await send_email(
        to=client_email,
        subject=f"Rappel : facture {invoice_number} en attente de paiement",
        html=reminder_email(client_name, invoice_number, total_ttc, due_date, company_name, reminder_level),
    )


async def send_payment_confirmation(owner_email, client_name, invoice_number, total_ttc, company_name):
    from email_templates import payment_confirmation_email
    return await send_email(
        to=owner_email,
        subject=f"Paiement reçu - Facture {invoice_number}",
        html=payment_confirmation_email(client_name, invoice_number, total_ttc, company_name),
    )
