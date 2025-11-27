"""
Redis Cache Utility
Provides caching functionality for expensive operations
"""
import json
import logging
import hashlib
from functools import wraps
from typing import Any, Optional, Callable
import redis
from flask import current_app

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager with connection pooling"""
    
    def __init__(self):
        self._client = None
        self._enabled = True
    
    def init_app(self, app):
        """Initialize Redis connection from app config"""
        try:
            self._client = redis.Redis(
                host=app.config.get('REDIS_HOST', 'localhost'),
                port=app.config.get('REDIS_PORT', 6379),
                db=app.config.get('REDIS_DB', 0),
                password=app.config.get('REDIS_PASSWORD'),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self._client.ping()
            logger.info("Redis cache initialized successfully")
        except redis.RedisError as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self._enabled = False
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client"""
        return self._client if self._enabled else None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._enabled:
            return None
        
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache get error for key {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, expiration: Optional[int] = None) -> bool:
        """Set value in cache with optional expiration (seconds)"""
        if not self._enabled:
            return False
        
        try:
            expiration = expiration or current_app.config.get('CACHE_EXPIRATION_SECONDS', 3600)
            serialized = json.dumps(value)
            self._client.setex(key, expiration, serialized)
            return True
        except (redis.RedisError, TypeError) as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._enabled:
            return False
        
        try:
            self._client.delete(key)
            return True
        except redis.RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self._enabled:
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._enabled:
            return False
        
        try:
            return bool(self._client.exists(key))
        except redis.RedisError:
            return False


# Global cache instance
cache = RedisCache()


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a unique cache key from arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(expiration: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Usage:
        @cached(expiration=3600, key_prefix="similarity")
        def expensive_operation(text):
            return complex_calculation(text)
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{f.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {f.__name__}")
                return cached_result
            
            # Execute function
            logger.debug(f"Cache miss for {f.__name__}")
            result = f(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, expiration)
            
            return result
        
        return wrapper
    
    return decorator
