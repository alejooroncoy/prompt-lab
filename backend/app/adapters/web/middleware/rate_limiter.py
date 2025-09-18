"""
Rate Limiting Middleware.
Implements rate limiting using Redis for distributed applications.
"""
import time
import logging
from typing import Dict, Tuple
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.dependencies import get_cache_repository

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.
    """
    
    def __init__(
        self, 
        app, 
        requests_per_minute: int = 100,
        window_seconds: int = 60
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self._local_cache: Dict[str, Tuple[int, float]] = {}
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path.endswith("/health"):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not await self._check_rate_limit(client_id):
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {self.requests_per_minute} per {self.window_seconds} seconds",
                    "retry_after": self.window_seconds
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        await self._add_rate_limit_headers(response, client_id)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        # Try to get real IP from headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Use user ID if available (for authenticated requests)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limit."""
        try:
            cache_repo = get_cache_repository()
            current_time = time.time()
            
            # Try Redis first
            if hasattr(cache_repo, '_connected') and cache_repo._connected:
                return await self._check_redis_rate_limit(cache_repo, client_id, current_time)
            else:
                # Fallback to local cache
                return self._check_local_rate_limit(client_id, current_time)
                
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}")
            # Allow request if rate limiting fails
            return True
    
    async def _check_redis_rate_limit(
        self, 
        cache_repo, 
        client_id: str, 
        current_time: float
    ) -> bool:
        """Check rate limit using Redis."""
        try:
            key = f"rate_limit:{client_id}"
            
            # Get current count
            count_str = await cache_repo.get(key)
            count = int(count_str) if count_str else 0
            
            if count >= self.requests_per_minute:
                return False
            
            # Increment counter
            await cache_repo.increment(key)
            
            # Set expiration if this is the first request
            if count == 0:
                await cache_repo.expire(key, self.window_seconds)
            
            return True
            
        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}")
            return True
    
    def _check_local_rate_limit(self, client_id: str, current_time: float) -> bool:
        """Check rate limit using local cache."""
        try:
            if client_id in self._local_cache:
                count, window_start = self._local_cache[client_id]
                
                # Check if window has expired
                if current_time - window_start >= self.window_seconds:
                    # Reset window
                    self._local_cache[client_id] = (1, current_time)
                    return True
                
                # Check if limit exceeded
                if count >= self.requests_per_minute:
                    return False
                
                # Increment count
                self._local_cache[client_id] = (count + 1, window_start)
            else:
                # First request in window
                self._local_cache[client_id] = (1, current_time)
            
            return True
            
        except Exception as e:
            logger.warning(f"Local rate limit check failed: {e}")
            return True
    
    async def _add_rate_limit_headers(self, response: Response, client_id: str) -> None:
        """Add rate limit headers to response."""
        try:
            cache_repo = get_cache_repository()
            
            if hasattr(cache_repo, '_connected') and cache_repo._connected:
                # Get current count from Redis
                key = f"rate_limit:{client_id}"
                count_str = await cache_repo.get(key)
                count = int(count_str) if count_str else 0
            else:
                # Get from local cache
                if client_id in self._local_cache:
                    count, _ = self._local_cache[client_id]
                else:
                    count = 0
            
            # Add headers
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(max(0, self.requests_per_minute - count))
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_seconds))
            
        except Exception as e:
            logger.warning(f"Failed to add rate limit headers: {e}")
    
    def _cleanup_local_cache(self) -> None:
        """Cleanup expired entries from local cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, window_start) in self._local_cache.items()
            if current_time - window_start >= self.window_seconds
        ]
        
        for key in expired_keys:
            del self._local_cache[key]
