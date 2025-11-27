"""
Authentication Middleware
API Key validation for secure endpoints
"""
import logging
from functools import wraps
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)


def require_api_key(f):
    """
    Decorator to require API key authentication
    
    Usage:
        @require_api_key
        def protected_route():
            return "Protected data"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication in testing mode
        if current_app.config.get('TESTING'):
            return f(*args, **kwargs)
        
        # Skip if API key not required
        if not current_app.config.get('REQUIRE_API_KEY', True):
            return f(*args, **kwargs)
        
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
        
        if not api_key:
            logger.warning(f"API key missing for {request.path}")
            return jsonify({
                'error': 'API key required',
                'status': 'error',
                'message': 'Please provide an API key in X-API-Key header'
            }), 401
        
        # Remove 'Bearer ' prefix if present
        if api_key.startswith('Bearer '):
            api_key = api_key[7:]
        
        # Validate API key
        expected_key = current_app.config.get('API_KEY')
        if api_key != expected_key:
            logger.warning(f"Invalid API key attempt for {request.path}")
            return jsonify({
                'error': 'Invalid API key',
                'status': 'error'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_api_key(f):
    """
    Decorator for optional API key authentication
    Validates if provided, but doesn't require it
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
        
        if api_key:
            if api_key.startswith('Bearer '):
                api_key = api_key[7:]
            
            expected_key = current_app.config.get('API_KEY')
            if api_key != expected_key:
                return jsonify({
                    'error': 'Invalid API key',
                    'status': 'error'
                }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
