"""
OTP Service for BTP Facture
Secure OTP generation, hashing, and verification with MongoDB storage
"""

import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import bcrypt
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


# OTP Configuration
MAX_ATTEMPTS = 5
OTP_EXPIRATION_MINUTES = 10
MAX_RESEND_PER_HOUR = 5
RESEND_COOLDOWN_SECONDS = 60


class OTPService:
    """
    Secure OTP service with bcrypt hashing and MongoDB storage.
    
    Features:
    - Secure 6-digit OTP generation using secrets module
    - bcrypt hashing for OTP storage
    - Configurable expiration (default 10 minutes)
    - Maximum attempt tracking
    - Resend rate limiting
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.email_verifications
    
    async def init_indexes(self) -> None:
        """Create necessary indexes including TTL index on expires_at"""
        try:
            # TTL index to auto-delete expired OTPs
            await self.collection.create_index(
                "expires_at",
                expireAfterSeconds=0,
                name="ttl_expires_at"
            )
            # Unique index on user_id + email for lookups
            await self.collection.create_index(
                [("user_id", 1), ("email", 1)],
                name="idx_user_email"
            )
            # Index for email lookups
            await self.collection.create_index(
                "email",
                name="idx_email"
            )
            logger.info("OTP indexes created successfully")
        except Exception as e:
            logger.warning(f"Index creation warning (may already exist): {e}")
    
    @staticmethod
    def generate_otp() -> str:
        """
        Generate a secure 6-digit OTP code using secrets module.
        
        Returns:
            str: 6-digit OTP code
        """
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    @staticmethod
    def hash_otp(otp_code: str) -> str:
        """
        Hash OTP code using bcrypt.
        
        Args:
            otp_code: Plain text OTP code
            
        Returns:
            str: bcrypt hashed OTP
        """
        return bcrypt.hashpw(
            otp_code.encode('utf-8'),
            bcrypt.gensalt(rounds=10)
        ).decode('utf-8')
    
    @staticmethod
    def verify_otp_hash(otp_code: str, otp_hash: str) -> bool:
        """
        Verify OTP code against bcrypt hash.
        
        Args:
            otp_code: Plain text OTP code
            otp_hash: bcrypt hashed OTP
            
        Returns:
            bool: True if OTP matches
        """
        try:
            return bcrypt.checkpw(
                otp_code.encode('utf-8'),
                otp_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def expiration_time(minutes: int = OTP_EXPIRATION_MINUTES) -> datetime:
        """
        Calculate OTP expiration time.
        
        Args:
            minutes: Minutes until expiration (default 10)
            
        Returns:
            datetime: Expiration timestamp
        """
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)
    
    async def create_otp(
        self,
        user_id: str,
        email: str,
        expiration_minutes: int = OTP_EXPIRATION_MINUTES
    ) -> str:
        """
        Create and store a new OTP for a user.
        Deletes any existing OTP for this user/email combination.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            expiration_minutes: Minutes until OTP expires
            
        Returns:
            str: Plain text OTP code (to be sent via email)
        """
        # Delete any existing OTP for this user
        await self.collection.delete_many({
            "user_id": user_id,
            "email": email
        })
        
        # Generate new OTP
        otp_code = self.generate_otp()
        otp_hash = self.hash_otp(otp_code)
        
        # Create verification document
        now = datetime.now(timezone.utc)
        verification_doc = {
            "user_id": user_id,
            "email": email,
            "otp_hash": otp_hash,
            "expires_at": self.expiration_time(expiration_minutes),
            "attempts": 0,
            "verified": False,
            "resend_count": 0,
            "last_sent_at": now,
            "created_at": now
        }
        
        await self.collection.insert_one(verification_doc)
        
        # Log OTP in development (never in production!)
        import os
        if os.environ.get("ENVIRONMENT", "development") == "development":
            print(f"""
