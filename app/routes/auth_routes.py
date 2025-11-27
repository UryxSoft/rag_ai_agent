"""
Authentication Routes
JWT-based authentication endpoints
"""
import logging
from flask import Blueprint, request, jsonify
from app.auth.jwt_manager import JWTManager, UserManager, require_jwt_token
from app.utils.decorators import validate_json

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
@validate_json(['username', 'password'])
def login():
    """
    User login
    
    POST /api/auth/login
    Body: {
        "username": "user",
        "password": "password"
    }
    
    Returns:
        JWT tokens
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Authenticate user
        user = UserManager.authenticate(username, password)
        
        if not user:
            return jsonify({
                'error': 'Invalid credentials',
                'status': 'error'
            }), 401
        
        # Generate tokens
        tokens = JWTManager.generate_tokens(
            user_id=user['user_id'],
            user_data={
                'username': user['username'],
                'email': user['email']
            }
        )
        
        logger.info(f"User logged in: {username}")
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            **tokens,
            'user': user
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'error': 'Login failed',
            'status': 'error'
        }), 500


@bp.route('/refresh', methods=['POST'])
@validate_json(['refresh_token'])
def refresh():
    """
    Refresh access token
    
    POST /api/auth/refresh
    Body: {
        "refresh_token": "token"
    }
    
    Returns:
        New access token
    """
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        # Refresh token
        new_tokens = JWTManager.refresh_access_token(refresh_token)
        
        if not new_tokens:
            return jsonify({
                'error': 'Invalid refresh token',
                'status': 'error'
            }), 401
        
        return jsonify({
            'status': 'success',
            **new_tokens
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({
            'error': 'Token refresh failed',
            'status': 'error'
        }), 500


@bp.route('/register', methods=['POST'])
@validate_json(['username', 'password', 'email'])
def register():
    """
    Register new user
    
    POST /api/auth/register
    Body: {
        "username": "user",
        "password": "password",
        "email": "user@example.com"
    }
    """
    try:
        data = request.get_json()
        
        # Create user
        user = UserManager.create_user(
            username=data['username'],
            password=data['password'],
            email=data['email']
        )
        
        # Generate tokens
        tokens = JWTManager.generate_tokens(user_id=user['user_id'])
        
        logger.info(f"New user registered: {user['username']}")
        
        return jsonify({
            'status': 'success',
            'message': 'Registration successful',
            'user': user,
            **tokens
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            'error': 'Registration failed',
            'status': 'error'
        }), 500


@bp.route('/me', methods=['GET'])
@require_jwt_token
def get_current_user():
    """
    Get current user info
    
    GET /api/auth/me
    Headers: Authorization: Bearer <token>
    """
    user_id = request.user_id
    user = UserManager.get_user(user_id)
    
    if not user:
        return jsonify({
            'error': 'User not found',
            'status': 'error'
        }), 404
    
    return jsonify({
        'status': 'success',
        'user': user
    }), 200


@bp.route('/logout', methods=['POST'])
@require_jwt_token
def logout():
    """
    Logout (token invalidation would be implemented with Redis)
    
    POST /api/auth/logout
    """
    # In production, add token to blacklist in Redis
    logger.info(f"User logged out: {request.user_id}")
    
    return jsonify({
        'status': 'success',
        'message': 'Logged out successfully'
    }), 200