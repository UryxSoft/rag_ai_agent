"""
Rate Limiting System
Per-user rate limiting with Redis backend
"""
import logging
from functools import wraps
from flask import request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
from typing import Optional, Callable

logger = logging.getLogger(__name__)


def get_user_id_for_rate_limit():
    """
    Get user identifier for rate limiting
    Tries JWT token first, falls back to IP address
    """
    # Try to get user_id from JWT token
    if hasattr(request, 'user_id') and request.user_id:
        return f"user:{request.user_id}"
    
    # Fall back to IP address
    return f"ip:{get_remote_address()}"


# Initialize Flask-Limiter
limiter = Limiter(
    key_func=get_user_id_for_rate_limit,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://redis:6379/4",
    strategy="fixed-window"
)


class RateLimitManager:
    """Advanced rate limit management"""
    
    def __init__(self, redis_host='redis', redis_port=6379, redis_db=4):
        """Initialize rate limit manager"""
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
    
    def check_rate_limit(self, user_id: str, limit: int, window: int) -> bool:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: User identifier
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            True if within limit, False if exceeded
        """
        key = f"rate_limit:{user_id}:{window}"
        
        try:
            current = self.redis_client.get(key)
            
            if current is None:
                # First request in window
                self.redis_client.setex(key, window, 1)
                return True
            
            current = int(current)
            
            if current >= limit:
                return False
            
            # Increment counter
            self.redis_client.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open - allow request on error
            return True
    
    def get_usage(self, user_id: str, window: int) -> dict:
        """
        Get current usage for user
        
        Args:
            user_id: User identifier
            window: Time window in seconds
        
        Returns:
            Usage statistics
        """
        key = f"rate_limit:{user_id}:{window}"
        
        try:
            current = self.redis_client.get(key)
            ttl = self.redis_client.ttl(key)
            
            return {
                'requests': int(current) if current else 0,
                'reset_in': ttl if ttl > 0 else window
            }
        except Exception as e:
            logger.error(f"Get usage error: {e}")
            return {'requests': 0, 'reset_in': window}
    
    def reset_user_limit(self, user_id: str):
        """Reset rate limit for user"""
        pattern = f"rate_limit:{user_id}:*"
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            logger.info(f"Reset rate limit for user: {user_id}")
        except Exception as e:
            logger.error(f"Reset limit error: {e}")


# Global rate limit manager
rate_manager = RateLimitManager()


def custom_rate_limit(limit: int, per: int, scope: Optional[str] = None):
    """
    Custom rate limit decorator
    
    Args:
        limit: Number of requests allowed
        per: Time period in seconds
        scope: Optional scope for the limit
    
    Usage:
        @custom_rate_limit(limit=10, per=60)
        def my_endpoint():
            return "Limited endpoint"
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get user identifier
            user_id = get_user_id_for_rate_limit()
            
            if scope:
                user_id = f"{user_id}:{scope}"
            
            # Check rate limit
            if not rate_manager.check_rate_limit(user_id, limit, per):
                # Get usage info
                usage = rate_manager.get_usage(user_id, per)
                
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'status': 'error',
                    'limit': limit,
                    'period': per,
                    'requests': usage['requests'],
                    'reset_in': usage['reset_in']
                }), 429
            
            return f(*args, **kwargs)
        
        return wrapper
    
    return decorator


def get_rate_limit_headers(user_id: str, limit: int, window: int) -> dict:
    """
    Get rate limit headers for response
    
    Args:
        user_id: User identifier
        limit: Request limit
        window: Time window
    
    Returns:
        Headers dictionary
    """
    usage = rate_manager.get_usage(user_id, window)
    
    return {
        'X-RateLimit-Limit': str(limit),
        'X-RateLimit-Remaining': str(max(0, limit - usage['requests'])),
        'X-RateLimit-Reset': str(usage['reset_in'])
    }


# Tier-based rate limits
RATE_LIMIT_TIERS = {
    'free': {
        'requests_per_hour': 50,
        'requests_per_day': 500,
        'analysis_per_day': 10,
        'chat_per_hour': 20
    },
    'basic': {
        'requests_per_hour': 200,
        'requests_per_day': 2000,
        'analysis_per_day': 100,
        'chat_per_hour': 100
    },
    'premium': {
        'requests_per_hour': 1000,
        'requests_per_day': 10000,
        'analysis_per_day': 1000,
        'chat_per_hour': 500
    },
    'enterprise': {
        'requests_per_hour': -1,  # Unlimited
        'requests_per_day': -1,
        'analysis_per_day': -1,
        'chat_per_hour': -1
    }
}


def get_user_tier(user_id: str) -> str:
    """Get user tier (would query from database)"""
    # Mock implementation
    if user_id.startswith('user:admin'):
        return 'enterprise'
    return 'free'


def check_tier_limit(user_id: str, action: str) -> bool:
    """
    Check if user can perform action based on tier
    
    Args:
        user_id: User identifier
        action: Action type (e.g., 'analysis_per_day')
    
    Returns:
        True if allowed, False otherwise
    """
    tier = get_user_tier(user_id)
    limits = RATE_LIMIT_TIERS.get(tier, RATE_LIMIT_TIERS['free'])
    
    limit = limits.get(action, 0)
    
    # -1 means unlimited
    if limit == -1:
        return True
    
    # Extract time window from action name
    if 'per_hour' in action:
        window = 3600
    elif 'per_day' in action:
        window = 86400
    else:
        window = 3600
    
    return rate_manager.check_rate_limit(
        f"{user_id}:{action}",
        limit,
        window
    )