╔══════════════════════════════════════════════════════════════╗
║ [DEV MODE] OTP CODE GENERATED                                ║
╠══════════════════════════════════════════════════════════════╣
║ Email: {email}
║ OTP Code: {otp_code}
║ Expires: {expiration_minutes} minutes
╚══════════════════════════════════════════════════════════════╝
            """, flush=True)
        
        return otp_code
    
    async def verify_otp(
        self,
        user_id: str,
        email: str,
        otp_code: str
    ) -> Dict[str, Any]:
        """
        Verify an OTP code.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            otp_code: OTP code to verify
            
        Returns:
            dict: {"success": bool, "message": str}
            
        Raises:
            HTTPException: On validation errors
        """
        # Find verification document
        verification = await self.collection.find_one({
            "user_id": user_id,
            "email": email,
            "verified": False
        })
        
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucun code OTP en attente pour cet utilisateur"
            )
        
        # Check expiration (handle both naive and aware datetimes from MongoDB)
        expires_at = verification["expires_at"]
        now = datetime.now(timezone.utc)
        # Make comparison timezone-aware if needed
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if now > expires_at:
            await self.collection.delete_one({"_id": verification["_id"]})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le code OTP a expiré. Demandez un nouveau code."
            )
        
        # Check max attempts
        if verification["attempts"] >= MAX_ATTEMPTS:
            await self.collection.delete_one({"_id": verification["_id"]})
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Trop de tentatives. Demandez un nouveau code."
            )
        
        # Increment attempts
        await self.collection.update_one(
            {"_id": verification["_id"]},
            {"$inc": {"attempts": 1}}
        )
        
        # Verify OTP
        if not self.verify_otp_hash(otp_code, verification["otp_hash"]):
            remaining = MAX_ATTEMPTS - verification["attempts"] - 1
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Code OTP invalide. {remaining} tentative(s) restante(s)."
            )
        
        # Mark as verified
        await self.collection.update_one(
            {"_id": verification["_id"]},
            {
                "$set": {
                    "verified": True,
                    "verified_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {
            "success": True,
            "message": "Code OTP vérifié avec succès"
        }
    
    async def can_resend_otp(self, user_id: str, email: str) -> Dict[str, Any]:
        """
        Check if OTP resend is allowed based on rate limits.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            
        Returns:
            dict: {"can_resend": bool, "wait_seconds": int, "message": str}
        """
        verification = await self.collection.find_one({
            "user_id": user_id,
            "email": email
        })
        
        if not verification:
            return {
                "can_resend": True,
                "wait_seconds": 0,
                "message": "OK"
            }
        
        now = datetime.now(timezone.utc)
        last_sent = verification.get("last_sent_at", verification["created_at"])
        
        # Check cooldown (60 seconds minimum between resends)
        seconds_since_last = (now - last_sent).total_seconds()
        if seconds_since_last < RESEND_COOLDOWN_SECONDS:
            wait_seconds = int(RESEND_COOLDOWN_SECONDS - seconds_since_last)
            return {
                "can_resend": False,
                "wait_seconds": wait_seconds,
                "message": f"Attendez {wait_seconds} secondes avant de renvoyer"
            }
        
        # Check hourly limit
        resend_count = verification.get("resend_count", 0)
        if resend_count >= MAX_RESEND_PER_HOUR:
            # Check if an hour has passed since first send
            created_at = verification["created_at"]
            if (now - created_at).total_seconds() < 3600:
                return {
                    "can_resend": False,
                    "wait_seconds": int(3600 - (now - created_at).total_seconds()),
                    "message": "Limite de renvoi atteinte. Réessayez dans 1 heure."
                }
        
        return {
            "can_resend": True,
            "wait_seconds": 0,
            "message": "OK"
        }
    
    async def resend_otp(
        self,
        user_id: str,
        email: str,
        expiration_minutes: int = OTP_EXPIRATION_MINUTES
    ) -> str:
        """
        Resend OTP with rate limiting checks.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            expiration_minutes: Minutes until OTP expires
            
        Returns:
            str: New plain text OTP code
            
        Raises:
            HTTPException: On rate limit exceeded
        """
        # Check if resend is allowed
        can_resend = await self.can_resend_otp(user_id, email)
        if not can_resend["can_resend"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=can_resend["message"]
            )
        
        # Get existing verification to preserve resend_count
        existing = await self.collection.find_one({
            "user_id": user_id,
            "email": email
        })
        
        current_resend_count = existing.get("resend_count", 0) if existing else 0
        
        # Delete existing OTP
        await self.collection.delete_many({
            "user_id": user_id,
            "email": email
        })
        
        # Generate new OTP
        otp_code = self.generate_otp()
        otp_hash = self.hash_otp(otp_code)
        
        # Create new verification document with incremented resend_count
        now = datetime.now(timezone.utc)
        verification_doc = {
            "user_id": user_id,
            "email": email,
            "otp_hash": otp_hash,
            "expires_at": self.expiration_time(expiration_minutes),
            "attempts": 0,
            "verified": False,
            "resend_count": current_resend_count + 1,
            "last_sent_at": now,
            "created_at": now
        }
        
        await self.collection.insert_one(verification_doc)
        
        # Log in development
        import os
        if os.environ.get("ENVIRONMENT", "development") == "development":
            logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║ [DEV MODE] OTP CODE RESENT                                   ║
╠══════════════════════════════════════════════════════════════╣
║ Email: {email}
║ New OTP Code: {otp_code}
║ Resend count: {current_resend_count + 1}/{MAX_RESEND_PER_HOUR}
╚══════════════════════════════════════════════════════════════╝
            """)
        
        return otp_code
    
    async def delete_otp(self, user_id: str, email: str) -> bool:
        """
        Delete OTP verification document.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            
        Returns:
            bool: True if deleted
        """
        result = await self.collection.delete_many({
            "user_id": user_id,
            "email": email
        })
        return result.deleted_count > 0
    
    async def is_email_verified(self, user_id: str, email: str) -> bool:
        """
        Check if email is verified for a user.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            
        Returns:
            bool: True if verified
        """
        verification = await self.collection.find_one({
            "user_id": user_id,
            "email": email,
            "verified": True
        })
        return verification is not None


# Factory function
def get_otp_service(db: AsyncIOMotorDatabase) -> OTPService:
    """Create OTP service instance"""
    return OTPService(db)
