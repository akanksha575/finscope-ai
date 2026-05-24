"""
Redis-based caching utilities for FinScope AI

Provides caching for:
- Query classification results
- LLM responses
- Research query generation
- Document embeddings
- Research results
"""

import json
import hashlib
from typing import Any, Optional, Dict, List
from datetime import timedelta
import redis.asyncio as redis
from utils.logger import log
from utils.helpers import get_env


class CacheManager:
    """Manages Redis cache with async operations"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache manager
        
        Args:
            redis_url: Redis connection URL (default: from env or localhost)
        """
        self.redis_url = redis_url or get_env(
            "REDIS_URL",
            default="redis://localhost:6379/0"
        )
        self.client: Optional[redis.Redis] = None
        self._connected = False
        
    async def connect(self):
        """Establish Redis connection"""
        if self._connected and self.client:
            return
        
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            # Test connection
            await self.client.ping()
            self._connected = True
            log.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            log.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.client = None
            self._connected = False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self._connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self._connected:
            await self.connect()
        
        if not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            log.warning(f"Cache get failed for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            await self.connect()
        
        if not self.client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)
            return True
        except Exception as e:
            log.warning(f"Cache set failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            log.warning(f"Cache delete failed for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.client:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception:
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "classify:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
        
        try:
            count = 0
            async for key in self.client.scan_iter(match=pattern):
                await self.client.delete(key)
                count += 1
            return count
        except Exception as e:
            log.warning(f"Cache clear pattern failed for {pattern}: {e}")
            return 0


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
        await _cache_manager.connect()
    return _cache_manager


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate cache key from prefix and arguments
    
    Args:
        prefix: Key prefix (e.g., "classify", "query_gen")
        *args: Positional arguments to hash
        **kwargs: Keyword arguments to hash
        
    Returns:
        Cache key string
    """
    # Combine all arguments
    key_parts = [prefix]
    
    # Add positional args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif isinstance(arg, (dict, list)):
            key_parts.append(json.dumps(arg, sort_keys=True, default=str))
        else:
            key_parts.append(str(hash(arg)))
    
    # Add keyword args (sorted for consistency)
    for key in sorted(kwargs.keys()):
        value = kwargs[key]
        if isinstance(value, (str, int, float, bool)):
            key_parts.append(f"{key}:{value}")
        elif isinstance(value, (dict, list)):
            key_parts.append(f"{key}:{json.dumps(value, sort_keys=True, default=str)}")
        else:
            key_parts.append(f"{key}:{hash(value)}")
    
    # Create hash of combined parts
    key_string = "|".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"{prefix}:{key_hash}"


# Cache TTL constants (in seconds)
CACHE_TTL = {
    "classification": 3600,  # 1 hour - queries don't change classification often
    "query_generation": 1800,  # 30 minutes - query generation can vary
    "embedding": 86400 * 7,  # 7 days - embeddings don't change
    "research_result": 3600 * 24,  # 24 hours - research results stay relevant longer
    "financial_data": 3600,  # 1 hour - financial data updates frequently
    "web_search": 1800,  # 30 minutes - web content changes quickly
    "llm_response": 3600,  # 1 hour - LLM responses for similar inputs
}


async def cached_call(
    cache_key: str,
    func,
    *args,
    ttl: Optional[int] = None,
    **kwargs
) -> Any:
    """
    Execute function with caching
    
    Args:
        cache_key: Cache key to use
        func: Async function to execute
        *args: Function arguments
        ttl: Time to live in seconds
        **kwargs: Function keyword arguments
        
    Returns:
        Function result (from cache or execution)
    """
    cache = await get_cache_manager()
    
    # Try to get from cache
    cached = await cache.get(cache_key)
    if cached is not None:
        log.debug(f"Cache hit for key: {cache_key}")
        return cached
    
    # Execute function
    log.debug(f"Cache miss for key: {cache_key}, executing function")
    result = await func(*args, **kwargs)
    
    # Store in cache
    if ttl is None:
        ttl = CACHE_TTL.get("llm_response", 3600)
    await cache.set(cache_key, result, ttl=ttl)
    
    return result
