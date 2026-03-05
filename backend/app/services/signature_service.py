"""
Electronic Signature Service
Legally valid electronic signatures for quotes
"""
import uuid
import hashlib
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import logging

from app.core.config import settings
from app.core.database import db, is_mongodb
from app.core.security import create_signature_token, decode_token

logger = logging.getLogger(__name__)

class SignatureService:
    """Service for electronic signatures"""
    
    @staticmethod
    async def generate_signature_link(quote_id: str, client_email: str, user_id: str) -> Dict[str, Any]:
        """Generate a secure signature link for a quote"""
        # Verify quote exists and belongs to user
        if is_mongodb():
            quote = await db.quotes.find_one(
                {"id": quote_id, "user_id": user_id},
                {"_id": 0}
            )
            if not quote:
                raise ValueError("Devis non trouvé")
            
            if quote.get("status") == "signed":
                raise ValueError("Ce devis est déjà signé")
        
        # Generate secure token
        token = create_signature_token(quote_id, client_email)
        
        # Build signature URL
        signature_url = f"{settings.FRONTEND_URL}/sign/{token}"
        
        # Store the token reference
        if is_mongodb():
            await db.signature_tokens.update_one(
                {"quote_id": quote_id},
                {
                    "$set": {
                        "token": token,
                        "client_email": client_email,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "used": False
                    }
                },
                upsert=True
            )
        
        return {
            "signature_url": signature_url,
            "token": token,
            "expires_in_days": 7
        }
    
    @staticmethod
    async def validate_signature_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate a signature token and return quote details"""
        payload = decode_token(token)
        
        if not payload:
            return None
        
        if payload.get("type") != "signature":
            return None
        
        quote_id = payload.get("quote_id")
        client_email = payload.get("client_email")
        
        if not quote_id or not client_email:
            return None
        
        # Get quote with client details
        if is_mongodb():
            quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
            if not quote:
                return None
            
            # Get client
            client = None
            if quote.get("client_id"):
                client = await db.clients.find_one({"id": quote["client_id"]}, {"_id": 0})
            
            # Get user settings for company info
            user_settings = await db.user_settings.find_one({"user_id": quote["user_id"]}, {"_id": 0})
            
            return {
                "quote": quote,
                "client": client,
                "company": user_settings,
                "client_email": client_email,
                "can_sign": quote.get("status") in ["draft", "sent"]
            }
        
        return None
    
    @staticmethod
    async def sign_quote(token: str, signature_data: Dict[str, Any], 
                         ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Sign a quote with electronic signature"""
        # Validate token
        validation = await SignatureService.validate_signature_token(token)
        if not validation:
            raise ValueError("Lien de signature invalide ou expiré")
        
        if not validation["can_sign"]:
            raise ValueError("Ce devis ne peut plus être signé")
        
        quote = validation["quote"]
        quote_id = quote["id"]
        
        # Validate signature data
        signer_name = signature_data.get("signer_name")
        signer_email = signature_data.get("signer_email")
        signature_image = signature_data.get("signature_data")  # Base64 image
        signer_title = signature_data.get("signer_title", "")
        
        if not signer_name or not signer_email or not signature_image:
            raise ValueError("Informations de signature incomplètes")
        
        # Create signature record
        signed_at = datetime.now(timezone.utc)
        
        # Generate certificate hash
        certificate_content = f"{quote_id}|{signer_name}|{signer_email}|{signed_at.isoformat()}|{ip_address}"
        certificate_hash = hashlib.sha256(certificate_content.encode()).hexdigest()
        
        signature_record = {
            "id": str(uuid.uuid4()),
            "quote_id": quote_id,
            "signer_name": signer_name,
            "signer_email": signer_email,
            "signer_title": signer_title,
            "signature_data": signature_image,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "signed_at": signed_at.isoformat(),
            "certificate_hash": certificate_hash,
            "certificate_pdf_url": None,  # Will be generated
            "created_at": signed_at.isoformat()
        }
        
        if is_mongodb():
            # Save signature
            await db.quote_signatures.insert_one(signature_record.copy())
            
            # Update quote status
            await db.quotes.update_one(
                {"id": quote_id},
                {
                    "$set": {
                        "status": "signed",
                        "signed_at": signed_at.isoformat(),
                        "updated_at": signed_at.isoformat()
                    }
                }
            )
            
            # Mark token as used
            await db.signature_tokens.update_one(
                {"quote_id": quote_id},
                {"$set": {"used": True}}
            )
        
        # Generate certificate PDF (placeholder - would need PDF generation)
        certificate_url = await SignatureService._generate_signature_certificate(
            quote, signature_record, validation.get("company")
        )
        
        # Update with certificate URL
        if certificate_url and is_mongodb():
            await db.quote_signatures.update_one(
                {"id": signature_record["id"]},
                {"$set": {"certificate_pdf_url": certificate_url}}
            )
        
        return {
            "success": True,
            "signature_id": signature_record["id"],
            "signed_at": signed_at.isoformat(),
            "certificate_hash": certificate_hash,
            "certificate_url": certificate_url,
            "message": "Devis signé avec succès"
        }
    
    @staticmethod
    async def get_signature(quote_id: str) -> Optional[Dict[str, Any]]:
        """Get signature for a quote"""
        if is_mongodb():
            signature = await db.quote_signatures.find_one(
                {"quote_id": quote_id},
                {"_id": 0, "signature_data": 0}  # Exclude large signature data
            )
            return signature
        return None
    
    @staticmethod
    async def get_signature_with_data(quote_id: str) -> Optional[Dict[str, Any]]:
        """Get signature including signature image data"""
        if is_mongodb():
            return await db.quote_signatures.find_one(
                {"quote_id": quote_id},
                {"_id": 0}
            )
        return None
    
    @staticmethod
    async def verify_signature(quote_id: str) -> Dict[str, Any]:
        """Verify the authenticity of a signature"""
        signature = await SignatureService.get_signature_with_data(quote_id)
        
        if not signature:
            return {
                "valid": False,
                "error": "Signature non trouvée"
            }
        
        # Recalculate hash
        certificate_content = f"{quote_id}|{signature['signer_name']}|{signature['signer_email']}|{signature['signed_at']}|{signature['ip_address']}"
        calculated_hash = hashlib.sha256(certificate_content.encode()).hexdigest()
        
        is_valid = calculated_hash == signature.get("certificate_hash")
        
        return {
            "valid": is_valid,
            "signer_name": signature.get("signer_name"),
            "signer_email": signature.get("signer_email"),
            "signed_at": signature.get("signed_at"),
            "certificate_hash": signature.get("certificate_hash"),
            "hash_match": is_valid
        }
    
    @staticmethod
    async def _generate_signature_certificate(quote: Dict, signature: Dict, 
                                               company: Optional[Dict]) -> Optional[str]:
        """Generate a signature certificate PDF"""
        # This is a placeholder - in production, use a PDF library like reportlab
        # For now, we'll store the certificate data
        
        certificate_filename = f"certificate_{signature['id']}.json"
        certificate_path = settings.SIGNATURES_PATH / certificate_filename
        
        import json
        certificate_data = {
            "type": "electronic_signature_certificate",
            "version": "1.0",
            "quote": {
                "id": quote["id"],
                "quote_number": quote.get("quote_number"),
                "title": quote.get("title"),
                "total_ttc": quote.get("total_ttc")
            },
            "signer": {
                "name": signature["signer_name"],
                "email": signature["signer_email"],
                "title": signature.get("signer_title")
            },
            "signature": {
                "signed_at": signature["signed_at"],
                "ip_address": signature["ip_address"],
                "certificate_hash": signature["certificate_hash"]
            },
            "company": {
                "name": company.get("company_name") if company else None,
                "siret": company.get("siret") if company else None
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        with open(certificate_path, 'w') as f:
            json.dump(certificate_data, f, indent=2)
        
        return f"/storage/signatures/{certificate_filename}"


# Create singleton instance
signature_service = SignatureService()
