"""
Redis Cache Repository Implementation.
Handles caching operations using Redis.
"""
import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis

from app.core.ports.repository_port import CacheRepositoryPort

logger = logging.getLogger(__name__)


class RedisCacheRepository(CacheRepositoryPort):
    """
    Redis implementation of cache repository.
    Handles caching operations for improved performance.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis cache repository.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis = None
        self._connected = False
    
    async def _ensure_connected(self) -> None:
        """Ensure Redis connection is established."""
        if self._connected and self._redis:
            return
        
        try:
            self._redis = redis.from_url(self.redis_url)
            await self._redis.ping()
            self._connected = True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._connected = False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        await self._ensure_connected()
        
        if not self._connected:
            return None
        
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            return value.decode('utf-8') if isinstance(value, bytes) else str(value)
        except Exception as e:
            logger.warning(f"Failed to get cache key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ttl_seconds: int = 3600
    ) -> None:
        """Set value in cache with TTL."""
        await self._ensure_connected()
        
        if not self._connected:
            return
        
        try:
            await self._redis.setex(key, ttl_seconds, value)
        except Exception as e:
            logger.warning(f"Failed to set cache key {key}: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        await self._ensure_connected()
        
        if not self._connected:
            return False
        
        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Failed to delete cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        await self._ensure_connected()
        
        if not self._connected:
            return False
        
        try:
            result = await self._redis.exists(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Failed to check cache key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        await self._ensure_connected()
        
        if not self._connected:
            return 0
        
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                return await self._redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Failed to clear cache pattern {pattern}: {e}")
            return 0
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value from cache."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON for key {key}")
        return None
    
    async def set_json(
        self, 
        key: str, 
        value: Dict[str, Any], 
        ttl_seconds: int = 3600
    ) -> None:
        """Set JSON value in cache."""
        try:
            json_value = json.dumps(value)
            await self.set(key, json_value, ttl_seconds)
        except Exception as e:
            logger.warning(f"Failed to set JSON cache key {key}: {e}")
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value in cache."""
        await self._ensure_connected()
        
        if not self._connected:
            return None
        
        try:
            return await self._redis.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Failed to increment cache key {key}: {e}")
            return None
    
    async def expire(self, key: str, ttl_seconds: int) -> bool:
        """Set expiration for existing key."""
        await self._ensure_connected()
        
        if not self._connected:
            return False
        
        try:
            result = await self._redis.expire(key, ttl_seconds)
            return result
        except Exception as e:
            logger.warning(f"Failed to set expiration for key {key}: {e}")
            return False
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False
