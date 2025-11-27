"""
JWT Authentication System
Token-based authentication with refresh tokens
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt
from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)


class JWTManager:
    """JWT token management"""
    
    @staticmethod
    def generate_tokens(user_id: str, user_data: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Generate access and refresh tokens
        
        Args:
            user_id: User identifier
            user_data: Additional user data to include in token
        
        Returns:
            Dictionary with access_token and refresh_token
        """
        secret_key = current_app.config.get('SECRET_KEY')
        
        # Access token (15 minutes)
        access_payload = {
            'user_id': user_id,
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(minutes=15),
            'iat': datetime.utcnow(),
            **(user_data or {})
        }
        
        # Refresh token (7 days)
        refresh_payload = {
            'user_id': user_id,
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow()
        }
        
        access_token = jwt.encode(access_payload, secret_key, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, secret_key, algorithm='HS256')
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 900  # 15 minutes in seconds
        }
    
    @staticmethod
    def verify_token(token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            token_type: Type of token ('access' or 'refresh')
        
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            secret_key = current_app.config.get('SECRET_KEY')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            # Verify token type
            if payload.get('type') != token_type:
                logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Generate new access token from refresh token
        
        Args:
            refresh_token: Refresh token
        
        Returns:
            New access token or None if invalid
        """
        payload = JWTManager.verify_token(refresh_token, token_type='refresh')
        
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        return JWTManager.generate_tokens(user_id)


def require_jwt_token(f):
    """
    Decorator to require JWT authentication
    
    Usage:
        @require_jwt_token
        def protected_route():
            user_id = request.user_id
            return "Protected data"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'No authorization token provided',
                'status': 'error'
            }), 401
        
        # Extract token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({
                    'error': 'Invalid authorization scheme',
                    'status': 'error'
                }), 401
        except ValueError:
            return jsonify({
                'error': 'Invalid authorization header format',
                'status': 'error'
            }), 401
        
        # Verify token
        payload = JWTManager.verify_token(token, token_type='access')
        
        if not payload:
            return jsonify({
                'error': 'Invalid or expired token',
                'status': 'error'
            }), 401
        
        # Add user info to request
        request.user_id = payload.get('user_id')
        request.user_data = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_jwt_token(f):
    """
    Decorator for optional JWT authentication
    Adds user info if token is valid, but doesn't require it
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                scheme, token = auth_header.split()
                if scheme.lower() == 'bearer':
                    payload = JWTManager.verify_token(token, token_type='access')
                    if payload:
                        request.user_id = payload.get('user_id')
                        request.user_data = payload
            except (ValueError, AttributeError):
                pass
        
        # Set default if no valid token
        if not hasattr(request, 'user_id'):
            request.user_id = None
            request.user_data = {}
        
        return f(*args, **kwargs)
    
    return decorated_function


class UserManager:
    """Simple user management (for demo - use proper DB in production)"""
    
    # In-memory user store (replace with database in production)
    users_db = {}
    
    @staticmethod
    def create_user(username: str, password: str, email: str, 
                   **kwargs) -> Dict[str, Any]:
        """Create new user"""
        user_id = f"user_{len(UserManager.users_db) + 1}"
        
        user = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.utcnow().isoformat(),
            'is_active': True,
            **kwargs
        }
        
        UserManager.users_db[user_id] = user
        UserManager.users_db[username] = user  # Also index by username
        
        return {
            'user_id': user_id,
            'username': username,
            'email': email
        }
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user"""
        user = UserManager.users_db.get(username)
        
        if not user:
            return None
        
        if not check_password_hash(user['password_hash'], password):
            return None
        
        if not user.get('is_active', True):
            return None
        
        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email']
        }
    
    @staticmethod
    def get_user(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = UserManager.users_db.get(user_id)
        
        if not user:
            return None
        
        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at']
        }


# Create default admin user for testing
UserManager.create_user(
    username='admin',
    password='admin123',
    email='admin@example.com',
    role='admin'
)

UserManager.create_user(
    username='demo',
    password='demo123',
    email='demo@example.com',
    role='user'
)