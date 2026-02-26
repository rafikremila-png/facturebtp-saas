"""
Email Service for BTP Facture
SMTP-based email sending with Mailtrap support for development
"""

import os
import ssl
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service using SMTP with TLS.
    Supports Mailtrap for development and any SMTP provider for production.
    """
    
    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "2525"))  # Default to Mailtrap port
        self.smtp_user = os.environ.get("SMTP_USER")
        self.smtp_pass = os.environ.get("SMTP_PASS")
        self.smtp_from = os.environ.get("SMTP_FROM", "noreply@btpfacture.com")
        self.environment = os.environ.get("ENVIRONMENT", "development")
        
        # Validate configuration
        self._is_configured = all([
            self.smtp_host,
            self.smtp_port,
            self.smtp_user,
            self.smtp_pass
        ])
        
        # Debug log configuration at instantiation
        logger.info(f"[EmailService] Initialized with:")
        logger.info(f"  - SMTP_HOST: {self.smtp_host}")
        logger.info(f"  - SMTP_PORT: {self.smtp_port}")
        logger.info(f"  - SMTP_USER: {self.smtp_user}")
        logger.info(f"  - SMTP_FROM: {self.smtp_from}")
        logger.info(f"  - SMTP_PASS: {'***SET***' if self.smtp_pass else '***NOT SET***'}")
        logger.info(f"  - Is Configured: {self._is_configured}")
        
        if not self._is_configured:
            logger.warning(
                "SMTP not fully configured. "
                "Required: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS"
            )
    
    @property
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return self._is_configured
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP with TLS.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            
        Returns:
            bool: True if sent successfully
            
        Raises:
            HTTPException: On SMTP errors
        """
        if not self._is_configured:
            # In development, log the email instead of sending
            if self.environment == "development":
                logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║ [DEV MODE] EMAIL NOT SENT (SMTP not configured)              ║
╠══════════════════════════════════════════════════════════════╣
║ To: {to_email}
║ Subject: {subject}
║ Body: {body[:100]}...
╚══════════════════════════════════════════════════════════════╝
                """)
                return True
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service email non configuré. Contactez l'administrateur."
                )
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.smtp_from
            message["To"] = to_email
            message["Subject"] = subject
            
            # Attach plain text part
            part_text = MIMEText(body, "plain", "utf-8")
            message.attach(part_text)
            
            # Attach HTML part if provided
            if html_body:
                part_html = MIMEText(html_body, "html", "utf-8")
                message.attach(part_html)
            
            # Create secure SSL context
            context = ssl.create_default_context()
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.smtp_from, to_email, message.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Erreur d'authentification SMTP"
            )
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipient refused: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adresse email invalide ou refusée"
            )
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Erreur d'envoi email. Réessayez plus tard."
            )
        except Exception as e:
            logger.error(f"Unexpected email error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur inattendue lors de l'envoi de l'email"
            )
    
    def send_otp_email(self, to_email: str, otp_code: str) -> bool:
        """
        Send OTP verification email.
        
        Args:
            to_email: Recipient email address
            otp_code: 6-digit OTP code
            
        Returns:
            bool: True if sent successfully
        """
        subject = "BTP Facture - Code de vérification"
        
        body = f"""Bonjour,

Votre code de vérification BTP Facture est :

{otp_code}

Ce code est valide pendant 10 minutes.

Si vous n'avez pas demandé ce code, ignorez cet email.

Cordialement,
L'équipe BTP Facture
"""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #f97316, #ea580c); padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ color: white; margin: 0; font-size: 24px; }}
        .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .otp-code {{ background: #fff; border: 2px dashed #f97316; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #f97316; margin: 20px 0; border-radius: 8px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 10px 15px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ BTP Facture</h1>
        </div>
        <div class="content">
            <p>Bonjour,</p>
            <p>Votre code de vérification est :</p>
            <div class="otp-code">{otp_code}</div>
            <p>Ce code est valide pendant <strong>10 minutes</strong>.</p>
            <div class="warning">
                ⚠️ Si vous n'avez pas demandé ce code, ignorez cet email.
            </div>
        </div>
        <div class="footer">
            <p>© 2026 BTP Facture - Gestion de devis et factures pour le BTP</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """
        Send welcome email after successful registration.
        
        Args:
            to_email: Recipient email address
            user_name: User's name
            
        Returns:
            bool: True if sent successfully
        """
        subject = "Bienvenue sur BTP Facture !"
        
        body = f"""Bonjour {user_name},

Bienvenue sur BTP Facture !

Votre compte a été activé avec succès. Vous bénéficiez d'un essai gratuit de 14 jours avec :
- Création illimitée de devis
- Jusqu'à 9 factures
- Export PDF professionnel
- Gestion des clients

Pour commencer, connectez-vous à votre espace.

Cordialement,
L'équipe BTP Facture
"""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #f97316, #ea580c); padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ color: white; margin: 0; font-size: 28px; }}
        .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .feature-list {{ list-style: none; padding: 0; }}
        .feature-list li {{ padding: 10px 0; padding-left: 30px; position: relative; }}
        .feature-list li::before {{ content: "✓"; position: absolute; left: 0; color: #22c55e; font-weight: bold; }}
        .cta-button {{ display: inline-block; background: #f97316; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 20px; }}
        .trial-badge {{ background: #dbeafe; color: #1d4ed8; padding: 10px 20px; border-radius: 20px; display: inline-block; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Bienvenue sur BTP Facture !</h1>
        </div>
        <div class="content">
            <p>Bonjour <strong>{user_name}</strong>,</p>
            <p>Votre compte a été activé avec succès !</p>
            <div class="trial-badge">🎁 Essai gratuit de 14 jours</div>
            <p>Votre essai inclut :</p>
            <ul class="feature-list">
                <li>Création illimitée de devis</li>
                <li>Jusqu'à 9 factures</li>
                <li>Export PDF professionnel</li>
                <li>Gestion complète des clients</li>
                <li>Mentions légales françaises</li>
            </ul>
            <p style="text-align: center;">
                <a href="#" class="cta-button">Accéder à mon espace</a>
            </p>
        </div>
        <div class="footer">
            <p>© 2026 BTP Facture - Gestion de devis et factures pour le BTP</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to_email, subject, body, html_body)


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create singleton email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
