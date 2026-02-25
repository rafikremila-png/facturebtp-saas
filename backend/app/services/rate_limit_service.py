"""
Rate Limit Service for BTP Facture
In-memory IP-based rate limiting with easy Redis migration path
"""

import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from threading import Lock
from fastapi import HTTPException, status, Request

logger = logging.getLogger(__name__)


@dataclass
class RateLimitEntry:
    """Single rate limit entry for an IP"""
    requests: int = 0
    window_start: float = field(default_factory=time.time)


class RateLimitService:
    """
    In-memory rate limiter with configurable limits per endpoint.
    
    Default: 10 requests per minute per IP on auth endpoints.
    
    Storage is in-memory (Python dict) but designed for easy Redis migration:
    - All state access is through methods
    - Keys are strings (IP:endpoint)
    - Values are simple counters with timestamps
    
    Thread-safe using locks for concurrent access.
    """
    
    def __init__(
        self,
        default_requests_per_minute: int = 10,
        cleanup_interval_seconds: int = 300
    ):
        self.default_requests_per_minute = default_requests_per_minute
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.window_seconds = 60  # 1 minute windows
        
        # In-memory storage: Dict[key, RateLimitEntry]
        self._storage: Dict[str, RateLimitEntry] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()
        
        # Endpoint-specific limits (can be customized)
        self._endpoint_limits: Dict[str, int] = {
            "/api/auth/register": 5,      # Stricter for registration
            "/api/auth/verify-otp": 10,
            "/api/auth/resend-otp": 3,    # Very strict for resend
            "/api/auth/login": 10,
        }
    
    def _get_key(self, ip: str, endpoint: str) -> str:
        """Generate storage key from IP and endpoint"""
        return f"{ip}:{endpoint}"
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from storage"""
        now = time.time()
        if now - self._last_cleanup < self.cleanup_interval_seconds:
            return
        
        with self._lock:
            expired_keys = [
                key for key, entry in self._storage.items()
                if now - entry.window_start > self.window_seconds
            ]
            for key in expired_keys:
                del self._storage[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit entries")
            
            self._last_cleanup = now
    
    def get_limit_for_endpoint(self, endpoint: str) -> int:
        """Get rate limit for a specific endpoint"""
        # Normalize endpoint (remove trailing slash, query params)
        clean_endpoint = endpoint.split("?")[0].rstrip("/")
        return self._endpoint_limits.get(
            clean_endpoint,
            self.default_requests_per_minute
        )
    
    def check_rate_limit(
        self,
        ip: str,
        endpoint: str
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            ip: Client IP address
            endpoint: API endpoint being accessed
            
        Returns:
            Tuple[allowed: bool, remaining: int, reset_in_seconds: int]
        """
        self._cleanup_expired()
        
        key = self._get_key(ip, endpoint)
        limit = self.get_limit_for_endpoint(endpoint)
        now = time.time()
        
        with self._lock:
            entry = self._storage.get(key)
            
            if entry is None:
                # First request in window
                self._storage[key] = RateLimitEntry(requests=1, window_start=now)
                return True, limit - 1, self.window_seconds
            
            # Check if window has expired
            if now - entry.window_start > self.window_seconds:
                # New window
                self._storage[key] = RateLimitEntry(requests=1, window_start=now)
                return True, limit - 1, self.window_seconds
            
            # Check if limit exceeded
            if entry.requests >= limit:
                reset_in = int(self.window_seconds - (now - entry.window_start))
                return False, 0, max(reset_in, 1)
            
            # Increment counter
            entry.requests += 1
            remaining = limit - entry.requests
            reset_in = int(self.window_seconds - (now - entry.window_start))
            
            return True, remaining, max(reset_in, 1)
    
    def increment(self, ip: str, endpoint: str) -> Tuple[int, int]:
        """
        Increment request count and return current state.
        
        Args:
            ip: Client IP address
            endpoint: API endpoint
            
        Returns:
            Tuple[remaining: int, reset_in_seconds: int]
        """
        allowed, remaining, reset_in = self.check_rate_limit(ip, endpoint)
        return remaining, reset_in
    
    def is_rate_limited(self, ip: str, endpoint: str) -> bool:
        """
        Quick check if IP is rate limited for endpoint.
        
        Args:
            ip: Client IP address
            endpoint: API endpoint
            
        Returns:
            bool: True if rate limited
        """
        allowed, _, _ = self.check_rate_limit(ip, endpoint)
        return not allowed
    
    def get_remaining(self, ip: str, endpoint: str) -> int:
        """Get remaining requests for IP/endpoint"""
        _, remaining, _ = self.check_rate_limit(ip, endpoint)
        return remaining
    
    def reset(self, ip: str, endpoint: Optional[str] = None) -> None:
        """
        Reset rate limit for an IP (optionally for specific endpoint).
        Useful for testing or manual override.
        
        Args:
            ip: Client IP address
            endpoint: Optional specific endpoint to reset
        """
        with self._lock:
            if endpoint:
                key = self._get_key(ip, endpoint)
                self._storage.pop(key, None)
            else:
                # Reset all endpoints for this IP
                keys_to_delete = [k for k in self._storage if k.startswith(f"{ip}:")]
                for key in keys_to_delete:
                    del self._storage[key]
    
    def get_stats(self) -> Dict[str, int]:
        """Get current rate limiter statistics"""
        with self._lock:
            return {
                "total_entries": len(self._storage),
                "unique_ips": len(set(k.split(":")[0] for k in self._storage)),
            }


# Singleton instance
_rate_limiter: Optional[RateLimitService] = None


def get_rate_limiter() -> RateLimitService:
    """Get or create singleton rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimitService()
    return _rate_limiter


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, handling proxies.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Client IP address
    """
    # Check for forwarded headers (reverse proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in the list is the original client
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


async def rate_limit_middleware(
    request: Request,
    endpoint: str,
    limiter: Optional[RateLimitService] = None
) -> None:
    """
    Rate limiting middleware for auth endpoints.
    
    Args:
        request: FastAPI request object
        endpoint: Endpoint path
        limiter: Optional rate limiter instance (uses singleton if not provided)
        
    Raises:
        HTTPException: 429 if rate limited
    """
    if limiter is None:
        limiter = get_rate_limiter()
    
    ip = get_client_ip(request)
    allowed, remaining, reset_in = limiter.check_rate_limit(ip, endpoint)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for IP {ip} on {endpoint}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Trop de requêtes. Réessayez dans {reset_in} secondes.",
            headers={
                "X-RateLimit-Limit": str(limiter.get_limit_for_endpoint(endpoint)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_in),
                "Retry-After": str(reset_in)
            }
        )


def rate_limit_dependency(endpoint: str):
    """
    FastAPI dependency for rate limiting specific endpoints.
    
    Usage:
        @router.post("/auth/login")
        async def login(
            request: Request,
            _: None = Depends(rate_limit_dependency("/api/auth/login"))
        ):
            ...
    
    Args:
        endpoint: Endpoint path for rate limiting
        
    Returns:
        Dependency function
    """
    async def _check_rate_limit(request: Request):
        await rate_limit_middleware(request, endpoint)
    
    return _check_rate_limit
