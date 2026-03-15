"""
HTML email templates for BTP Facture
Professional, mobile-responsive email templates using inline CSS and tables
"""

BASE_STYLE = """
body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f4f5f7; }
.container { max-width: 600px; margin: 0 auto; background: #ffffff; }
.header { background-color: #1e2328; padding: 24px 32px; }
.header h1 { color: #ffffff; font-size: 22px; margin: 0; }
.header .subtitle { color: #9ca3af; font-size: 13px; margin-top: 4px; }
.content { padding: 32px; }
.content p { color: #374151; font-size: 15px; line-height: 1.6; margin: 0 0 16px 0; }
.otp-box { background: #fff7ed; border: 2px solid #e8792f; border-radius: 8px; padding: 20px; text-align: center; margin: 24px 0; }
.otp-code { font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #e8792f; margin: 0; }
.btn { display: inline-block; background-color: #e8792f; color: #ffffff !important; text-decoration: none; padding: 12px 28px; border-radius: 6px; font-weight: 600; font-size: 15px; }
.info-table { width: 100%; border-collapse: collapse; margin: 16px 0; }
.info-table td { padding: 10px 12px; font-size: 14px; color: #374151; border-bottom: 1px solid #f3f4f6; }
.info-table td:first-child { font-weight: 600; color: #6b7280; width: 40%; }
.footer { background-color: #f9fafb; padding: 20px 32px; text-align: center; border-top: 1px solid #e5e7eb; }
.footer p { color: #9ca3af; font-size: 12px; margin: 0; }
"""


def _wrap(body_html):
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>{BASE_STYLE}</style></head>
<body><div class="container">{body_html}</div></body></html>"""


def welcome_email():
    return _wrap("""
        <div class="header">
            <h1>BTP Facture</h1>
            <div class="subtitle">Gestion devis &amp; factures</div>
        </div>
        <div class="content">
            <p>Bonjour,</p>
            <p>Votre compte <strong>BTP Facture</strong> a été créé avec succès.</p>
            <p>Vous pouvez dès maintenant créer des devis et des factures pour votre activité.</p>
            <p style="text-align: center; margin: 28px 0;">
                <a href="https://facturebtp.fr/login" class="btn">Accéder à mon tableau de bord</a>
            </p>
            <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
            <p>Cordialement,<br><strong>L'équipe BTP Facture</strong></p>
        </div>
        <div class="footer"><p>BTP Facture - Gestion simplifiée pour les professionnels du BTP</p></div>
    """)


def otp_email(code):
    return _wrap(f"""
        <div class="header">
            <h1>BTP Facture</h1>
            <div class="subtitle">Vérification de votre email</div>
        </div>
        <div class="content">
            <p>Bonjour,</p>
            <p>Votre code de vérification est :</p>
            <div class="otp-box">
                <p class="otp-code">{code}</p>
            </div>
            <p>Ce code est valable pendant <strong>10 minutes</strong>.</p>
            <p style="color: #9ca3af; font-size: 13px;">Si vous n'avez pas demandé ce code, vous pouvez ignorer cet email.</p>
            <p>BTP Facture</p>
        </div>
        <div class="footer"><p>BTP Facture - Gestion simplifiée pour les professionnels du BTP</p></div>
    """)


def invoice_email(client_name, invoice_number, total_ttc, due_date, invoice_link, company_name):
    return _wrap(f"""
        <div class="header">
            <h1>{company_name or 'BTP Facture'}</h1>
            <div class="subtitle">Facture {invoice_number}</div>
        </div>
        <div class="content">
            <p>Bonjour {client_name},</p>
            <p>Veuillez trouver ci-joint votre facture.</p>
            <table class="info-table">
                <tr><td>N° Facture</td><td><strong>{invoice_number}</strong></td></tr>
                <tr><td>Montant TTC</td><td><strong>{total_ttc} €</strong></td></tr>
                <tr><td>Date d'échéance</td><td>{due_date}</td></tr>
            </table>
            <p>Vous pouvez également consulter votre facture en ligne :</p>
            <p style="text-align: center; margin: 24px 0;">
                <a href="{invoice_link}" class="btn">Voir la facture</a>
            </p>
            <p>Merci pour votre confiance.</p>
            <p>Cordialement,<br><strong>{company_name or 'BTP Facture'}</strong></p>
        </div>
        <div class="footer"><p>{company_name or 'BTP Facture'} - Facture {invoice_number}</p></div>
    """)


def reminder_email(client_name, invoice_number, total_ttc, due_date, company_name, reminder_level=1):
    urgency = {
        1: ("Rappel", "#e8792f"),
        2: ("2ème rappel", "#d97706"),
        3: ("Dernier rappel", "#dc2626"),
    }.get(reminder_level, ("Rappel", "#e8792f"))

    return _wrap(f"""
        <div class="header" style="background-color: {urgency[1]};">
            <h1 style="color: #fff;">{urgency[0]} - Facture en attente</h1>
            <div class="subtitle" style="color: rgba(255,255,255,0.8);">{company_name or 'BTP Facture'}</div>
        </div>
        <div class="content">
            <p>Bonjour {client_name},</p>
            <p>Nous vous rappelons que la facture suivante est en attente de règlement.</p>
            <table class="info-table">
                <tr><td>N° Facture</td><td><strong>{invoice_number}</strong></td></tr>
                <tr><td>Montant</td><td><strong>{total_ttc} €</strong></td></tr>
                <tr><td>Échéance</td><td>{due_date}</td></tr>
            </table>
            <p>Si votre règlement a déjà été envoyé, veuillez ignorer ce message.</p>
            <p>Cordialement,<br><strong>{company_name or 'BTP Facture'}</strong></p>
        </div>
        <div class="footer"><p>{company_name or 'BTP Facture'}</p></div>
    """)


def payment_confirmation_email(client_name, invoice_number, total_ttc, company_name):
    return _wrap(f"""
        <div class="header" style="background-color: #059669;">
            <h1 style="color: #fff;">Paiement reçu</h1>
            <div class="subtitle" style="color: rgba(255,255,255,0.8);">{company_name or 'BTP Facture'}</div>
        </div>
        <div class="content">
            <p>Un paiement vient d'être reçu.</p>
            <table class="info-table">
                <tr><td>Client</td><td><strong>{client_name}</strong></td></tr>
                <tr><td>Facture</td><td><strong>{invoice_number}</strong></td></tr>
                <tr><td>Montant</td><td><strong>{total_ttc} €</strong></td></tr>
            </table>
        </div>
        <div class="footer"><p>{company_name or 'BTP Facture'}</p></div>
    """)
